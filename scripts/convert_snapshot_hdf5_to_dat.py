#!/usr/bin/env python3
"""Convert STARFORGE snapshot HDF5 to 3D-PDR .dat format.

This follows the notebook workflow:
- Load snapshot with yt unit_base.
- Regrid to N^3 on the selected box with arbitrary_grid.
- Convert mass density to number density.
- Write x, y, z, number_density with two-line header:
  1) N N N
  2) box_size_pc box_size_pc box_size_pc
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import yt


UNIT_BASE = {
    "UnitLength_in_cm": 3.085677581e18,   # 1 pc
    "UnitMass_in_g": 1.98847e33,          # 1 Msun
    "UnitVelocity_in_cm_per_s": 1.0e2,    # 1 m/s
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_hdf5", type=Path, help="Input snapshot_XXX.hdf5 path")
    parser.add_argument(
        "--output-dat",
        type=Path,
        default=None,
        help="Output .dat file path (default: snapshot_XXX.dat next to input)",
    )
    parser.add_argument("--n", type=int, default=128, help="Grid resolution per axis")
    parser.add_argument(
        "--left-edge",
        type=float,
        nargs=3,
        default=[400.0, 400.0, 400.0],
        metavar=("LX", "LY", "LZ"),
        help="Arbitrary-grid left edge in code length units",
    )
    parser.add_argument(
        "--right-edge",
        type=float,
        nargs=3,
        default=[600.0, 600.0, 600.0],
        metavar=("RX", "RY", "RZ"),
        help="Arbitrary-grid right edge in code length units",
    )
    parser.add_argument(
        "--mu",
        type=float,
        default=2.3,
        help="Mean molecular weight used for number-density conversion",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_hdf5 = args.input_hdf5
    if not input_hdf5.exists():
        raise FileNotFoundError(f"Input file not found: {input_hdf5}")

    output_dat = (
        args.output_dat
        if args.output_dat is not None
        else input_hdf5.with_suffix(".dat")
    )
    output_dat.parent.mkdir(parents=True, exist_ok=True)

    ds = yt.load(str(input_hdf5), unit_base=UNIT_BASE)

    n = args.n
    box_size_pc = ds.domain_width.value[0]

    ag = ds.arbitrary_grid(
        left_edge=args.left_edge,
        right_edge=args.right_edge,
        dims=(n, n, n),
    )

    density_grid = ag[("gas", "density")].v
    n_density = density_grid / (args.mu * yt.physical_constants.mh)

    box_size_slice = args.right_edge[0] - args.left_edge[0]
    cell_size = box_size_slice / n
    coords = np.linspace(cell_size / 2.0, box_size_slice - cell_size / 2.0, n)

    x_grid, y_grid, z_grid = np.meshgrid(coords, coords, coords, indexing="ij")

    x = x_grid.flatten()
    y = y_grid.flatten()
    z = z_grid.flatten()
    density = n_density.value.flatten()

    data = np.column_stack([x, y, z, density])

    with output_dat.open("w", encoding="utf-8") as f:
        f.write(f"{n}\t{n}\t{n}\n")
        f.write(f"{box_size_pc}\t {box_size_pc}\t {box_size_pc} \n")
        np.savetxt(f, data, fmt="%.6e")

    print(f"[OK] Wrote {output_dat}")
    print(f"[INFO] Grid: {n}^3")
    print(f"[INFO] Number density max: {np.max(n_density.value):.3e} cm^-3")


if __name__ == "__main__":
    main()
