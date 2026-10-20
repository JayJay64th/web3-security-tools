import json

import requests

from .models import DeployedSource, FetchedContract, normalize_addr
from .sources import parse_abi, parse_standard_json


class ExplorerError(RuntimeError):
    pass


def _get_json(url, params=None, timeout=30):
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def fetch_sourcify(chain_id, address, timeout=30):
    url = f"https://sourcify.dev/server/files/any/{chain_id}/{address}"
    try:
        data = _get_json(url, timeout=timeout)
    except requests.RequestException:
        return None
    if not data or data.get("error"):
        return None
    files = data.get("files") or []
    sources = []
    abi = None
    name = ""
    compiler = ""
    for f in files:
        path = f.get("name") or f.get("path") or ""
        content = f.get("content") or ""
        if path.endswith("metadata.json"):
            try:
                meta = json.loads(content)
            except Exception:
                meta = None
            if meta:
                name = meta.get("output", {}).get("devdoc", {}).get("title") or name
                comp = meta.get("compiler", {})
                version = comp.get("version") or ""
                compiler = version
                abi = meta.get("output", {}).get("abi") or abi
                if not name:
                    settings_contracts = meta.get("settings", {}).get("compilationTarget") or {}
                    if settings_contracts:
                        name = list(settings_contracts.keys())[0].split(":")[-1]
            continue
        if path.endswith(".sol") or path.endswith(".vy") or path.endswith(".yul"):
            clean = path.split("sources/")[-1] if "sources/" in path else path
            sources.append(DeployedSource(path=clean, content=content))
    if not sources:
        return None
    if not name:
        for s in sources:
            base = s.path.split("/")[-1].rsplit(".", 1)[0]
            if base:
                name = base
                break
    return FetchedContract(
        address=address,
        name=name,
        compiler=compiler or "unknown",
        explorer="sourcify",
        sources=sources,
        abi=abi if isinstance(abi, list) else None,
    )


def _parse_etherscan_like(payload, address, explorer_label):
    status = str(payload.get("status", ""))
    result = payload.get("result")
    if status != "1" or not isinstance(result, list) or not result:
        return None
    entry = result[0]
    if entry.get("SourceCode") in (None, "", "Contract source code not verified"):
        impl = entry.get("Implementation") or None
        if impl:
            impl = impl.strip() or None
        proxy = str(entry.get("Proxy", "0")) == "1"
        return FetchedContract(
            address=address,
            name=entry.get("ContractName") or "",
            compiler=entry.get("CompilerVersion") or "",
            explorer=explorer_label,
            sources=[],
            abi=None,
            proxy_hint_implementation=impl.lower() if impl else None,
        ) if (proxy or impl) else None
    sources = []
    parsed = parse_standard_json(entry.get("SourceCode") or "")
    if parsed:
        for path, content in parsed.items():
            sources.append(DeployedSource(path=path, content=content))
    else:
        sources.append(DeployedSource(path=f"{entry.get('ContractName') or 'Contract'}.sol", content=entry.get("SourceCode") or ""))
    impl = entry.get("Implementation") or None
    if impl:
        impl = impl.strip().lower() or None
    return FetchedContract(
        address=address,
        name=entry.get("ContractName") or "",
        compiler=entry.get("CompilerVersion") or "",
        explorer=explorer_label,
        sources=sources,
        abi=parse_abi(entry.get("ABI")),
        proxy_hint_implementation=impl,
        partial=False,
    )


def fetch_etherscan(chain_id, address, api_key, timeout=30):
    if not api_key:
        return None
    url = "https://api.etherscan.io/v2/api"
    params = {
        "chainid": chain_id,
        "module": "contract",
        "action": "getsourcecode",
        "address": address,
        "apikey": api_key,
    }
    try:
        data = _get_json(url, params=params, timeout=timeout)
    except requests.RequestException:
        return None
    return _parse_etherscan_like(data, address, "etherscan")


def fetch_blockscout(blockscout_base, address, timeout=30):
    if not blockscout_base:
        return None
    url = blockscout_base.rstrip("/") + "/api"
    params = {"module": "contract", "action": "getsourcecode", "address": address}
    try:
        data = _get_json(url, params=params, timeout=timeout)
    except requests.RequestException:
        return None
    return _parse_etherscan_like(data, address, "blockscout")


def fetch_contract(chain_cfg, address, etherscan_key=None, explorers=("sourcify", "etherscan", "blockscout")):
    address = normalize_addr(address)
    chain_id = chain_cfg["chain_id"]
    for name in explorers:
        result = None
        if name == "sourcify":
            result = fetch_sourcify(chain_id, address)
        elif name == "etherscan":
            result = fetch_etherscan(chain_id, address, etherscan_key)
        elif name == "blockscout":
            result = fetch_blockscout(chain_cfg.get("blockscout"), address)
        if result and result.verified:
            return result
        if result and result.proxy_hint_implementation:
            return result
    return None
