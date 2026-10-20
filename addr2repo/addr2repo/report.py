import csv
import io
import json


def _proxy_line(result):
    if not result.proxy:
        return "direct (not a proxy, or rpc unavailable)"
    p = result.proxy
    bits = [p.kind]
    if p.implementation:
        bits.append(f"impl={p.implementation}")
    if p.beacon:
        bits.append(f"beacon={p.beacon}")
    if p.admin:
        bits.append(f"admin={p.admin}")
    return ", ".join(bits)


def render_text(results, groups):
    lines = []
    for impl_addr, members in groups:
        lines.append("=" * 72)
        lines.append(f"implementation group: {impl_addr}")
        first = members[0]
        if first.fetch:
            lines.append(f"  contract: {first.fetch.name or '?'} (via {first.fetch.explorer}, compiler {first.fetch.compiler})")
            lines.append(f"  source files: {len(first.fetch.sources)}{'  [partial]' if first.fetch.partial else ''}")
        else:
            lines.append("  source: NOT VERIFIED on any explorer")
        lines.append(f"  repo match: {first.primary_repo_path or 'NONE'}  [{first.primary_confidence}]")
        lines.append(f"  proxy for:")
        for m in members:
            lines.append(f"    {m.address}  ({_proxy_line(m)})")
        for note in first.notes:
            lines.append(f"  note: {note}")
        for err in first.errors:
            lines.append(f"  error: {err}")
        identical = [m for m in first.matches if m.confidence == "IDENTICAL"]
        if identical and first.primary_confidence != "IDENTICAL":
            lines.append(f"  identical files: {', '.join(m.repo_path for m in identical[:8])}")
        elif identical:
            lines.append(f"  identical files: {len(identical)}/{len(first.matches)}")
        lines.append("")
    return "\n".join(lines)


def render_markdown(results, groups):
    lines = [
        "| address | proxy | implementation | contract | repo file | confidence |",
        "|---|---|---|---|---|---|",
    ]
    for impl_addr, members in groups:
        first = members[0]
        name = first.fetch.name if first.fetch else "?"
        repo = first.primary_repo_path or "—"
        conf = first.primary_confidence
        proxy_kind = first.proxy.kind if first.proxy else "?"
        for m in members:
            lines.append(
                f"| `{m.address}` | {proxy_kind} | `{impl_addr}` | {name} | {repo} | {conf} |"
            )
    return "\n".join(lines)


def render_csv(results, groups):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(
        [
            "address",
            "chain",
            "proxy_kind",
            "implementation",
            "contract_name",
            "explorer",
            "compiler",
            "source_files",
            "repo_path",
            "confidence",
            "notes",
        ]
    )
    for impl_addr, members in groups:
        first = members[0]
        for m in members:
            w.writerow(
                [
                    m.address,
                    m.chain_name,
                    m.proxy.kind if m.proxy else "",
                    impl_addr,
                    first.fetch.name if first.fetch else "",
                    first.fetch.explorer if first.fetch else "",
                    first.fetch.compiler if first.fetch else "",
                    len(first.fetch.sources) if first.fetch else 0,
                    first.primary_repo_path or "",
                    first.primary_confidence,
                    "; ".join(m.notes + m.errors),
                ]
            )
    return buf.getvalue()


def render_json(results, groups):
    payload = []
    for impl_addr, members in groups:
        first = members[0]
        payload.append(
            {
                "implementation": impl_addr,
                "contract": first.to_dict(),
                "proxied_by": [m.to_dict() for m in members],
            }
        )
    return json.dumps(payload, indent=2)


def render(fmt, results, groups):
    if fmt == "text":
        return render_text(results, groups)
    if fmt == "md":
        return render_markdown(results, groups)
    if fmt == "csv":
        return render_csv(results, groups)
    if fmt == "json":
        return render_json(results, groups)
    raise ValueError(f"unknown format: {fmt}")


def group_by_implementation(results):
    groups = {}
    order = []
    for r in results:
        key = (r.target_address or r.address).lower()
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(r)
    return [(k, groups[k]) for k in order]
