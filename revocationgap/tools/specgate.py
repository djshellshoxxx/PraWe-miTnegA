#!/usr/bin/env python3
"""Specification quality gate and generator for the RevocationGap specification package.

Commands
  check   validate registry + specs (exit 1 on errors). `--final` additionally enforces full coverage.
  render  regenerate generated tables: docs/01-MASTER-ROADMAP.md (between markers), docs/PROGRESS.md (markers),
          docs/REQUIREMENTS-TRACEABILITY.md (fully generated).
  order   print dependency-ordered list of unfinished elements.

Conventions (see docs/06-MODULES/_TEMPLATE.md):
  * Module specs: docs/06-MODULES/<ID>-<slug>.md with YAML front matter and 27 numbered sections `## N. ...`.
  * Requirement IDs are defined once, as headings `### FR-AREA-NNN` / `### NFR-AREA-NNN` in docs/03-PRODUCT/PRODUCT-REQUIREMENTS.md.
  * Tests: `TST-<ELEMENT>-NN`; acceptance criteria: `AC-<ELEMENT>-NN` (each must cite >=1 TST of the same spec).
  * Interfaces: `IF-*` defined in spec front matter `interfaces_defined`; indexed in 04-ARCHITECTURE/INTERFACE-CONTRACTS.md.
"""
from __future__ import annotations
import re, sys, pathlib, collections
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
REG = DOCS / "work-elements.yaml"
PRD = DOCS / "03-PRODUCT" / "PRODUCT-REQUIREMENTS.md"
IFACE = DOCS / "04-ARCHITECTURE" / "INTERFACE-CONTRACTS.md"
STATUSES = ["TODO", "IN_PROGRESS", "DRAFT", "COMPLETE", "BLOCKED"]
SECTIONS = 27
VAGUE = ["appropriate handling", "necessary validation", "make it secure", "optimize performance",
         "support standard authentication", "handle edge cases", "as appropriate", "tbd", "to be determined"]
FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def load_registry():
    d = yaml.safe_load(REG.read_text(encoding="utf-8"))
    return d["phases"], d["elements"]


def spec_path(e):
    if e.get("spec"):
        return DOCS / e["spec"]
    return DOCS / "06-MODULES" / f"{e['id']}-{e['slug']}.md"


def requirement_ids():
    if not PRD.exists():
        return set()
    return set(re.findall(r"^#{2,4}\s+((?:N?FR)-[A-Z0-9]+-\d{3})\b", PRD.read_text(encoding="utf-8"), re.M))


def interface_index():
    if not IFACE.exists():
        return set()
    return set(re.findall(r"\b(IF-[A-Z0-9]+(?:-[A-Z0-9]+)*)\b", IFACE.read_text(encoding="utf-8")))


def topo(elements):
    by = {e["id"]: e for e in elements}
    indeg = {i: 0 for i in by}
    out = collections.defaultdict(list)
    for e in elements:
        for d in e["deps"]:
            out[d].append(e["id"]); indeg[e["id"]] += 1
    ready = sorted(i for i, n in indeg.items() if n == 0)
    order = []
    while ready:
        i = ready.pop(0); order.append(i)
        for j in sorted(out[i]):
            indeg[j] -= 1
            if indeg[j] == 0:
                ready.append(j); ready.sort()
    return order, [i for i, n in indeg.items() if n > 0]


def parse_spec(path):
    text = path.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    fm = yaml.safe_load(m.group(1)) if m else None
    body = text[m.end():] if m else text
    secs = {}
    parts = re.split(r"^##\s+(\d+)\.\s+.*$", body, flags=re.M)
    for k in range(1, len(parts), 2):
        secs[int(parts[k])] = parts[k + 1]
    return fm, body, secs


