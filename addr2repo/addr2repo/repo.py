import os

from .models import RepoFile
from .sources import extract_contract_names, extract_function_names, normalize_hash

SKIP_DIRS = {
    ".git",
    "node_modules",
    "out",
    "cache",
    "artifacts",
    "broadcast",
    "typechain",
    "typechain-types",
    "lib",
    "libs",
    "vendor",
    "dependencies",
    "__pycache__",
    ".venv",
    "venv",
}


def scan_repo(repo_root, extensions=(".sol", ".vy")):
    repo_root = os.path.abspath(repo_root)
    if not os.path.isdir(repo_root):
        raise SystemExit(f"repo path is not a directory: {repo_root}")
    files = []
    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            if not fn.endswith(extensions):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, repo_root).replace("\\", "/")
            try:
                with open(full, encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except OSError:
                continue
            files.append(
                RepoFile(
                    path=rel,
                    normalized_hash=normalize_hash(content),
                    contract_names=extract_contract_names(content),
                    function_names=extract_function_names(content),
                )
            )
    return files
