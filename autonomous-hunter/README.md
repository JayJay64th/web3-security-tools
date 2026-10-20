# Autonomous Hunter

An unattended, multi-pass security-hunt pipeline that runs inside an AI coding
agent. It takes a target (repo clone / contract address / bug-bounty program),
builds a source-linked model, sweeps known bug patterns, runs independent
residual and adversarial passes, and hands you back a verdict, an ordered TODO,
and evidence-packed draft findings. **Proof-of-concept work is always the
human's** — the pipeline never writes or runs a PoC, never submits, never
touches live systems.

It is not a scanner binary. It is a **skill library + state machine + helper
tools** that turn a capable LLM agent into a disciplined hunter: stage gates,
coverage contracts, hypothesis ledgers, kill/residue records, and stage-gate
git commits.

## What's inside

```
autonomous-hunter/
├── README.md                  # this file
├── AGENTS.md                  # Hunter's Laws 1-18 (shared policy - required)
├── opencode.json              # sample opencode config (providers, references)
├── install.ps1                # Windows installer
├── install.sh                 # macOS/Linux installer
├── scripts/
│   ├── check-skills.ps1       # skill integrity lint (Windows)
│   └── check-skills.sh        # skill integrity lint (macOS/Linux)
└── .opencode/skills/          # 22 skills - the whole hunter
    ├── autonomous-pipeline/   # THE PIPELINE: S0-S7 stages, refs, templates,
    │   ├── SKILL.md           #   tools (ledger/queue/coverage/commit), tests
    │   ├── stages/            #   S0 intake .. S7 retro
    │   ├── refs/              #   state schema, coverage contract, autonomy rules
    │   ├── templates/         #   architecture/coverage/threat-model scaffolds
    │   ├── tools/             #   Python 3 stdlib-only CLI tools
    │   └── tests/             #   acceptance criteria + tool tests
    ├── universal-testing/     # authority skill: laws wiring, phases 0-7,
    │                          #   protocol dispatch (EVM/DeFi, Cosmos, Solana,
    │                          #   chain-DLT, Algorand, web2, infra L1/L2)
    ├── impact-hunter/         # impact-objective directed mode (/hunt-impact)
    ├── protocol-recon/        # live deployed protocol recon (addresses first)
    ├── dlt-recon/             # repo/fork-first recon (architecture, trust boundaries)
    ├── critical-flow-selection/
    ├── audit-gap-analysis/    # what previous auditors did NOT cover
    ├── hotspot-mapping/       # coverage/hotspot/dead-lead/finding maps
    ├── hypothesis-generation/ # 7-field lead intake, kill conditions
    ├── cross-mechanism-consistency/
    ├── exploitability-analysis/
    ├── dead-lead-analysis/    # residue + offspring from killed leads
    ├── prior-audit-pattern-matching/
    ├── audit-fix-review/
    ├── contest-learning/
    ├── web3-hack-patterns/    # 3,700+ incident technique classes
    ├── lending-contest-patterns/   # 12 paid-report patterns + Immunefi cache
    ├── cosmos-contest-patterns/    # 6 Cosmos SDK contest patterns
    ├── cosmos-sdk-audit/      # full Cosmos/CometBFT fork audit playbook
    ├── consensus-bridge-known-faults/
    ├── price-truncation-theft/
    └── js-file-analyzer/      # web2 JS/bundle recon
```

Every skill folder ships its own `SKILL.md` with frontmatter `name` +
`description` — the agent dispatcher picks them up automatically. Full list:

`autonomous-pipeline` · `universal-testing` · `impact-hunter` ·
`protocol-recon` · `dlt-recon` · `critical-flow-selection` ·
`audit-gap-analysis` · `hotspot-mapping` · `hypothesis-generation` ·
`cross-mechanism-consistency` · `exploitability-analysis` ·
`dead-lead-analysis` · `prior-audit-pattern-matching` · `audit-fix-review` ·
`contest-learning` · `web3-hack-patterns` · `lending-contest-patterns` ·
`cosmos-contest-patterns` · `cosmos-sdk-audit` ·
`consensus-bridge-known-faults` · `price-truncation-theft` ·
`js-file-analyzer` (22 skills).

## Requirements (everything you need to install)

