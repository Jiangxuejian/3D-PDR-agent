#!/usr/bin/env python3
"""
RT-vis: Convert RTsynth post-processed output files to PNG images.

Usage
-----
# Convert all _cds.dat (column density) files in the current directory:
    python rt_vis.py --pattern "RT_*_cds.dat" --col 2 --name NH2 --threshold 1e13

# Convert all CO10 (integrated intensity) files:
    python rt_vis.py --pattern "RT_*_CO10.dat" --col 2 --name ICO --threshold 1e-4

# Convert all files recursively in a Products/RTsynth subtree:
    python rt_vis.py --dir Products/RTsynth --pattern "RT_*_cds.dat" --recursive

# Dry run (list matching files only):
    python rt_vis.py --pattern "RT_*_cds.dat" --dry-run

Arguments
---------
--dir          Root directory to search (default: current working directory)
--pattern      Glob pattern for input files (default: "RT_*_cds.dat")
--recursive    Search recursively under --dir
--col          Data column index to visualise (0=x, 1=y, 2=value; default: 2)
--name         Physical quantity name shown in saved filename suffix (default: NH2)
--threshold    Mask and vmin: pixels below this value are hidden (default: 1e13)
--vmax-factor  vmax = threshold * vmax_factor (default: 1e10)
--cmap         Matplotlib colormap name (default: inferno)
--dpi          Output image DPI (default: 150)
--overwrite    Overwrite existing .png files (default: skip)
--dry-run      List matching files and exit without writing anything
"""

import argparse
import glob
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # non-interactive backend: safe for headless runs
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm


# ---------------------------------------------------------------------------
# Core rendering
# ---------------------------------------------------------------------------

def render_file(
    filepath: str,
    col_idx: int = 2,
    col_name: str = "NH2",
    mask_threshold: float = 1e13,
    vmax_factor: float = 1e10,
    cmap_name: str = "inferno",
    dpi: int = 150,
    overwrite: bool = False,
) -> str:
    """
    Render a single RTsynth output file to a PNG with the same stem name.

    Returns one of: "ok", "skip", "error".
    """
    output_path = Path(os.path.splitext(filepath)[0] + ".png")

    if output_path.exists() and not overwrite:
        print(f"  [SKIP] Already exists: {output_path}")
        return "skip"

    # --- load ----------------------------------------------------------------
    try:
        df = pd.read_csv(filepath, sep=r"\s+", header=None, engine="python")
    except Exception as exc:
        print(f"  [ERROR] Could not read {filepath}: {exc}")
        return "error"

    if df.shape[1] <= col_idx:
        print(f"  [ERROR] File has only {df.shape[1]} columns; --col {col_idx} out of range.")
        return "error"

    # --- coordinates & extent ------------------------------------------------
    df[0] = df[0].round(6)
    df[1] = df[1].round(6)

    unique_x = sorted(df[0].unique())
    unique_y = sorted(df[1].unique())
    dx = unique_x[1] - unique_x[0] if len(unique_x) > 1 else 1.0
    dy = unique_y[1] - unique_y[0] if len(unique_y) > 1 else 1.0

    extent = [
        df[0].min() - dx / 2,
        df[0].max() + dx / 2,
        df[1].min() - dy / 2,
        df[1].max() + dy / 2,
    ]

    # --- pivot to 2-D grid ---------------------------------------------------
    # 2-D map files should have one value per (x, y). Files like RT_vel_* often
    # contain multiple velocity channels per (x, y), causing duplicate pairs.
    dup_xy = int(df.duplicated(subset=[0, 1]).sum())
    if dup_xy > 0:
        print(
            f"  [SKIP] Non-2D map (found {dup_xy} duplicate x/y rows): {filepath}"
        )
        return "skip"

    try:
        grid = df.pivot(index=1, columns=0, values=col_idx)
    except Exception as exc:
        print(f"  [ERROR] Pivot failed for {filepath}: {exc}")
        return "error"

    # --- mask ----------------------------------------------------------------
    grid_masked = grid.copy().astype(float)
    grid_masked[grid_masked < mask_threshold] = np.nan

    valid = grid_masked.values.flatten()
    valid = valid[~np.isnan(valid)]
    if len(valid) == 0:
        print(f"  [WARN]  No pixels above threshold={mask_threshold:.2e} in {filepath}; skipping.")
        return "skip"

    vmin = mask_threshold
    vmax = mask_threshold * vmax_factor

    # --- figure (borderless) -------------------------------------------------
    ny, nx = grid_masked.shape
    fig_width = 8.0
    fig_height = fig_width * (ny / nx)

    fig = plt.figure(figsize=(fig_width, fig_height))
    ax = plt.Axes(fig, [0.0, 0.0, 1.0, 1.0])
    ax.set_facecolor("black")
    ax.set_axis_off()
    fig.add_axes(ax)

    cmap = plt.get_cmap(cmap_name).copy()
    cmap.set_bad(color="black")

    ax.imshow(
        grid_masked,
        origin="lower",
        extent=extent,
        norm=LogNorm(vmin=vmin, vmax=vmax),
        cmap=cmap,
        aspect="equal",
    )

    # --- save ----------------------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(output_path), dpi=dpi, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    print(f"  [OK]   {output_path}")
    return "ok"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(
        description="Convert RTsynth output .dat files to PNG images.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--dir", default=".", help="Root directory to search")
    p.add_argument("--pattern", default="RT_*_cds.dat", help="Glob pattern for input files")
    p.add_argument("--recursive", action="store_true", help="Search recursively")
    p.add_argument("--col", type=int, default=2, help="Data column index to visualise (default: 2)")
    p.add_argument("--name", default="NH2", help="Physical quantity name (label only)")
    p.add_argument("--threshold", type=float, default=1e13, help="Mask threshold and vmin")
    p.add_argument("--vmax-factor", type=float, default=1e10, help="vmax = threshold * vmax_factor")
    p.add_argument("--cmap", default="inferno", help="Matplotlib colormap name")
    p.add_argument("--dpi", type=int, default=150, help="Output DPI")
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing PNG files")
    p.add_argument("--dry-run", action="store_true", help="List files only, do not write")
    return p.parse_args()


def main():
    args = parse_args()

    root = Path(args.dir).resolve()
    if not root.is_dir():
        print(f"[ERROR] --dir '{args.dir}' is not a valid directory.")
        sys.exit(1)

    # --- collect files -------------------------------------------------------
    if args.recursive:
        files = sorted(root.rglob(args.pattern))
    else:
        files = sorted(root.glob(args.pattern))

    if not files:
        print(f"[INFO] No files matched pattern '{args.pattern}' under {root}")
        sys.exit(0)

    print(f"[INFO] Found {len(files)} file(s) matching '{args.pattern}'")

    if args.dry_run:
        for f in files:
            print(f"  {f}")
        sys.exit(0)

    # --- process -------------------------------------------------------------
    ok = skip = fail = 0
    for f in files:
        print(f"Processing: {f}")
        status = render_file(
            str(f),
            col_idx=args.col,
            col_name=args.name,
            mask_threshold=args.threshold,
            vmax_factor=args.vmax_factor,
            cmap_name=args.cmap,
            dpi=args.dpi,
            overwrite=args.overwrite,
        )
        if status == "ok":
            ok += 1
        elif status == "skip":
            skip += 1
        else:
            fail += 1

    print(f"\n[DONE] {ok} rendered | {skip} skipped | {fail} errors")


if __name__ == "__main__":
    main()
