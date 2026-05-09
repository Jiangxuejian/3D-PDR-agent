#!/usr/bin/env python3
"""Convert INPUT snapshot HDF5 to RTsynth velocity file format.

The output is a plain text file with one row per cell:
  vx vy vz

where each component is written in cm/s, matching RTsynth expectations
when VELOCITY mode is enabled.
"""

from __future__ import annotations

import argparse
import re
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
        "--output-vel",
        type=Path,
        default=None,
        help="Output velocity file path (default: snapshot_XXX_v.dat next to input)",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=None,
        help="Grid resolution per axis (default: infer from simulation folder token like R10)",
    )
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
        "--overwrite",
        action="store_true",
        help="Overwrite output velocity file if it already exists",
    )
    return parser.parse_args()


def infer_n_from_sim_folder(input_hdf5: Path) -> int:
    # Expected path shape: .../<sim>/snapshots/<snapshot>/snapshot_xxx.hdf5
    # Example sim folder: M2e4_R10_Z1_... -> n = 10 (from second token R10)
    sim_folder = input_hdf5.parent.parent.parent.name
    parts = sim_folder.split("_")
    if len(parts) < 2:
        raise ValueError(f"Could not parse simulation folder from path: {input_hdf5}")

    second = parts[1]
    match = re.fullmatch(r"R([0-9]+(?:\.[0-9]+)?)", second)
    if not match:
        raise ValueError(
            f"Could not infer n from simulation token '{second}' in folder '{sim_folder}'"
        )

    value = float(match.group(1))
    if not value.is_integer():
        raise ValueError(f"Inferred n is not an integer from token '{second}'")
    return int(value)


def _to_cms(field: yt.YTArray) -> np.ndarray:
    try:
        return field.to_value("cm/s")
    except Exception:
        return field.v


def main() -> None:
    args = parse_args()

    input_hdf5 = args.input_hdf5
    if not input_hdf5.exists():
        raise FileNotFoundError(f"Input file not found: {input_hdf5}")

    default_output = input_hdf5.with_name(f"{input_hdf5.stem}_v.dat")
    output_vel = args.output_vel if args.output_vel is not None else default_output
    output_vel.parent.mkdir(parents=True, exist_ok=True)

    if output_vel.exists() and not args.overwrite:
        raise FileExistsError(
            f"Output already exists: {output_vel}. Use --overwrite to replace it."
        )

    ds = yt.load(str(input_hdf5), unit_base=UNIT_BASE)

    n = args.n if args.n is not None else infer_n_from_sim_folder(input_hdf5)
    if n <= 0:
        raise ValueError(f"Invalid grid size n={n}; expected positive integer")

    ag = ds.arbitrary_grid(
        left_edge=args.left_edge,
        right_edge=args.right_edge,
        dims=(n, n, n),
    )

    vx = _to_cms(ag[("gas", "velocity_x")])
    vy = _to_cms(ag[("gas", "velocity_y")])
    vz = _to_cms(ag[("gas", "velocity_z")])

    expected_shape = (n, n, n)
    if vx.shape != expected_shape or vy.shape != expected_shape or vz.shape != expected_shape:
        raise ValueError(
            "Unexpected velocity grid shape: "
            f"vx={vx.shape}, vy={vy.shape}, vz={vz.shape}, expected={expected_shape}"
        )

    if not (np.isfinite(vx).all() and np.isfinite(vy).all() and np.isfinite(vz).all()):
        raise ValueError("Velocity grid contains NaN/Inf values")

    # Flatten in C-order so k-index changes fastest, matching ci/cj/ck read loops.
    data = np.column_stack([vx.flatten(), vy.flatten(), vz.flatten()])
    expected_rows = n ** 3
    if data.shape != (expected_rows, 3):
        raise ValueError(
            f"Unexpected output matrix shape {data.shape}; expected ({expected_rows}, 3)"
        )

    np.savetxt(output_vel, data, fmt="%.6e")

    print(f"[OK] Wrote {output_vel}")
    print(f"[INFO] Grid: {n}^3")
    print(
        "[INFO] |v| max (cm/s): "
        f"{np.sqrt(vx * vx + vy * vy + vz * vz).max():.3e}"
    )


if __name__ == "__main__":
    main()
