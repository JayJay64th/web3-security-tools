import json
import re


def normalize_source(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"//[^\n]*", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_hash(text: str) -> str:
    from .keccakutil import keccak256_hex

    return keccak256_hex(normalize_source(text).encode("utf-8"))


def parse_standard_json(source_code: str):
    """Explorer SourceCode -> {path: content}. Handles single-file and double-wrapped standard-json."""
    raw = source_code.strip()
    if raw.startswith("{{") and raw.endswith("}}"):
        raw = raw[1:-1]
    if raw.startswith("{"):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None
        sources = data.get("sources")
        if isinstance(sources, dict):
            out = {}
            for path, entry in sources.items():
                if isinstance(entry, dict) and "content" in entry:
                    out[path] = entry["content"]
                elif isinstance(entry, str):
                    out[path] = entry
            return out or None
        return None
    return None


def parse_abi(abi_raw):
    if not abi_raw:
        return None
    if isinstance(abi_raw, list):
        return abi_raw
    if isinstance(abi_raw, str):
        s = abi_raw.strip()
        if not s or s in ("[]", "Contract source code not verified"):
            return None
        try:
            data = json.loads(s)
        except json.JSONDecodeError:
            return None
        return data if isinstance(data, list) else None
    return None


def abi_function_names(abi):
    if not abi:
        return set()
    names = set()
    for item in abi:
        if isinstance(item, dict) and item.get("type") == "function":
            name = item.get("name")
            if name:
                names.add(name)
    return names


def extract_contract_names(source: str):
    text = normalize_source(source)
    names = set()
    for kind in ("contract", "interface", "library"):
        for m in re.finditer(rf"\b{kind}\s+([A-Za-z_][A-Za-z0-9_]*)", text):
            names.add(m.group(1))
    return names


def extract_function_names(source: str):
    text = normalize_source(source)
    names = set()
    for m in re.finditer(r"\bfunction\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", text):
        names.add(m.group(1))
    for kw in ("constructor", "receive", "fallback"):
        if re.search(rf"\b{kw}\s*\(", text):
            names.add(kw)
    return names