def check(final=False):
    errs, warns = [], []
    phases, elements = load_registry()
    ids = [e["id"] for e in elements]
    if len(ids) != len(set(ids)):
        errs.append("duplicate element ids")
    phase_ids = {p["id"] for p in phases}
    by = {e["id"]: e for e in elements}
    for e in elements:
        if e["status"] not in STATUSES: errs.append(f"{e['id']}: bad status {e['status']}")
        if e["id"].split("-")[1][1:] not in phase_ids: errs.append(f"{e['id']}: unknown phase")
        for d in e["deps"]:
            if d not in by: errs.append(f"{e['id']}: unknown dependency {d}")
        if e["kind"] == "module" and not e.get("slug"): errs.append(f"{e['id']}: module needs slug")
    order, cyc = topo(elements)
    if cyc: errs.append(f"dependency cycle among: {cyc}")
    reqs = requirement_ids(); ifaces = interface_index()
    defined_if = set(); used_if = set(); req_cov = collections.defaultdict(set)
    for e in elements:
        p = spec_path(e)
        if e["status"] in ("DRAFT", "COMPLETE"):
            if not p.exists():
                errs.append(f"{e['id']}: status {e['status']} but missing {p.relative_to(DOCS)}"); continue
            if e["status"] == "COMPLETE":
                for d in e["deps"]:
                    if by[d]["status"] not in ("COMPLETE",) and e["kind"] != "audit":
                        warns.append(f"{e['id']}: COMPLETE but dependency {d} is {by[d]['status']}")
        if e["kind"] != "module" or e["status"] not in ("DRAFT", "COMPLETE") or not p.exists():
            continue
        fm, body, secs = parse_spec(p)
        rel = p.relative_to(DOCS)
        if not fm: errs.append(f"{rel}: missing YAML front matter"); continue
        if fm.get("id") != e["id"]: errs.append(f"{rel}: front matter id {fm.get('id')} != {e['id']}")
        if sorted(fm.get("depends_on", [])) != sorted(e["deps"]):
            errs.append(f"{rel}: depends_on {sorted(fm.get('depends_on', []))} != registry {sorted(e['deps'])}")
        for n in range(1, SECTIONS + 1):
            if n not in secs: errs.append(f"{rel}: missing section {n}")
            elif len(secs[n].split()) < 12: errs.append(f"{rel}: section {n} too thin (<12 words)")
        for r in fm.get("requirements", []):
            if reqs and r not in reqs: errs.append(f"{rel}: unknown requirement {r}")
            req_cov[r].add(e["id"])
        if not fm.get("requirements"): errs.append(f"{rel}: no requirements cited")
        defined_if |= set(fm.get("interfaces_defined", [])); used_if |= set(fm.get("interfaces_used", []))
        low = body.lower()
        for v in VAGUE:
            if v in low: errs.append(f"{rel}: vague phrase '{v}'")
        tsts = set(re.findall(rf"\bTST-{re.escape(e['id'])}-\d{{2}}\b", body))
        acs = re.findall(rf"^\s*[-*]?\s*\**(AC-{re.escape(e['id'])}-\d{{2}})\**[:\s](.*)$", secs.get(24, ""), re.M)
        if len(tsts) < 3: errs.append(f"{rel}: fewer than 3 tests (TST-{e['id']}-NN) defined")
        if len(acs) < 3: errs.append(f"{rel}: fewer than 3 acceptance criteria (AC-{e['id']}-NN) in section 24")
        for ac, line in acs:
            if not re.search(rf"TST-{re.escape(e['id'])}-\d{{2}}", line):
                errs.append(f"{rel}: {ac} cites no TST")
        if re.search(r"\b(TODO|FIXME)\b", body): errs.append(f"{rel}: contains TODO/FIXME")
    for u in used_if - defined_if - ifaces:
        warns.append(f"interface {u} used but not defined/indexed")
    if final:
        for r in sorted(reqs):
            if not req_cov.get(r): errs.append(f"requirement {r} has no covering module spec")
        for e in elements:
            if e["status"] != "COMPLETE": errs.append(f"{e['id']} not COMPLETE at final check")
    for w in warns: print("WARN ", w)
    for x in errs: print("ERROR", x)
    print(f"{len(elements)} elements, {sum(e['status']=='COMPLETE' for e in elements)} complete, "
          f"{len(reqs)} requirements, {len(errs)} errors, {len(warns)} warnings")
    return 1 if errs else 0


def replace_block(text, name, content):
    a, b = f"<!-- BEGIN:{name} -->", f"<!-- END:{name} -->"
    block = f"{a}\n{content.rstrip()}\n{b}"
    if a in text and b in text:
        return re.sub(re.escape(a) + r".*?" + re.escape(b), lambda _: block, text, flags=re.S)
    return text.rstrip() + "\n\n" + block + "\n"


