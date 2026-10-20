from .keccakutil import keccak256_hex
from .models import normalize_addr
from .rpc import Rpc, RpcError

IMPL_SLOT_1967 = "0x" + format(int(keccak256_hex(b"eip1967.proxy.implementation"), 16) - 1, "064x")
BEACON_SLOT_1967 = "0x" + format(int(keccak256_hex(b"eip1967.proxy.beacon"), 16) - 1, "064x")
ADMIN_SLOT_1967 = "0x" + format(int(keccak256_hex(b"eip1967.proxy.admin"), 16) - 1, "064x")
IMPL_SLOT_1822 = "0x" + keccak256_hex(b"PROXIABLE")
IMPL_SLOT_ZOS = "0x" + keccak256_hex(b"org.zeppelinos.proxy.implementation")
ADMIN_SLOT_ZOS = "0x" + keccak256_hex(b"org.zeppelinos.proxy.admin")

IMPLEMENTATION_CALL = "0x5c60da1b"
ADMIN_CALL = "0xf851a440"
EIP1167_PREFIX = "363d3d373d3d3d363d73"
EIP1167_SUFFIX = "5af43d82803e903d91602b57fd5bf3"


def word_to_address(word: str) -> str | None:
    if not word or word in ("0x", "0x0"):
        return None
    h = word[2:] if word.startswith("0x") else word
    h = h.rjust(64, "0")
    addr = "0x" + h[-40:]
    if int(addr, 16) == 0:
        return None
    return addr.lower()


def parse_eip1167_bytecode(code: str) -> str | None:
    h = code[2:] if code.startswith("0x") else code
    h = h.lower()
    if h.startswith(EIP1167_PREFIX) and h.endswith(EIP1167_SUFFIX) and len(h) == 90:
        return "0x" + h[20:60]
    return None


def _call_implementation(rpc: Rpc, beacon: str) -> str | None:
    try:
        raw = rpc.eth_call(beacon, IMPLEMENTATION_CALL)
    except RpcError:
        return None
    return word_to_address(raw)


def detect_proxy(rpc: Rpc, address: str):
    """Return (kind, ProxyInfo-like dict) for a single address."""
    address = normalize_addr(address)
    try:
        code = rpc.get_code(address)
    except RpcError as e:
        return None, f"rpc getCode failed: {e}"
    if not code or code == "0x":
        return None, "no bytecode at address (not a contract, or wrong chain)"

    addr1167 = parse_eip1167_bytecode(code)
    if addr1167:
        return {
            "kind": "eip1167",
            "implementation": addr1167,
            "admin": None,
            "beacon": None,
        }, None

    try:
        impl_slot = word_to_address(rpc.get_storage_at(address, IMPL_SLOT_1967))
    except RpcError as e:
        return None, f"rpc getStorageAt failed: {e}"

    if impl_slot:
        try:
            admin = word_to_address(rpc.get_storage_at(address, ADMIN_SLOT_1967))
        except RpcError:
            admin = None
        return {
            "kind": "eip1967",
            "implementation": impl_slot,
            "admin": admin,
            "beacon": None,
        }, None

    try:
        impl1822 = word_to_address(rpc.get_storage_at(address, IMPL_SLOT_1822))
    except RpcError:
        impl1822 = None
    if impl1822:
        return {
            "kind": "eip1822",
            "implementation": impl1822,
            "admin": None,
            "beacon": None,
        }, None

    try:
        impl_zos = word_to_address(rpc.get_storage_at(address, IMPL_SLOT_ZOS))
    except RpcError:
        impl_zos = None
    if impl_zos:
        try:
            admin_zos = word_to_address(rpc.get_storage_at(address, ADMIN_SLOT_ZOS))
        except RpcError:
            admin_zos = None
        return {
            "kind": "zeppelinos",
            "implementation": impl_zos,
            "admin": admin_zos,
            "beacon": None,
        }, None

    try:
        beacon = word_to_address(rpc.get_storage_at(address, BEACON_SLOT_1967))
    except RpcError:
        beacon = None
    if beacon:
        impl = _call_implementation(rpc, beacon)
        return {
            "kind": "beacon",
            "implementation": impl,
            "admin": None,
            "beacon": beacon,
        }, None

    try:
        impl_call = word_to_address(rpc.eth_call(address, IMPLEMENTATION_CALL))
    except RpcError:
        impl_call = None
    if impl_call:
        return {
            "kind": "implementation-call",
            "implementation": impl_call,
            "admin": None,
            "beacon": None,
        }, None

    return {"kind": "none", "implementation": None, "admin": None, "beacon": None}, None


def resolve_chain(rpc: Rpc, address: str, max_depth=5):
    """Walk proxy chain. Returns (addresses, proxies, notes)."""
    addresses = [normalize_addr(address)]
    proxies = []
    notes = []
    seen = set(addresses)
    for _ in range(max_depth):
        current = addresses[-1]
        info, err = detect_proxy(rpc, current)
        if err:
            notes.append(f"{current}: {err}")
            break
        if info is None or info["kind"] == "none":
            break
        proxies.append(info)
        impl = info.get("implementation")
        if not impl:
            notes.append(f"{current}: proxy kind={info['kind']} but no implementation resolved")
            break
        impl = normalize_addr(impl)
        if impl in seen:
            notes.append(f"{current}: implementation loop at {impl}")
            break
        seen.add(impl)
        addresses.append(impl)
    if len(addresses) > max_depth:
        notes.append(f"stopped at max-depth {max_depth}")
    return addresses, proxies, notes
