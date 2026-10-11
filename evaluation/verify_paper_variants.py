"""Checks of the two paper variants (6-page main.tex, 10-page main_10p.tex) and their supplements
(results/v3/verification_paper_variants.json).

1. page limits; clean LaTeX logs; no '??' in any PDF;
2. none of the phrases that refer to earlier drafts, review rounds or protocol bookkeeping appears in any PDF;
3. every number macro used in any source or included table is defined, and no macro value changed relative to the
   10-page manuscript checkpoint (checkpoints/v3_10p_2026-10-12) - only new macros were added;
4. the substantive corrections of the final audit (2026-10-11) are still stated in both variants;
5. the game-engine diagnostic macros are re-derived from its result files;
6. PDFs are newer than their sources; frozen protocol and checkpoints are intact.
Exits non-zero if any check fails.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import sys

import numpy as np
import pandas as pd
from pypdf import PdfReader

RR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P, T = os.path.join(RR, "paper"), os.path.join(RR, "tables")
CK10 = os.path.join(RR, "checkpoints", "v3_10p_2026-10-12")
CHECKS = []


def check(name, ok, **info):
    CHECKS.append(dict(check=name, passed=bool(ok), **{k: (v if isinstance(v, (str, int, float, bool, list, dict)) or v is None
                                                          else str(v)) for k, v in info.items()}))
    print(("PASS " if ok else "FAIL ") + name + ("  " + json.dumps(info, default=str)[:300] if info else ""))


def macros(folder):
    pat = re.compile(r"\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}")
    out = {}
    for f in ("numbers.tex", "numbers_v2.tex", "numbers_v3.tex"):
        out.update(dict(pat.findall(open(os.path.join(folder, f), encoding="utf-8").read())))
    return out


def text(pdf):
    return re.sub(r"\s+", " ", " ".join(p.extract_text() or "" for p in PdfReader(pdf).pages))


def expand(path, seen=None):
    """source with its \\input files (sections and tables), comments removed"""
    seen = seen or set()
    src = re.sub(r"(?<!\\)%.*", "", open(path, encoding="utf-8").read())

    def rep(m):
        name = m.group(1)
        if name.startswith("numbers") or name.startswith("references_cited"):
            return ""
        p = os.path.normpath(os.path.join(os.path.dirname(path), name if name.endswith(".tex") else name + ".tex"))
        if os.path.exists(p) and p not in seen:
            seen.add(p)
            return expand(p, seen)
        return ""
    return re.sub(r"\\input\{([^}]*)\}", rep, src)


DOCS = {"main": 6, "main_10p": 10, "supplementary": None, "supplementary_10p": None}

# ---------------------------------------------------------------- 1. build
for d, limit in DOCS.items():
    pdf, log = os.path.join(P, d + ".pdf"), os.path.join(P, d + ".log")
    n = len(PdfReader(pdf).pages)
    lg = open(log, encoding="latin-1").read()
    bad = [w for w in ("undefined", "Overfull", "Undefined control sequence", "Emergency stop") if w in lg]
    check(f"{d}.pdf: clean log and no '??'", not bad and "??" not in text(pdf), pages=n, log_problems=bad)
    if limit:
        check(f"{d}.pdf within {limit} pages", n <= limit, pages=n)
check("main.pdf fills exactly 6 pages", len(PdfReader(os.path.join(P, "main.pdf")).pages) == 6)

# ---------------------------------------------------------------- 2. standalone wording
BLACK = ["our earlier", "earlier study", "earlier pipeline", "unpublished", "first version", "second version", "third version",
         "negative reference", "evidence class", "class C1", "class R", "class E", "class S", "re-analys", "dated local",
         "dated file", "protocol freeze", "frozen", "first protocol", "second protocol", "third protocol", "analysis round",
         "legacy", "revises an", "correction to our", "reviewer", "independent review", "pre-registered", "earlier label",
         "earlier split", "earlier recipe", "our first", "our second", "working copy"]
for d in DOCS:
    t = text(os.path.join(P, d + ".pdf")).lower()
    hits = {b: t.count(b.lower()) for b in BLACK if b.lower() in t}
    check(f"{d}.pdf: no wording about earlier drafts, reviews or protocol bookkeeping", not hits, hits=hits)

# ---------------------------------------------------------------- 3. macros
M, M10 = macros(P), macros(os.path.join(CK10, "paper"))
changed = sorted(k for k in M10 if M.get(k) != M10[k])
added = sorted(k for k in M if k not in M10)
check("no macro value changed relative to the 10-page checkpoint (only additions)", not changed, changed=changed[:10],
      added=added)
used = set()
for d in ("main.tex", "main_10p.tex", "supplementary.tex"):
    used |= set(re.findall(r"\\([A-Za-z]+)", expand(os.path.join(P, d))))
prefixes = ("po", "cu", "bl", "ba", "ld", "rp", "sr", "ns", "pd", "re", "mt", "kd", "vp", "vr", "vv", "pc", "vb", "el", "ep",
            "ss", "sp", "bg", "inv", "ud", "bj", "rk", "lira", "acf", "inf", "ar", "vs", "rbv", "ge", "bng", "legacy", "iriVal",
            "align", "sim", "hf", "pvs", "disc")
cand = {u for u in used if u.startswith(prefixes) and any(c.isupper() for c in u[1:])}
undefined = sorted(u for u in cand if u not in M)
check("every number macro used in either variant, the supplement and the included tables is defined", not undefined,
      undefined=undefined[:20], n_used=len(cand))

# ---------------------------------------------------------------- 4. final-audit corrections still stated
T6, T10 = text(os.path.join(P, "main.pdf")), text(os.path.join(P, "main_10p.pdf"))
TS = text(os.path.join(P, "supplementary.pdf"))
need = {
    "ranking bound names its exceptions": (["LightGBM without speed inputs and the speed-only model"], [T6, T10]),
    "speed-CV caveat": (["not robust to controlling for within-pass speed variation"], [T6]),
    "speed-CV caveat (10 p)": (["is therefore not established"], [T10]),
    "class level = mean of its two routes": (["averaged over its two routes"], [T6]),
    "class level = mean of its two routes (10 p)": (["mean of the levels of its two routes"], [T10]),
    "configuration selection only for whole-route real LightGBM": (["inner leave-one-route-out validation"], [T6, T10]),
    "release statement": (["will be released with the published version"], [T6, T10]),
    "Nitsche details attributed to Bajic et al.": (["as described in"], [T6]),
    "Nitsche details attributed to Bajic et al. (10 p)": (["according to Bajic et al."], [T10]),
    "exploratory status stated": (["exploratory"], [T6, T10, TS]),
    "plans not registered publicly": (["not registered publicly"], [TS]),
    "computations before the plans disclosed": (["neither they nor the two hypotheses are confirmatory"], [TS]),
    "analyses added after results were known disclosed": (["six further analyses were added after some of their results were known"], [TS]),
    "re-run of the robustness experiment disclosed": (["first run with independent draws per perturbation level"], [TS]),
}
for name, (phrases, docs) in need.items():
    miss = [p for p in phrases for t in docs if p not in t]
    check(f"stated: {name}", not miss, missing=miss)

# ---------------------------------------------------------------- 5. game-engine diagnostic
GA = pd.read_csv(os.path.join(RR, "results", "v3", "beamng_profile_artifacts.csv"))
GS = json.load(open(os.path.join(RR, "results", "v3", "beamng_profile_summary.json"), encoding="utf-8"))
ok = (f"{GA.repeat_pct.min():.0f}" == M["geRepeatMin"] and f"{GA.repeat_pct.max():.0f}" == M["geRepeatMax"]
      and f"{np.average(GA.iri_logged, weights=GA.n_seg):.1f}" == M["geIriLogged"]
      and f"{np.average(GA.iri_fresh, weights=GA.n_seg):.1f}" == M["geIriFresh"]
      and f"{np.average(GA.iri_smoothed, weights=GA.n_seg):.1f}" == M["geIriSmoothed"])
check("game-engine macros re-derived from the per-trip results", ok,
      printed=[M[k] for k in ("geRepeatMin", "geRepeatMax", "geIriLogged", "geIriFresh", "geIriSmoothed")])
check("logged-elevation IRI agrees with the raw-label mean of the BeamNG dataset", abs(GS["iri_logged_mean"] - float(M["bngIriRawMean"])) < 0.05,
      diagnostic=round(GS["iri_logged_mean"], 3), labels=M["bngIriRawMean"])
check("removing repeated readings does not lower the IRI (claim in both variants)", GS["iri_fresh_mean"] > GS["iri_logged_mean"])
PP = pd.read_csv(os.path.join(RR, "results", "v3", "profile_psd.csv"))


def bp(src, a, b):
    g = PP[PP.source == src]
    n, p = g.n_cyc_per_m.to_numpy(), g.psd_m2_per_cyc_m.to_numpy()
    s = (n >= 1 / a) & (n <= 1 / b)
    return float(np.trapezoid(p[s], n[s]))
r_long = bp("game engine, logged", 30, 10) / bp("P79, urban", 30, 10)
r_short = [bp("game engine, logged", a, b) / bp("P79, urban", a, b) for a, b in ((5, 2), (2, 1), (1, 0.5))]
check("game-engine power ratios rise toward short wavelengths and match the macros",
      min(r_short) > r_long and f"{r_long:.0f}" == M["gePsdUrbanLong"] and f"{min(r_short):.0f}" == M["gePsdUrbanShortMin"],
      long=round(r_long, 1), short=[round(x, 1) for x in r_short])

# ---------------------------------------------------------------- 6. freshness and integrity
for d, srcs in (("main", ["main.tex", "fig_pipeline.tex", "references_cited.tex"] + glob.glob(os.path.join(P, "sections", "*.tex"))),
                ("main_10p", ["main_10p.tex", "fig_pipeline.tex", "references_cited_10p.tex"] + glob.glob(os.path.join(P, "sections_10p", "*.tex"))),
                ("supplementary", ["supplementary.tex"]), ("supplementary_10p", ["supplementary_10p.tex", "supplementary.tex"])):
    files = [os.path.join(P, s) if not os.path.isabs(s) else s for s in srcs]
    files += glob.glob(os.path.join(P, "numbers*.tex")) + glob.glob(os.path.join(T, "*.tex"))
    newest = max(os.path.getmtime(f) for f in files)
    check(f"{d}.pdf newer than its sources, tables and macros", os.path.getmtime(os.path.join(P, d + ".pdf")) >= newest)
h = hashlib.sha256(open(os.path.join(RR, "evaluation", "PROTOCOL_V3.md"), "rb").read()).hexdigest()
check("PROTOCOL_V3.md unchanged", h == "994cd02729a8bf3b4ec3040bedc2b83bc7647227772b56f87eca7831a415ccc6")
for cp in ("v2_2026-10-03", "v3_2026-10-11", "v3_10p_2026-10-12"):
    base = os.path.join(RR, "checkpoints", cp)
    bad, n = [], 0
    for line in open(os.path.join(base, "MANIFEST.sha256"), encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        dig, rel = line.split(None, 1)
        rel = rel.lstrip("*")
        n += 1
        f = os.path.join(base, rel)
        if not os.path.exists(f) or hashlib.sha256(open(f, "rb").read()).hexdigest() != dig:
            bad.append(rel)
    check(f"checkpoint {cp} matches its manifest", not bad, files=n, mismatched=bad[:5])

out = dict(n_checks=len(CHECKS), n_failed=sum(not c["passed"] for c in CHECKS), checks=CHECKS)
json.dump(out, open(os.path.join(RR, "results", "v3", "verification_paper_variants.json"), "w", encoding="utf-8"), indent=1)
print(f"{out['n_checks']} checks, {out['n_failed']} failed -> results/v3/verification_paper_variants.json")
sys.exit(1 if out["n_failed"] else 0)