def render():
    phases, elements = load_registry()
    order, _ = topo(elements)
    rank = {i: n + 1 for n, i in enumerate(order)}
    lines = []
    for p in phases:
        es = [e for e in elements if e["id"].split("-")[1] == "P" + p["id"]]
        lines.append(f"#### PHASE-{p['id']} — {p['title']}\n")
        lines.append("| ID | Element | Pkg | Kind | Depends on | Spec | Order | Status |\n|---|---|---|---|---|---|---|---|")
        for e in es:
            rp = spec_path(e).relative_to(DOCS).as_posix()
            lines.append(f"| {e['id']} | {e['title']} | {e['pkg']} | {e['kind']} | {', '.join(d.replace('RG-','') for d in e['deps']) or '—'} | `{rp}` | {rank[e['id']]} | {e['status']} |")
        lines.append("")
    rm = DOCS / "01-MASTER-ROADMAP.md"
    if rm.exists():
        rm.write_text(replace_block(rm.read_text(encoding="utf-8"), "ELEMENTS", "\n".join(lines)), encoding="utf-8")
    cnt = collections.Counter(e["status"] for e in elements)
    pl = ["| Status | Count |\n|---|---|"] + [f"| {s} | {cnt.get(s,0)} |" for s in STATUSES]
    pl.append("\n| Phase | Complete / Total |\n|---|---|")
    for p in phases:
        es = [e for e in elements if e["id"].split("-")[1] == "P" + p["id"]]
        pl.append(f"| {p['id']} {p['title']} | {sum(e['status']=='COMPLETE' for e in es)} / {len(es)} |")
    unfinished = [i for i in order if next(e for e in elements if e["id"] == i)["status"] != "COMPLETE"]
    pl.append("\nNext 8 eligible elements in dependency order: " + (", ".join(unfinished[:8]) or "none"))
    pg = DOCS / "PROGRESS.md"
    if pg.exists():
        pg.write_text(replace_block(pg.read_text(encoding="utf-8"), "STATUS", "\n".join(pl)), encoding="utf-8")
    # traceability
    reqs = sorted(requirement_ids())
    cov = collections.defaultdict(list)
    for e in elements:
        p = spec_path(e)
        if e["kind"] == "module" and p.exists():
            fm, body, secs = parse_spec(p)
            for r in (fm or {}).get("requirements", []):
                tst = sorted(set(re.findall(rf"\bTST-{re.escape(e['id'])}-\d{{2}}\b", body)))
                cov[r].append((e, fm, tst))
    t = ["# Requirements Traceability Matrix\n", "_Generated by `tools/specgate.py render` — do not edit by hand. Requirement → Phase → Module → Interface → Test → Status._\n",
         "| Requirement | Phase | Module (element) | Interfaces defined | Tests | Status |", "|---|---|---|---|---|---|"]
    for r in reqs:
        rows = cov.get(r)
        if not rows:
            t.append(f"| {r} | — | _unassigned_ | — | — | UNCOVERED |")
        for e, fm, tst in rows or []:
            t.append(f"| {r} | {e['id'].split('-')[1][1:]} | {e['id']} {e['title']} | {', '.join(fm.get('interfaces_defined', [])) or '—'} | {', '.join(x.replace('TST-'+e['id']+'-','#') for x in tst[:6])}{' …' if len(tst)>6 else ''} | {e['status']} |")
    (DOCS / "REQUIREMENTS-TRACEABILITY.md").write_text("\n".join(t) + "\n", encoding="utf-8")

    # component catalog
    cc = DOCS / "04-ARCHITECTURE" / "COMPONENT-CATALOG.md"
    rows = ["| Module id | Element | Package | Responsibility (element title) | Depends on | Spec | Status |", "|---|---|---|---|---|---|---|"]
    for e in elements:
        if e["kind"] != "module":
            continue
        mod = "MOD-" + e["pkg"].upper() + "-" + e["slug"].upper().replace("-", "_")
        rows.append(f"| {mod} | {e['id']} | {e['pkg']} | {e['title']} | {', '.join(d.replace('RG-','') for d in e['deps'])} | `06-MODULES/{e['id']}-{e['slug']}.md` | {e['status']} |")
    if cc.exists():
        cc.write_text(replace_block(cc.read_text(encoding="utf-8"), "CATALOG", "\n".join(rows)), encoding="utf-8")
    print("rendered")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "check": sys.exit(check("--final" in sys.argv))
    if cmd == "render": render()
    elif cmd == "order":
        _, els = load_registry(); order, _ = topo(els)
        for i in order:
            e = next(x for x in els if x["id"] == i)
            if e["status"] != "COMPLETE": print(i, e["status"], e["title"])
    else: print(__doc__)


if __name__ == "__main__":
    main()
