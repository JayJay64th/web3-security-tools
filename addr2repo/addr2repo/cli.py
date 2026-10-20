import argparse
import os
import sys

from .cache import Cache
from .chains import resolve_chain
from .explorers import fetch_contract
from .matcher import match_contract
from .models import AddressResult, ProxyInfo, normalize_addr
from .proxy import resolve_chain as resolve_proxy_chain
from .repo import scan_repo
from .report import group_by_implementation, render
from .rpc import Rpc, RpcError


def _load_addresses(args):
    addresses = []
    if args.address:
        addresses.extend(args.address)
    if args.batch:
        with open(args.batch, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "," in line:
                    line = line.split(",")[0].strip()
                addresses.append(line)
    seen = set()
    out = []
    for a in addresses:
        n = normalize_addr(a)
        if n not in seen:
            seen.add(n)
            out.append(n)
    if not out:
        raise SystemExit("no addresses given (use --address and/or --batch)")
    return out


def process_address(address, chain_cfg, chain_name, repo_files, rpc, cache, args):
    result = AddressResult(address=address, chain=chain_cfg["chain_id"], chain_name=chain_name)
    resolution = [address]
    proxy_obj = None
    notes = []

    if rpc is not None:
        try:
            addresses, proxies, proxy_notes = resolve_proxy_chain(rpc, address, max_depth=args.max_depth)
            resolution = addresses
            notes.extend(proxy_notes)
            if proxies:
                last = proxies[-1]
                proxy_obj = ProxyInfo(
                    kind="+".join(p["kind"] for p in proxies),
                    implementation=addresses[-1] if len(addresses) > 1 else None,
                    admin=proxies[-1].get("admin"),
                    beacon=proxies[-1].get("beacon"),
                )
        except RpcError as e:
            notes.append(f"proxy resolve failed: {e}")

    target = resolution[-1]
    result.resolution = resolution
    result.proxy = proxy_obj
    result.target_address = target
    result.notes.extend(notes)

    fetch = None
    for hop in reversed(resolution):
        key = f"fetch:{chain_name}:{chain_cfg['chain_id']}:{hop}:{','.join(args.explorers)}"
        cached = cache.get(key)
        if cached is not None:
            from .models import DeployedSource, FetchedContract

            fetch = FetchedContract(
                address=cached["address"],
                name=cached["name"],
                compiler=cached["compiler"],
                explorer=cached["explorer"],
                sources=[DeployedSource(s["path"], s["content"]) for s in cached["sources"]],
                abi=cached.get("abi"),
                proxy_hint_implementation=cached.get("proxy_hint_implementation"),
                partial=cached.get("partial", False),
            )
            fetch.address = hop
            break
        fetch = fetch_contract(
            chain_cfg, hop, etherscan_key=args.etherscan_key, explorers=tuple(args.explorers)
        )
        if fetch is not None:
            cache.set(
                key,
                {
                    "address": fetch.address,
                    "name": fetch.name,
                    "compiler": fetch.compiler,
                    "explorer": fetch.explorer,
                    "sources": [{"path": s.path, "content": s.content} for s in fetch.sources],
                    "abi": fetch.abi,
                    "proxy_hint_implementation": fetch.proxy_hint_implementation,
                    "partial": fetch.partial,
                },
            )
            if fetch.verified:
                break
        if proxy_obj is None and fetch is None:
            break

    if fetch is None and proxy_obj is None:
        for hop in reversed(resolution):
            fetch = fetch_contract(
                chain_cfg, hop, etherscan_key=args.etherscan_key, explorers=tuple(args.explorers)
            )
            if fetch:
                break

    if fetch is not None and not fetch.verified and fetch.proxy_hint_implementation:
        impl = normalize_addr(fetch.proxy_hint_implementation)
        if impl not in resolution:
            resolution.append(impl)
            result.resolution = resolution
            result.target_address = impl
            if proxy_obj is None:
                proxy_obj = ProxyInfo(kind="explorer-hint", implementation=impl)
                result.proxy = proxy_obj
            impl_fetch = fetch_contract(
                chain_cfg, impl, etherscan_key=args.etherscan_key, explorers=tuple(args.explorers)
            )
            if impl_fetch and impl_fetch.verified:
                fetch = impl_fetch

    result.fetch = fetch
    if fetch is None:
        result.errors.append("no verified source found on sourcify/etherscan/blockscout")
        result.primary_confidence = "UNVERIFIED"
        return result
    if not fetch.verified:
        result.errors.append("source not verified (bytecode only)")
        result.primary_confidence = "UNVERIFIED"
        return result

    matches, confidence, repo_path = match_contract(fetch, repo_files)
    result.matches = matches
    result.primary_confidence = confidence
    result.primary_repo_path = repo_path
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="addr2repo",
        description="Map deployed contract addresses to source files in a local repo (proxy-aware).",
    )
    parser.add_argument("--repo", required=True, help="path to the local source repo")
    parser.add_argument("--address", action="append", help="contract address (repeatable)")
    parser.add_argument("--batch", help="file with one address per line (# comments ok, CSV first column ok)")
    parser.add_argument("--chain", default="ethereum", help="chain name or numeric id (default: ethereum)")
    parser.add_argument("--rpc-url", help="JSON-RPC URL for proxy slot reads (default: public RPC for chain)")
    parser.add_argument("--no-rpc", action="store_true", help="skip on-chain proxy detection")
    parser.add_argument("--etherscan-key", default=os.environ.get("ETHERSCAN_API_KEY"), help="Etherscan API key (or ETHERSCAN_API_KEY env)")
    parser.add_argument(
        "--explorers",
        default="sourcify,etherscan,blockscout",
        help="comma list, tried in order (default: sourcify,etherscan,blockscout)",
    )
    parser.add_argument("--format", choices=("text", "md", "csv", "json"), default="text")
    parser.add_argument("--cache-dir", default=os.path.join(os.path.expanduser("~"), ".cache", "addr2repo"))
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--max-depth", type=int, default=5, help="max proxy nesting depth (default: 5)")
    args = parser.parse_args(argv)

    args.explorers = [e.strip() for e in args.explorers.split(",") if e.strip()]
    chain_cfg, chain_name = resolve_chain(args.chain)
    addresses = _load_addresses(args)

    print(f"scanning repo: {args.repo} ...", file=sys.stderr)
    repo_files = scan_repo(args.repo)
    print(f"  {len(repo_files)} source files indexed", file=sys.stderr)

    cache = Cache(args.cache_dir, enabled=not args.no_cache)
    rpc = None
    if not args.no_rpc:
        rpc_url = args.rpc_url or chain_cfg.get("rpc")
        if rpc_url:
            rpc = Rpc(rpc_url)
        else:
            print("  warning: no RPC available; proxy detection limited to explorer hints", file=sys.stderr)

    results = []
    for i, address in enumerate(addresses, 1):
        print(f"[{i}/{len(addresses)}] {address}", file=sys.stderr)
        try:
            results.append(process_address(address, chain_cfg, chain_name, repo_files, rpc, cache, args))
        except Exception as e:
            r = AddressResult(address=address, chain=chain_cfg["chain_id"], chain_name=chain_name)
            r.errors.append(str(e))
            results.append(r)

    groups = group_by_implementation(results)
    print(render(args.format, results, groups))
    matched = sum(1 for r in results if r.primary_repo_path)
    print(f"\n{matched}/{len(results)} addresses mapped to a repo file", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
