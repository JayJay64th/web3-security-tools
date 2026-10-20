# check-skills.ps1 - skill integrity lint (run after ANY skill rename/create/edit)
# Validates: (1) folder == frontmatter name, (2) description present + <=300 chars,
# (3) every "Composes with" name exists as a folder, (4) zero retired-name hits
# outside hunt/targets/** history. Scans project + global skill dirs. ASCII only.
param()
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$skillDirs = @((Join-Path $root '.opencode\skills'))
$globalSkills = Join-Path $env:USERPROFILE '.config\opencode\skills'
if (Test-Path $globalSkills) { $skillDirs += $globalSkills }
$retired = @('lead-intake-rules', 'hotspot-mapper', 'dead-lead-residue', 'realistic-attacker-constraint')
$fail = @()
$allFolders = @()
$skills = @()
foreach ($d in $skillDirs) {
    $dirs = Get-ChildItem -Path $d -Directory
    $skills += $dirs
    $allFolders += $dirs.Name
}
$allFolders = $allFolders | Select-Object -Unique

foreach ($s in $skills) {
    $skillFile = Join-Path $s.FullName 'SKILL.md'
    if (-not (Test-Path $skillFile)) { $fail += "MISSING SKILL.md in $($s.Name)"; continue }
    $raw = Get-Content -Raw -LiteralPath $skillFile
    if ($raw -notmatch '(?ms)^---\s*\r?\n(.*?)\r?\n---') { $fail += "$($s.Name): no frontmatter"; continue }
    $fm = $Matches[1]
    $name = if ($fm -match '(?m)^name:\s*(.+)$') { $Matches[1].Trim() } else { '' }
    $desc = if ($fm -match '(?m)^description:\s*(.+)$') { $Matches[1].Trim() } else { '' }
    if ($name -ne $s.Name) { $fail += "$($s.Name): frontmatter name '$name' != folder" }
    if (-not $desc) { $fail += "$($s.Name): missing description (skill is invisible without one)" }
    elseif ($desc.Length -gt 300) { $fail += "$($s.Name): description $($desc.Length) chars > 300 budget" }
    if ($raw -match '(?m)^\*\*Composes with:\*\*\s*(.+)$') {
        foreach ($tok in ($Matches[1] -split ',')) {
            $n = ($tok.Trim() -replace '\s*\(.*?\)', '').Trim()
            if ($n -and ($allFolders -notcontains $n)) { $fail += "$($s.Name): Composes-with '$n' has no folder" }
        }
    } else {
        $fail += "$($s.Name): missing Composes with footer"
    }
}

# Retired names: search live config surfaces only (AGENTS.md, skills, hunt root files)
$targets = @((Join-Path $root 'AGENTS.md'))
foreach ($d in $skillDirs) { $targets += (Get-ChildItem -Path $d -Recurse -Filter '*.md').FullName }
$huntDir = Join-Path $root 'hunt'
if (Test-Path $huntDir) { $targets += (Get-ChildItem -Path $huntDir -Filter '*.md' -File).FullName }
foreach ($f in $targets) {
    $hits = Select-String -LiteralPath $f -Pattern ($retired -join '|') -SimpleMatch:$false | Where-Object { $_.Line -notmatch '^\*\*Renamed from:\*\*' }
    foreach ($h in $hits) { $line = $h.Line.Trim(); $fail += "RETIRED NAME in ${f}:$($h.LineNumber) -> $($line.Substring(0, [Math]::Min(80, $line.Length)))" }
}

if ($fail.Count -eq 0) {
    Write-Output "OK: $($skills.Count) skills validated - folder==name, descriptions in budget, Composes-with resolve, no retired names."
    exit 0
} else {
    Write-Output "FAIL ($($fail.Count) issues):"
    $fail | ForEach-Object { Write-Output "  - $_" }
    exit 1
}