| Need | Why | Install |
|---|---|---|
| **An AI agent host** (pick one) | Skills are markdown instructions an agent demand-loads | [opencode](https://opencode.ai) (primary, `npm i -g opencode-ai` or `curl -fsSL https://opencode.ai/install.sh \| bash`), Claude Code, Cursor, or any LLM chat/agent that can read files |
| **Python 3.9+** | Pipeline tools (`render_ledger.py`, `queue.py`, `validate_coverage.py`, `commit_checkpoint.py`, `mode_state.py`, `model_diff.py`) — stdlib only, zero pip deps | `python3 --version` |
| **git** | Stage-gate checkpoints (`commit_checkpoint.py` does allowlisted commits) | system package manager |
| **A capable LLM** | The pipeline is a long-horizon agentic loop; it works best with a large-context coding model (GPT-5.x-class, Claude Sonnet/Opus-class, Kimi K2.x, GLM, etc.) via the host | your provider key |

Optional, Law-10-gated (the run asks you once, up front, never mid-run):
`solc` + [slither](https://github.com/crytic/slither) for Solidity analysis
builds; Foundry/Hardhat for target test harnesses.

No other dependencies. Tools have **zero third-party Python packages**.

## Install

### Option A — opencode (recommended)

**Project mode** (skills live with one project):

```powershell
# Windows (PowerShell), from a clone of this repo:
.\install.ps1 -Target C:\path\to\your\project
```

```bash
# macOS/Linux, from a clone of this repo:
./install.sh /path/to/your/project
```

**Global mode** (skills available in every opencode session):

```powershell
.\install.ps1 -Global
```

```bash
./install.sh --global
```

**Manual install** (no installer): copy `.opencode/skills/*` into the target's
`.opencode/skills/`, copy `AGENTS.md` into the target root, and point
`opencode.json` at it:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": ["AGENTS.md"],
  "references": {
    "hunt": { "path": "./hunt", "description": "Active hunts: per-target scope, module maps, findings ledger, PoCs, report drafts" }
  }
}
```

`AGENTS.md` is **not optional** — it carries the Hunter's Laws 1–18 (scope
gate, proof bar, kill/residue discipline, variant analysis). The autonomous
pipeline halts without it.

### Option B — Claude Code

```powershell
.\install.ps1 -Target C:\path\to\your\project -Claude
```

```bash
./install.sh /path/to/your/project --claude
```

This lays down `.claude/skills/<name>/SKILL.md` stubs (Claude Code's native
skill format) **plus** the full `.opencode/skills/` tree and `AGENTS.md`.
Then, in the project, tell Claude Code: *"Read AGENTS.md first; treat it as
standing law. Use the autonomous-pipeline skill for hunts."* Claude Code
loads `.claude/skills/*` automatically; for the deeper `refs/`/`stages/`
files, the agent reads them on demand from `.opencode/skills/`.

### Option C — Cursor (or any rules-based editor)

1. Install as in Option A (project mode) so `.opencode/skills/` + `AGENTS.md`
   sit in the project root.
2. Add to `.cursor/rules/autonomous-hunter.mdc` (or your rules file):

```md
---
description: Autonomous Hunter standing law + skill index
alwaysApply: true
---
Read AGENTS.md and obey it as standing law inside this repo.
Skill library: .opencode/skills/ — each <skill>/SKILL.md has frontmatter
name/description; load on demand, never preload everything.
Entry point for unattended hunts: .opencode/skills/autonomous-pipeline/SKILL.md
```

3. The editor agent can now read/run the same files. Invoke by asking for an
   autonomous hunt (see Usage). Run the Python tools from the integrated
   terminal.

### Option D — any raw LLM (API or chat, no agent host)

The pipeline is prompt-addressable. Minimum viable wiring:

1. Ship these two files into the model's context (or a RAG store):
   `AGENTS.md` and `.opencode/skills/autonomous-pipeline/SKILL.md`.
2. When the model reaches a stage, append the matching
   `stages/S<#>-*.md` file, then only the `refs/`, `templates/`, and
   pack skills that stage names (demand-load discipline — never dump all 22
   skills at once; it exceeds context and defeats the design).
3. The model executes tools by emitting shell commands the harness runs
   (`python3 tools/render_ledger.py hunt/targets/<name>/`, etc.).
4. Human-in-the-loop substitution for autonomy: `autonomous-pipeline/refs/autonomy-rules.md`
   lists exactly which gates become user questions when the host cannot act
   alone (Law 10 approvals, commit policy, PoC handoff).

Example system-prompt bootstrap (OpenAI-compatible API):

```python
import os, pathlib
root = pathlib.Path("autonomous-hunter")
system = (root / "AGENTS.md").read_text() + "\n\n" +
         (root / ".opencode/skills/autonomous-pipeline/SKILL.md").read_text()
# then on each turn, append the current stage file + named refs
```

Model guidance: use a large-context, tool-calling capable model. The pipeline
is deliberately verbose (raw-over-summary, ledgers, residue blocks) — cheap
small models will violate the laws.

## Connect your LLM provider (opencode)

`opencode.json` ships with a sample provider block. Replace it with **your**
provider. Any OpenAI-compatible endpoint works:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": ["AGENTS.md"],
  "provider": {
    "myprovider": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "My Provider",
      "options": { "baseURL": "https://api.example.com/v1" },
      "models": {
        "my-model-id": { "name": "My Model" }
      }
    }
  }
}
```

Then either set the key in the environment (preferred — Law 9: keys never in
files):

```powershell
# Windows
$env:MYPROVIDER_API_KEY = "sk-..."
```

```bash
export MYPROVIDER_API_KEY="sk-..."
```

or use opencode's auth (`opencode auth login`). Works with hosted providers
(OpenAI, Anthropic, OpenRouter, Groq, …), local servers (Ollama,
`ollama serve` → `baseURL: http://localhost:11434/v1`, llama.cpp, vLLM), and
routers (LiteLLM, AgentRouter, …). Official providers need no `npm` field —
see the [opencode config docs](https://opencode.ai/docs/config).

Pick the model with `/models` inside opencode, or set a default per project.

## Usage — starting an unattended hunt

1. **Scope first (Law 1).** The run halts at S0 until the program's rules are
   pasted verbatim into `hunt/targets/<name>/scope.md`. Have them ready.
2. **Handoff message** (one message, no mid-run steering needed):

   ```text
   autonomous hunt:
   target: <git URL or local path or contract addresses>
   scope: <paste program rules / link>
   analysis_build_approved: true|false   # allow solc/slither at S1 (Law 10)
   commit_policy: stage-gates            # or "manual"
   ```

   With `/hunt-impact <objective>`, the impact-hunter overlay derives the
   brief and feeds every stage's queue.
3. **Walk away.** The agent runs S0 intake → S1 recon/model → Pass 1 pattern
   sweep → S3 closeout → Pass 2 residual/cross-mechanism → Pass 3 blind
   adversarial → Pass 4 evidence + Law-17 variant sweeps → S7 retro,
   checkpointing via `commit_checkpoint.py`. It never writes/runs a PoC,
   never submits, never mutates external state. Findings needing dynamic
   proof ship as DRAFTs marked `poc: pending-human`.
4. **Come back to `OUTBOX.md`** in the target folder: verdict · candidates
   table · ordered human TODO · stop reason. The final chat message reproduces
   it verbatim. That TODO is where *you* do PoCs (human-owned, Law 10).

Resuming after a dead session: open the target folder, read
`pipeline-state.md → next_action`, and tell the agent: `resume autonomous
hunt from pipeline-state.md`.

## Verify the install

```powershell
powershell -File .\scripts\check-skills.ps1
```

```bash
./scripts/check-skills.sh
```

Expect `OK: 22 skills validated …`. Smoke-test the tools:

```bash
python3 .opencode/skills/autonomous-pipeline/tools/render_ledger.py --help
python3 .opencode/skills/autonomous-pipeline/tools/queue.py --help
python3 .opencode/skills/autonomous-pipeline/tools/validate_coverage.py --help
python3 .opencode/skills/autonomous-pipeline/tools/commit_checkpoint.py --help
```

Then in the agent: ask *"list the autonomous pipeline stages and the current
hunts"* — a working install answers from `pipeline-state.md` files.

## Safety rails (by design)

- **Authorized targets only** (Law 1): bounty programs, your own chain,
  testnets. The scope gate is a hard stop.
- **No live attacks** (Law 8): PoCs are human-owned and run on local devnet
  or tests. No validator-set attacks, no DoS volume.
- **Present before proving** (Law 10): builds, downloads, and nodes require
  up-front approval — asked once at handoff, never surprise-run.
- **No secrets in files** (Law 9): `commit_checkpoint.py` refuses commits
  matching secret patterns; keys stay in env vars.
- **Impact bar is the program's** (Law 11): dismissals must cite the
  program's verbatim paid-impact classes — no standing "DoS doesn't count".

## Updating

Re-run the installer with overwrite (`-Force` / `--force`) after pulling a
new version of this repo. Skill renames/edits: re-run `check-skills` after
any change — it enforces folder==frontmatter-name, description budget, and
that every "Composes with" reference resolves to a real skill folder.

## Customizing

- **New skill:** create `.opencode/skills/<name>/SKILL.md` with frontmatter
  `name` (== folder) + `description` (≤300 chars) and a `**Composes with:**`
  footer; run `check-skills`.
- **New pattern pack:** follow the pack shape of
  `lending-contest-patterns/` (SKILL.md + `refs/mined-patterns.md` with grep
  packs + PoC shapes); wire it into the stage table in
  `autonomous-pipeline/SKILL.md` via a change proposal
  (`refs/improvement-map.md` — measurement-backed changes only).
- **Stage/schema changes:** land only through the improvement-map proposal
  process (the pipeline's change discipline). Measuring precedes extending.

## License / use

For authorized security testing only. You are responsible for target scope
and program rules in your jurisdiction.
