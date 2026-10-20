# addr2repo

Map **deployed contract addresses** to **source files in a local repo** — proxy-aware, batch-friendly, no AI involved.

Given a bug-bounty scope list of addresses and a cloned protocol repo, answer:

```
0xA0b8…eB48  →  proxy (eip1967)  →  impl 0xB49d…  →  FiatTokenProxy.sol / FiatTokenV2_2.sol  [IDENTICAL]
```

## What it does

| Step | How |
|------|-----|
| 1. Proxy resolution | Reads EIP-1967 / EIP-1822 / ZeppelinOS storage slots + beacon `implementation()` + `implementation()` call fallback + EIP-1167 bytecode pattern over JSON-RPC. Falls back to the explorer `Implementation` field if RPC is unavailable. Recurses nested proxies (depth-limited). |
| 2. Source fetch | Tries Sourcify (no API key) → Etherscan v2 (needs free key) → Blockscout (no key), in that order. Handles multi-file standard-JSON and single-file sources. |
| 3. Repo matching | Normalized keccak of each source file vs every `.sol`/`.vy` in the repo (comments/whitespace stripped). Falls back to ABI function-name overlap against the closest same-name file. |
| 4. Report | One row per address; proxies grouped under their implementation. Formats: `text`, `md`, `csv`, `json`. |

**Match confidence levels:** `IDENTICAL` (normalized hash equal) → `SELECTOR_MATCH` (≥50% function-name overlap) → `NAME_CANDIDATE` (name only) → `NONE` / `UNVERIFIED`.

**Out of scope (v1):** source-vs-repo diffing, decompilation, non-EVM chains.

## Install

```bash
cd tools/addr2repo
pip install -e .
```

Requires Python ≥3.10. Deps: `pycryptodome`, `requests`.

## Usage

### Single address

```bash
addr2repo --repo ./protocol --address 0xProxy123… --chain ethereum
```

### Batch (the normal case)

```bash
addr2repo --repo ./protocol --batch scope.txt --chain base --format csv > map.csv
```

`scope.txt`: one address per line. `#` comments and CSV first-column are accepted.

### Common flags

| Flag | Meaning |
|------|---------|
| `--chain ethereum` | Chain name or numeric id (`ethereum base arbitrum optimism polygon bsc gnosis avalanche linea scroll blast`, or e.g. `1`, `8453`). |
| `--rpc-url URL` | Custom JSON-RPC (default: a public RPC for the chain). |
| `--no-rpc` | Skip on-chain proxy detection (explorer hints only). |
| `--etherscan-key KEY` | Or set `ETHERSCAN_API_KEY`. Sourcify/Blockscout work without any key. |
| `--explorers sourcify,blockscout` | Reorder / restrict explorer chain. |
| `--format text\|md\|csv\|json` | Output format. |
| `--max-depth 5` | Max nested-proxy walk. |
| `--no-cache` | Disable the `~/.cache/addr2repo` fetch cache. |

### Example output (text)

```
========================================================================
implementation group: 0xbb4c…7b09
  contract: PancakeProxy (via sourcify, compiler v0.6.6+commit.6c089d02)
  source files: 2
  repo match: contracts/token/WBNB.sol  [IDENTICAL]
  proxy for:
    0xbb4c…7b09  (eip1967, impl=0x10ed…32d5)
  identical files: 2/2
```

## How proxies are handled

1. `eth_getCode` — empty ⇒ not a contract.
2. EIP-1167 minimal-proxy bytecode pattern ⇒ clone target.
3. EIP-1967 implementation slot `keccak("eip1967.proxy.implementation")-1`.
4. EIP-1822 `keccak("PROXIABLE")` slot.
5. ZeppelinOS slot `keccak("org.zeppelinos.proxy.implementation")` (e.g. USDC FiatTokenProxy).
6. EIP-1967 beacon slot → `beacon.implementation()`.
7. `implementation()` eth_call fallback (old proxies that expose the method).
8. Else treat the address as a direct implementation.

Nested chains recurse (`proxy → impl → proxy → impl`) up to `--max-depth`. Batch mode groups every proxy under its final implementation so 50 scope addresses often collapse to a handful of unique code files.

## Tests

```bash
python -m unittest discover -s tests -v
```

No network required — fixtures only.

## Notes

- Unverified contracts report `UNVERIFIED` (bytecode only). That is intentional partial coverage, not a failure.
- Deployed tag ≠ repo HEAD is surfaced as `SELECTOR_MATCH` / `NAME_CANDIDATE` with overlap %, not as a diff (v1 scope).
- Cache lives in `~/.cache/addr2repo` (24h TTL). Delete the directory to force refetch.
