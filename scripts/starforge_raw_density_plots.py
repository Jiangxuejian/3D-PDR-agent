#!/usr/bin/env python3
"""Generate density diagnostics for STARFORGE RAW HDF5 snapshots.

For each candidate HDF5 file under the RAW directory, this script creates:
1) A yt slice plot through the domain center.
2) A regridded 128^3 central-half-box density slice plot.
3) A density histogram plot (log10 number density).
4) A text file with 25th, 50th (median), and 75th density percentiles.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import yt
from matplotlib.colors import LogNorm


UNIT_BASE = {
    "UnitLength_in_cm": 3.085677581e18,  # 1 pc
    "UnitMass_in_g": 1.98847e33,         # 1 Msun
    "UnitVelocity_in_cm_per_s": 1.0e2,   # 1 m/s
}

GRID_DIMS = (128, 128, 128)
MEAN_MU = 2.3


def find_hdf5_files(raw_root: Path) -> list[Path]:
    files = sorted(raw_root.rglob("*.hdf5"))
    files.extend(sorted(raw_root.rglob("*.h5")))
    return sorted(set(files))


def choose_density_field(ds: yt.Dataset) -> tuple[str, str]:
    candidates = [
        ("gas", "density"),
        ("PartType0", "density"),
        ("deposit", "PartType0_smoothed_density"),
    ]

    all_fields = set(ds.field_list) | set(ds.derived_field_list)
    for field in candidates:
        if field in all_fields:
            return field

    raise RuntimeError("No supported density field found.")


def central_half_edges(ds: yt.Dataset) -> tuple[np.ndarray, np.ndarray]:
    center = ds.domain_center.to("code_length")
    half_box_width = 0.5 * ds.domain_width.to("code_length")
    left = (center - 0.5 * half_box_width).d
    right = (center + 0.5 * half_box_width).d
    return left, right


def output_dir_for_file(hdf5_file: Path, output_root: Optional[Path]) -> Path:
    if output_root is None:
        return hdf5_file.parent

    return output_root / hdf5_file.stem


def output_files_for_hdf5(hdf5_file: Path, out_dir: Path) -> dict[str, Path]:
    stem = hdf5_file.stem
    return {
        "slice": out_dir / f"{stem}_slice_plot.png",
        "grid": out_dir / f"{stem}_regridded_density_grid_slice.png",
        "hist": out_dir / f"{stem}_density_histogram.png",
        "pct": out_dir / f"{stem}_density_percentiles.txt",
    }


def ensure_number_density_field(
    ds: yt.Dataset, density_field: tuple[str, str]
) -> tuple[str, str]:
    number_density_field = ("gas", "number_density_mu23")

    all_fields = set(ds.field_list) | set(ds.derived_field_list)
    if number_density_field in all_fields:
        return number_density_field

    def _number_density(field, data):
        return data[density_field] / (MEAN_MU * yt.physical_constants.mh)

    ds.add_field(
        number_density_field,
        function=_number_density,
        sampling_type="local",
        units="cm**-3",
    )
    return number_density_field


def make_yt_slice_plot(
    ds: yt.Dataset, density_field: tuple[str, str], out_png: Path
) -> None:
    number_density_field = ensure_number_density_field(ds, density_field)
    slc = yt.SlicePlot(ds, "z", number_density_field)
    slc.set_unit(number_density_field, "cm**-3")
    slc.annotate_timestamp(corner="upper_left")
    slc.save(str(out_png))


def make_regridded_density(ds: yt.Dataset, density_field: tuple[str, str]) -> np.ndarray:
    left, right = central_half_edges(ds)
    ag = ds.arbitrary_grid(left_edge=left, right_edge=right, dims=GRID_DIMS)
    density = ag[density_field]
    n_density = (density / (MEAN_MU * yt.physical_constants.mh)).to("cm**-3")
    return n_density.v


def make_density_grid_plot(n_density: np.ndarray, out_png: Path) -> None:
    z_mid = n_density.shape[2] // 2
    fig, ax = plt.subplots(figsize=(7, 6), dpi=150)

    positive = n_density[n_density > 0]
    vmin = max(np.nanpercentile(positive, 1), 1e-10) if positive.size else 1e-10
    vmax = np.nanpercentile(positive, 99.5) if positive.size else 1.0

    im = ax.imshow(
        n_density[:, :, z_mid],
        origin="lower",
        cmap="viridis",
        norm=LogNorm(vmin=vmin, vmax=max(vmax, vmin * 10.0)),
    )
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Number density [cm^-3]")
    ax.set_title("Regridded density slice (z-mid, central half box)")
    ax.set_xlabel("x index")
    ax.set_ylabel("y index")

    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)


def make_density_histogram(n_density: np.ndarray, out_png: Path) -> None:
    positive = n_density[np.isfinite(n_density) & (n_density > 0)]
    if positive.size == 0:
        raise RuntimeError("Density grid has no positive finite values.")

    log_rho = np.log10(positive)
    counts, edges = np.histogram(log_rho, bins=40, density=True)
    centers = 0.5 * (edges[:-1] + edges[1:])

    fig, ax = plt.subplots(figsize=(7, 5), dpi=150)
    ax.plot(centers, counts, lw=2.5, color="tab:blue")
    ax.set_yscale("log")
    ax.set_xlabel("log10(number density [cm^-3])")
    ax.set_ylabel("PDF")
    ax.set_title("Density distribution in central regridded box")

    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)


def write_percentiles(n_density: np.ndarray, out_txt: Path) -> None:
    positive = n_density[np.isfinite(n_density) & (n_density > 0)]
    if positive.size == 0:
        raise RuntimeError("Density grid has no positive finite values.")

    p25, p50, p75 = np.percentile(positive, [25, 50, 75])
    with out_txt.open("w", encoding="utf-8") as f:
        f.write("# Number density percentiles (cm^-3)\n")
        f.write(f"p25 = {p25:.6e}\n")
        f.write(f"p50_median = {p50:.6e}\n")
        f.write(f"p75 = {p75:.6e}\n")


def process_one_file(hdf5_file: Path, output_root: Optional[Path], force: bool) -> None:
    out_dir = output_dir_for_file(hdf5_file, output_root)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = output_files_for_hdf5(hdf5_file, out_dir)

    if not force and all(path.exists() for path in outputs.values()):
        print(f"[SKIP] Outputs already exist for {hdf5_file}")
        return

    print(f"[INFO] Processing {hdf5_file}")
    ds = yt.load(str(hdf5_file), unit_base=UNIT_BASE)
    density_field = choose_density_field(ds)

    make_yt_slice_plot(ds, density_field, outputs["slice"])

    n_density = make_regridded_density(ds, density_field)
    make_density_grid_plot(n_density, outputs["grid"])
    make_density_histogram(n_density, outputs["hist"])
    write_percentiles(n_density, outputs["pct"])

    print(f"[OK] Wrote outputs to {out_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=Path("STARFORGE/RAW"),
        help="Directory containing RAW HDF5 snapshots.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help=(
            "Optional output directory. By default, outputs are written in the "
            "same directory as each input HDF5 file."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit for number of files to process.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Recompute outputs even if all expected output files already exist.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raw_root = args.raw_root.resolve()
    output_root = args.output_root.resolve() if args.output_root is not None else None

    if not raw_root.exists():
        raise FileNotFoundError(f"RAW directory not found: {raw_root}")

    files = find_hdf5_files(raw_root)
    if args.limit is not None:
        files = files[: args.limit]

    if not files:
        print(f"[WARN] No HDF5 files found under {raw_root}")
        return

    print(f"[INFO] Found {len(files)} HDF5 candidate files")
    for fp in files:
        try:
            process_one_file(fp, output_root, args.force)
        except Exception as exc:
            print(f"[ERROR] Failed for {fp}: {exc}")

    print("[DONE] All candidates processed.")


if __name__ == "__main__":
    main()
