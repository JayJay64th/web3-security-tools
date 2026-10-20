# install.ps1 - install Autonomous Hunter into a target (Windows)
# Usage:
#   .\install.ps1                          # install into current directory (project mode)
#   .\install.ps1 -Target C:\path\proj     # install into a specific project
#   .\install.ps1 -Global                  # install into user config (~/.config/opencode)
#   .\install.ps1 -Target X -Claude        # also lay down Claude Code skill stubs
param(
    [string]$Target = "",
    [switch]$Global,
    [switch]$Claude,
    [switch]$Force
)
$ErrorActionPreference = 'Stop'
$pkg = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillsSrc = Join-Path $pkg ".opencode\skills"
if (-not (Test-Path $skillsSrc)) { Write-Error "skills not found at $skillsSrc"; exit 1 }

if ($Global) {
    $destRoot = Join-Path $env:USERPROFILE ".config\opencode"
    $skillsDst = Join-Path $destRoot "skills"
    $agentsDst = Join-Path $destRoot "AGENTS.md"
} else {
    if ($Target -eq "") { $Target = (Get-Location).Path }
    $destRoot = $Target
    $skillsDst = Join-Path $destRoot ".opencode\skills"
    $agentsDst = Join-Path $destRoot "AGENTS.md"
}

New-Item -ItemType Directory -Force $skillsDst | Out-Null
$skills = Get-ChildItem -Path $skillsSrc -Directory
$copied = 0
foreach ($s in $skills) {
    $dst = Join-Path $skillsDst $s.Name
    if ((Test-Path $dst) -and -not $Force) {
        Write-Output "SKIP  $s.Name (exists; use -Force to overwrite)"
        continue
    }
    if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
    Copy-Item -Recurse -Force $s.FullName $dst
    Write-Output "COPY  $s.Name"
    $copied++
}

# AGENTS.md (Hunter's Laws - required by autonomous-pipeline)
$agentsSrc = Join-Path $pkg "AGENTS.md"
if (-not (Test-Path $agentsDst) -or $Force) {
    Copy-Item -Force $agentsSrc $agentsDst
    Write-Output "COPY  AGENTS.md -> $agentsDst"
} else {
    Write-Output "SKIP  AGENTS.md (exists; use -Force to overwrite)"
}

# opencode.json - merge is manual; only drop if absent
$ocDst = Join-Path $destRoot "opencode.json"
$ocSrc = Join-Path $pkg "opencode.json"
if (-not $Global -and -not (Test-Path $ocDst)) {
    Copy-Item -Force $ocSrc $ocDst
    Write-Output "COPY  opencode.json -> $ocDst (edit providers/models to taste)"
} elseif (-not $Global) {
    Write-Output "SKIP  opencode.json (exists; merge 'instructions' and 'references' by hand)"
}

# Claude Code stubs (optional): each SKILL.md is a Claude Code skill already.
if ($Claude) {
    $claudeSkills = Join-Path $destRoot ".claude\skills"
    New-Item -ItemType Directory -Force $claudeSkills | Out-Null
    foreach ($s in $skills) {
        $src = Join-Path $s.FullName "SKILL.md"
        if (-not (Test-Path $src)) { continue }
        $dd = Join-Path $claudeSkills $s.Name
        New-Item -ItemType Directory -Force $dd | Out-Null
        Copy-Item -Force $src (Join-Path $dd "SKILL.md")
    }
    Write-Output "COPY  Claude Code stubs -> $claudeSkills"
}

Write-Output ""
Write-Output "Installed $copied skills + AGENTS.md into $destRoot"
Write-Output "Verify:  powershell -File $pkg\scripts\check-skills.ps1"
Write-Output "Start:   open opencode in $destRoot and ask for an autonomous hunt"
