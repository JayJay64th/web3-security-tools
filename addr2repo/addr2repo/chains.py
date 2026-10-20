CHAINS = {
    "ethereum": {
        "chain_id": 1,
        "blockscout": "https://eth.blockscout.com",
        "rpc": "https://ethereum-rpc.publicnode.com",
        "etherscan": "https://api.etherscan.io/v2/api",
    },
    "base": {
        "chain_id": 8453,
        "blockscout": "https://base.blockscout.com",
        "rpc": "https://base-rpc.publicnode.com",
        "etherscan": "https://api.etherscan.io/v2/api",
    },
    "arbitrum": {
        "chain_id": 42161,
        "blockscout": "https://arbitrum.blockscout.com",
        "rpc": "https://arbitrum-one-rpc.publicnode.com",
        "etherscan": "https://api.etherscan.io/v2/api",
    },
    "optimism": {
        "chain_id": 10,
        "blockscout": "https://optimism.blockscout.com",
        "rpc": "https://optimism-rpc.publicnode.com",
        "etherscan": "https://api.etherscan.io/v2/api",
    },
    "polygon": {
        "chain_id": 137,
        "blockscout": "https://polygon.blockscout.com",
        "rpc": "https://polygon-rpc.com",
        "etherscan": "https://api.etherscan.io/v2/api",
    },
    "bsc": {
        "chain_id": 56,
        "blockscout": "https://bnb.blockscout.com",
        "rpc": "https://bsc-rpc.publicnode.com",
        "etherscan": "https://api.etherscan.io/v2/api",
    },
    "gnosis": {
        "chain_id": 100,
        "blockscout": "https://gnosis.blockscout.com",
        "rpc": "https://gnosis-rpc.publicnode.com",
        "etherscan": "https://api.etherscan.io/v2/api",
    },
    "avalanche": {
        "chain_id": 43114,
        "blockscout": "https://avalanche.blockscout.com",
        "rpc": "https://avalanche-c-chain-rpc.publicnode.com",
        "etherscan": "https://api.etherscan.io/v2/api",
    },
    "linea": {
        "chain_id": 59144,
        "blockscout": "https://linea.blockscout.com",
        "rpc": "https://linea-rpc.publicnode.com",
        "etherscan": "https://api.etherscan.io/v2/api",
    },
    "scroll": {
        "chain_id": 534352,
        "blockscout": "https://scroll.blockscout.com",
        "rpc": "https://scroll-rpc.publicnode.com",
        "etherscan": "https://api.etherscan.io/v2/api",
    },
    "blast": {
        "chain_id": 81457,
        "blockscout": "https://blast.blockscout.com",
        "rpc": "https://blast-rpc.publicnode.com",
        "etherscan": "https://api.etherscan.io/v2/api",
    },
}


def resolve_chain(name_or_id):
    if name_or_id is None:
        return CHAINS["ethereum"], "ethereum"
    key = str(name_or_id).lower().strip()
    if key.isdigit():
        for name, cfg in CHAINS.items():
            if cfg["chain_id"] == int(key):
                return cfg, name
        return {
            "chain_id": int(key),
            "blockscout": None,
            "rpc": None,
            "etherscan": "https://api.etherscan.io/v2/api",
        }, key
    if key not in CHAINS:
        known = ", ".join(sorted(CHAINS))
        raise SystemExit(f"unknown chain '{name_or_id}' (known: {known}, or a numeric chain id)")
    return CHAINS[key], key
