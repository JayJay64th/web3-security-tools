from .models import FileMatch
from .sources import abi_function_names, extract_function_names, normalize_hash


def _primary_deployed_source(fetch):
    wanted = fetch.name
    candidates = [s for s in fetch.sources if wanted and wanted in s.path.split("/")[-1]]
    if candidates:
        scored = sorted(candidates, key=lambda s: (s.path.count("/"), len(s.content)))
        return scored[0]
    if fetch.sources:
        scored = sorted(fetch.sources, key=lambda s: (s.path.count("/"), len(s.content)))
        return scored[0]
    return None


def match_contract(fetch, repo_files):
    if not fetch or not fetch.sources:
        return [], "NONE", None

    hash_index = {}
    for rf in repo_files:
        hash_index.setdefault(rf.normalized_hash, []).append(rf)

    per_file = []
    for src in fetch.sources:
        h = normalize_hash(src.content)
        hits = hash_index.get(h)
        if hits:
            best = sorted(hits, key=lambda r: abs(len(r.path) - len(src.path)))[0]
            per_file.append(FileMatch(src.path, best.path, "hash", "IDENTICAL", 1.0))
        else:
            per_file.append(FileMatch(src.path, None, "none", "NONE", None))

    primary = _primary_deployed_source(fetch)
    if primary is None:
        return per_file, "NONE", None

    primary_match = next((m for m in per_file if m.deployed_path == primary.path), None)
    if primary_match and primary_match.confidence == "IDENTICAL":
        return per_file, "IDENTICAL", primary_match.repo_path

    deployed_fns = abi_function_names(fetch.abi) or extract_function_names(primary.content)
    name = fetch.name
    basename = primary.path.split("/")[-1].rsplit(".", 1)[0]

    candidates = []
    for rf in repo_files:
        name_hit = (name and name in rf.contract_names) or (basename and basename in rf.contract_names) or (
            basename and rf.path.split("/")[-1].rsplit(".", 1)[0] == basename
        )
        if not name_hit:
            continue
        if not deployed_fns:
            candidates.append((rf, None))
            continue
        overlap = len(deployed_fns & rf.function_names) / len(deployed_fns)
        candidates.append((rf, overlap))

    if not candidates:
        if primary_match:
            primary_match.confidence = "NONE"
        return per_file, "NONE", None

    def sort_key(item):
        rf, overlap = item
        basename_bonus = 1.0 if basename and rf.path.split("/")[-1].rsplit(".", 1)[0] == basename else 0.0
        return (overlap if overlap is not None else -1.0, basename_bonus, -rf.path.count("/"))

    best_rf, best_overlap = sorted(candidates, key=sort_key, reverse=True)[0]
    if best_overlap is not None and best_overlap >= 0.5:
        confidence, method = "SELECTOR_MATCH", "selector"
    elif best_overlap is not None and best_overlap > 0:
        confidence, method = "SELECTOR_MATCH", "selector-partial"
    else:
        confidence, method = "NAME_CANDIDATE", "name"

    if primary_match and primary_match.confidence == "NONE":
        primary_match.repo_path = best_rf.path
        primary_match.confidence = confidence
        primary_match.method = method
        primary_match.overlap = best_overlap
    return per_file, confidence, best_rf.path
