"""Additional diagnostic for the 6-page revision (not part of PROTOCOL_V3; exploratory): elevation artefacts of the
game-engine (BeamNG.tech) corpus compared with measured P79 profiles.

For every BeamNG trip:
  1. share of ray-cast elevation readings that repeat the previous reading exactly while the car moves (> 1 m/s),
     split into short repeats (runs of at most SHORT_RUN readings, typical of a reading that is updated less often
     than it is logged) and long repeats (flat stretches);
  2. IRI of non-overlapping 100 m segments (continuous quarter-car run over the whole trip, mean of the two wheel
     paths, as for the raw-profile labels) from three versions of the profile on the same 0.25 m distance grid:
       logged      every reading, as used for the raw-profile labels;
       fresh       repeated readings removed before interpolation (only readings that changed);
       smoothed    logged profile after the curvature-adaptive mesh correction of the corpus's label code;
  3. Welch displacement PSD of the detrended logged and fresh profiles, and of the measured P79 profiles of LiRA-CD
     (laser 5 and 21, gap-free runs, linearly interpolated to the same 0.25 m grid).
Outputs (results/v3/): beamng_profile_artifacts.csv (per trip), profile_psd.csv (mean PSD per source),
beamng_profile_summary.json.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.signal import welch

HERE = os.path.dirname(os.path.abspath(__file__))
RESCUE = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, RESCUE)
sys.path.insert(0, os.path.join(RESCUE, "experiments"))
from common import iri, lira  # noqa: E402
import beamng_build_dataset as B  # noqa: E402  (load_trip, profiles, DX, legacy label code)

OUT = os.path.join(RESCUE, "results", "v3")
DX = B.DX                 # 0.25 m
SEG = 100.0
SHORT_RUN = 10            # readings
NPERSEG = 512             # 128 m Welch windows on the 0.25 m grid
ROUTES = {"CPH1": "urban", "CPH6": "urban", "M3": "motorway", "M13": "motorway"}


def repeats(el, moving):
    """Boolean mask of readings equal to the previous one while moving, and run lengths of repeated values."""
    same = np.concatenate([[False], np.diff(el) == 0]) & moving
    runs = np.zeros(len(el), dtype=int)          # length of the repeat run each repeated reading belongs to
    i, n = 0, len(el)
    while i < n:
        if same[i]:
            j = i
            while j < n and same[j]:
                j += 1
            runs[i:j] = j - i
            i = j
        else:
            i += 1
    return same, runs


def fresh_profile(df, side, grid):
    cd = df.cd.to_numpy(); el = df[f"road_elevation_{side}"].to_numpy()
    keep = np.concatenate([[True], np.diff(el) != 0])
    c, e = cd[keep], el[keep]
    inc = np.concatenate([[True], np.diff(c) > 0])
    return np.interp(grid, c[inc], e[inc])


def seg_iri(zl, zr):
    rl, pos = iri.continuous_rectified_slope(zl, DX)
    rr, _ = iri.continuous_rectified_slope(zr, DX)
    rs = 0.5 * (rl + rr)
    starts = np.arange(0.0, pos[-1] - SEG, SEG)
    return iri.window_iri(rs, pos, starts, SEG)


def psd(z):
    f, p = welch(z, fs=1.0 / DX, nperseg=NPERSEG, detrend="linear")
    return f, p


def main():
    rows, psd_acc = [], {}

    def add_psd(name, z, w):
        if len(z) < NPERSEG:
            return
        f, p = psd(z)
        acc = psd_acc.setdefault(name, [f, np.zeros_like(p), 0.0])
        acc[1] += w * p; acc[2] += w

    for car in ["hopper", "sunburst2", "vivace"]:
        for route in ["automation_test_track", "east_coast_usa", "west_coast_usa"]:
            for trip in sorted(os.listdir(os.path.join(B.BEAMNG_RAW, car, route))):
                if not trip.startswith("trip_"):
                    continue
                df = B.load_trip(car, route, trip)
                moving = df.speed_ms.to_numpy() > 1.0
                grid, z = B.profiles(df)
                zf = {s: fresh_profile(df, s, grid) for s in ("left", "right")}
                zs = {s: B.legacy.correct_mesh_tessellation(z[s], DX) for s in ("left", "right")}
                same, runs = repeats(df.road_elevation_left.to_numpy(), moving)
                nmov = max(int(moving.sum()), 1)
                i_log = seg_iri(z["left"], z["right"]); i_fr = seg_iri(zf["left"], zf["right"])
                i_sm = seg_iri(zs["left"], zs["right"])
                rows.append(dict(car=car, map=route, trip=trip, km=float(grid[-1] / 1000),
                                 repeat_pct=100 * same.sum() / nmov,
                                 repeat_short_pct=100 * (same & (runs <= SHORT_RUN)).sum() / nmov,
                                 repeat_long_pct=100 * (same & (runs > SHORT_RUN)).sum() / nmov,
                                 n_seg=int(np.isfinite(i_log).sum()),
                                 iri_logged=float(np.nanmean(i_log)), iri_fresh=float(np.nanmean(i_fr)),
                                 iri_smoothed=float(np.nanmean(i_sm)),
                                 iri_logged_med=float(np.nanmedian(i_log)), iri_fresh_med=float(np.nanmedian(i_fr))))
                for s in ("left", "right"):
                    add_psd("game engine, logged", z[s], grid[-1]); add_psd("game engine, fresh readings", zf[s], grid[-1])
                print(car, route, trip, {k: round(v, 2) for k, v in rows[-1].items() if isinstance(v, float)}, flush=True)

    for route, cls in ROUTES.items():
        for direction in ("HH", "VH"):
            zp = lira.load_zp(route, direction)
            for s0, s1 in lira.zp_runs(zp):
                d = zp.dist.to_numpy()[s0:s1]
                g = np.arange(d[0], d[-1], DX)
                for col in ("z_left", "z_right"):
                    v = zp[col].to_numpy()[s0:s1]
                    ok = np.isfinite(v)
                    if ok.sum() < 2:
                        continue
                    add_psd(f"P79, {cls}", np.interp(g, d[ok], v[ok]), g[-1] - g[0])
        print("P79", route, flush=True)

    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(OUT, "beamng_profile_artifacts.csv"), index=False)
    recs = []
    for name, (f, p, w) in psd_acc.items():
        for fi, pi in zip(f, p / w):
            recs.append(dict(source=name, n_cyc_per_m=fi, psd_m2_per_cyc_m=pi))
    P = pd.DataFrame(recs)
    P.to_csv(os.path.join(OUT, "profile_psd.csv"), index=False)

    # slope-variance share at wavelengths 0.5-2 m within 0.5-30 m (slope PSD = (2 pi n)^2 * displacement PSD)
    share = {}
    for name, g in P.groupby("source"):
        n = g.n_cyc_per_m.to_numpy(); sp = (2 * np.pi * n) ** 2 * g.psd_m2_per_cyc_m.to_numpy()
        band = (n >= 1 / 30) & (n <= 2.0); short = (n >= 0.5) & (n <= 2.0)
        share[name] = float(np.trapezoid(sp[short], n[short]) / np.trapezoid(sp[band], n[band]))
    w = D.km / D.km.sum()
    summ = dict(n_trips=len(D), km=float(D.km.sum()),
                repeat_pct_min=float(D.repeat_pct.min()), repeat_pct_max=float(D.repeat_pct.max()),
                repeat_pct_mean=float(np.average(D.repeat_pct, weights=w)),
                repeat_short_pct_mean=float(np.average(D.repeat_short_pct, weights=w)),
                repeat_long_pct_mean=float(np.average(D.repeat_long_pct, weights=w)),
                iri_logged_mean=float(np.average(D.iri_logged, weights=D.n_seg)),
                iri_fresh_mean=float(np.average(D.iri_fresh, weights=D.n_seg)),
                iri_smoothed_mean=float(np.average(D.iri_smoothed, weights=D.n_seg)),
                short_wavelength_slope_share=share)
    json.dump(summ, open(os.path.join(OUT, "beamng_profile_summary.json"), "w"), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
