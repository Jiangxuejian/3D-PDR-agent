---
name: sel-dat
description: 'When user selects snapshot(s) for next step: mirror RAW structure into SELECTED, create symlinks, and always generate both 3D-PDR .dat input and RTsynth velocity files in one step.'
argument-hint: 'Provide one or more snapshot ids or paths; this skill always generates paired outputs (.dat/.data + velocity) in SELECTED.'
user-invocable: true
disable-model-invocation: false
---

# Selected Snapshot To DAT

## When To Use
- User selects one or multiple snapshots for downstream 3D-PDR processing.
- User wants SELECTED to mirror RAW for chosen snapshots.
- User wants `.dat`/`.data` files generated from selected snapshot HDF5 files.
- User wants RTsynth-ready velocity files generated as a required paired output.

## Inputs To Collect
- Selected snapshot list:
  - Snapshot ids (for example `076`, `810`), or
  - Full HDF5 paths.
- Optional conversion parameters:
  - Grid size `N` (default 128)
  - Regridding bounds (default left=[400,400,400], right=[600,600,600])
  - Velocity filename pattern (default `snapshot_<snapshot>_v.dat`)
  - `force_overwrite` for regenerating existing `.dat` or velocity outputs (default: off)

## Required Preconditions
- Conversion scripts exist:
  - `scripts/convert_snapshot_hdf5_to_dat.py`
  - `scripts/convert_snapshot_hdf5_to_velocity_dat.py`
- Python dependencies for conversion are available (`yt`, `numpy`).
- For each selected snapshot, source HDF5 is readable.

## Procedure
1. Resolve each selected snapshot to a RAW source path.
   - Pattern:
     - `STARFORGE/RAW/<sim>/snapshots/<snapshot>/snapshot_<snapshot>.hdf5`
   - If id-only input is ambiguous (multiple matches), ask user to choose simulation.

2. Mirror RAW structure in SELECTED and create symlink for each snapshot.
   - Create target folder:
     - `STARFORGE/SELECTED/<sim>/snapshots/<snapshot>/`
   - Create/update symlink:
     - `STARFORGE/SELECTED/<sim>/snapshots/<snapshot>/snapshot_<snapshot>.hdf5`

3. Generate RTsynth velocity file for each selected snapshot (required, no skip mode).
   - Run:
     - `scripts/convert_snapshot_hdf5_to_velocity_dat.py <selected_snapshot_hdf5>`
     - Add `--overwrite` only when `force_overwrite` is enabled.
   - Expected output:
     - `STARFORGE/SELECTED/<sim>/snapshots/<snapshot>/snapshot_<snapshot>_v.dat`

4. Convert each linked SELECTED snapshot to `.dat`.
   - Run:
     - `scripts/convert_snapshot_hdf5_to_dat.py <selected_snapshot_hdf5>`
     - If the `.dat` output already exists and `force_overwrite` is off, fail this snapshot with a clear overwrite-required message.
   - Expected output:
     - `STARFORGE/SELECTED/<sim>/snapshots/<snapshot>/snapshot_<snapshot>.dat`

5. Validate and summarize.
   - Check symlink exists and resolves.
  - Check velocity file exists and record size.
   - Check `.dat` exists and record size.
  - Confirm both files are present as a paired result for each snapshot.
  - If either output is missing, mark the snapshot as failed (not partial success).
   - Report per-snapshot success/failure and key warnings.

## Decision Rules
- RAW remains source of truth; SELECTED holds links and derived outputs.
- Velocity file generation is mandatory whenever `.dat`/`.data` generation is requested.
- Downstream RT post-processing must reuse the generated `snapshot_<snapshot>_v.dat`; do not regenerate unless user explicitly asks for overwrite/rebuild.
- Treat `.dat` and velocity as an atomic pair for status reporting.
- Continue batch processing on independent failures; report failures at end.
- If conversion values look suspicious (for example max density near zero), flag and suggest checking bounds/field mapping.

## Completion Checklist
- SELECTED folder structure mirrors RAW for each selected snapshot.
- Symlink exists for each selected snapshot.
- Velocity file generated for each successful snapshot.
- `.dat`/`.data` generated for each successful conversion.
- Final report includes exact output paths and any caveats.
