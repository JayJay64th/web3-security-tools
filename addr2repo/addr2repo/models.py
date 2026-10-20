from dataclasses import dataclass, field, asdict
from typing import Optional


def normalize_addr(addr: str) -> str:
    a = addr.strip().lower()
    if not a.startswith("0x") or len(a) != 42:
        raise ValueError(f"invalid address: {addr!r}")
    int(a, 16)
    return "0x" + a[2:]


@dataclass
class DeployedSource:
    path: str
    content: str


@dataclass
class FetchedContract:
    address: str
    name: str
    compiler: str
    explorer: str
    sources: list
    abi: Optional[list] = None
    proxy_hint_implementation: Optional[str] = None
    partial: bool = False

    @property
    def verified(self) -> bool:
        return bool(self.sources)


@dataclass
class ProxyInfo:
    kind: str
    implementation: Optional[str] = None
    admin: Optional[str] = None
    beacon: Optional[str] = None


@dataclass
class RepoFile:
    path: str
    normalized_hash: str
    contract_names: set
    function_names: set


@dataclass
class FileMatch:
    deployed_path: str
    repo_path: Optional[str]
    method: str
    confidence: str
    overlap: Optional[float] = None


@dataclass
class AddressResult:
    address: str
    chain: str
    chain_name: str
    resolution: list = field(default_factory=list)
    proxy: Optional[ProxyInfo] = None
    target_address: Optional[str] = None
    fetch: Optional[FetchedContract] = None
    matches: list = field(default_factory=list)
    primary_repo_path: Optional[str] = None
    primary_confidence: str = "NONE"
    notes: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def to_dict(self):
        def clean(o):
            if isinstance(o, FetchedContract):
                return {
                    "address": o.address,
                    "name": o.name,
                    "compiler": o.compiler,
                    "explorer": o.explorer,
                    "partial": o.partial,
                    "source_files": len(o.sources),
                    "has_abi": o.abi is not None,
                }
            if isinstance(o, ProxyInfo):
                return asdict(o)
            if isinstance(o, FileMatch):
                return asdict(o)
            if isinstance(o, list):
                return [clean(x) for x in o]
            if isinstance(o, dict):
                return {k: clean(v) for k, v in o.items()}
            return o

        d = {
            "address": self.address,
            "chain": self.chain,
            "chain_name": self.chain_name,
            "resolution": self.resolution,
            "proxy": clean(self.proxy) if self.proxy else None,
            "target_address": self.target_address,
            "fetch": clean(self.fetch) if self.fetch else None,
            "matches": clean(self.matches),
            "primary_repo_path": self.primary_repo_path,
            "primary_confidence": self.primary_confidence,
            "notes": self.notes,
            "errors": self.errors,
        }
        return clean(d)
