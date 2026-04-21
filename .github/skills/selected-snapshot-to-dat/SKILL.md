---
name: selected-snapshot-to-dat
description: 'When user selects snapshot(s) for next step: mirror RAW structure into SELECTED, create symlinks, and convert each selected snapshot to 3D-PDR .dat input.'
argument-hint: 'Provide one or more snapshot ids or paths to prepare in SELECTED and convert to .dat.'
user-invocable: true
disable-model-invocation: false
---

# Selected Snapshot To DAT

## When To Use
- User selects one or multiple snapshots for downstream 3D-PDR processing.
- User wants SELECTED to mirror RAW for chosen snapshots.
- User wants `.dat` files generated from selected snapshot HDF5 files.

## Inputs To Collect
- Selected snapshot list:
  - Snapshot ids (for example `076`, `810`), or
  - Full HDF5 paths.
- Optional conversion parameters:
  - Grid size `N` (default 128)
  - Regridding bounds (default left=[400,400,400], right=[600,600,600])

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

3. Convert each linked SELECTED snapshot to `.dat`.
   - Run:
     - `scripts/convert_snapshot_hdf5_to_dat.py <selected_snapshot_hdf5>`
   - Expected output:
     - `STARFORGE/SELECTED/<sim>/snapshots/<snapshot>/snapshot_<snapshot>.dat`

4. Validate and summarize.
   - Check symlink exists and resolves.
   - Check `.dat` exists and record size.
   - Report per-snapshot success/failure and key warnings.

## Decision Rules
- RAW remains source of truth; SELECTED holds links and derived outputs.
- Continue batch processing on independent failures; report failures at end.
- If conversion values look suspicious (for example max density near zero), flag and suggest checking bounds/field mapping.

## Completion Checklist
- SELECTED folder structure mirrors RAW for each selected snapshot.
- Symlink exists for each selected snapshot.
- `.dat` generated for each successful conversion.
- Final report includes exact output paths and any caveats.
