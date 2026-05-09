---
name: curate-hydro
description: "Curate hydrodynamical snapshots for 3D-PDR: optionally place incoming HDF5 files into INPUT/RAW, mirror selected files into INPUT/SELECTED, and generate paired density DAT plus RTsynth velocity DAT files."
argument-hint: "Provide one or more snapshot ids or HDF5 paths; optionally include simulation folder, RAW/SELECTED placement, conversion bounds, grid size, and force mode."
user-invocable: true
disable-model-invocation: false
---

# Curate Hydro

## When To Use
- User has selected one or more hydrodynamical snapshots for downstream 3D-PDR processing.
- User provides an HDF5 file that needs to be placed under `INPUT/RAW`.
- User already has an input file somewhere under `INPUT/` and wants to convert it for 3D-PDR.
- User wants `INPUT/SELECTED` to mirror RAW for chosen snapshots.
- User wants both required derived files generated as one paired result:
  - 3D-PDR density `.dat`
  - RTsynth velocity `*_v.dat`

## Minimal Workflow Position
If the user already knows the input HDF5 file, the workflow can start here:

`/curate-hydro -> /run-pdr -> /run-rtsynth`

`/preview-hydro` is optional and only helps decide which hydro snapshots to curate.

## Inputs To Collect
- Snapshot targets:
  - Full HDF5 paths, or
  - Snapshot ids plus simulation folder, or
  - Existing files under `INPUT/RAW` or `INPUT/SELECTED`.
- Optional placement inputs:
  - Source file or download link.
  - Simulation folder name.
  - Snapshot id.
  - Expected filename, normally `snapshot_<snapshot>.hdf5`.
- Optional conversion parameters:
  - Grid size `N` (default: infer from simulation folder when scripts allow it).
  - Regridding bounds (default left=[400,400,400], right=[600,600,600] in conversion scripts).
  - Velocity filename pattern (default `snapshot_<snapshot>_v.dat`).
  - `force_overwrite` for regenerating existing `.dat` or velocity outputs.

## Required Preconditions
- Conversion scripts exist:
  - `scripts/convert_snapshot_hdf5_to_dat.py`
  - `scripts/convert_snapshot_hdf5_to_velocity_dat.py`
- Python dependencies for conversion are available (`yt`, `numpy`).
- Each selected source HDF5 is readable.

## Procedure
1. Resolve or place each source HDF5.
   - If the user provides an external local file or URL, place it under:
     - `INPUT/RAW/<sim>/snapshots/<snapshot>/snapshot_<snapshot>.hdf5`
   - If the file already exists under `INPUT/RAW`, keep RAW as source of truth.
   - If the file already exists under `INPUT/SELECTED`, use it directly but still identify the simulation and snapshot ids.

2. Mirror the selected file into `INPUT/SELECTED`.
   - Target folder:
     - `INPUT/SELECTED/<sim>/snapshots/<snapshot>/`
   - Preferred selected HDF5 path:
     - `INPUT/SELECTED/<sim>/snapshots/<snapshot>/snapshot_<snapshot>.hdf5`
   - If RAW exists, create or refresh a symlink from SELECTED to RAW.
   - If the user intentionally starts from a standalone SELECTED file, do not require RAW.

3. Generate RTsynth velocity file for each selected snapshot.
   - Run:
     - `python scripts/convert_snapshot_hdf5_to_velocity_dat.py <selected_snapshot_hdf5>`
   - Add `--overwrite` only when force overwrite is enabled.
   - Expected output:
     - `INPUT/SELECTED/<sim>/snapshots/<snapshot>/snapshot_<snapshot>_v.dat`

4. Convert each selected HDF5 to 3D-PDR density `.dat`.
   - Run:
     - `python scripts/convert_snapshot_hdf5_to_dat.py <selected_snapshot_hdf5>`
   - Expected output:
     - `INPUT/SELECTED/<sim>/snapshots/<snapshot>/snapshot_<snapshot>.dat`

5. Validate paired curation outputs.
   - Check selected HDF5 exists and resolves.
   - Check velocity file exists and record size.
   - Check density `.dat` exists and record size.
   - Treat density DAT and velocity DAT as an atomic pair for status reporting.

## Decision Rules
- RAW remains source of truth when available.
- SELECTED holds curated links/files plus derived outputs.
- Never overwrite a valid RAW source file without explicit user confirmation.
- Velocity generation is mandatory whenever density DAT generation is requested.
- Downstream RT post-processing must reuse the generated `snapshot_<snapshot>_v.dat`.
- If conversion values look suspicious, flag them and suggest `/preview-hydro` or adjusted bounds before `/run-pdr`.
- Continue batch processing on independent failures and report per-snapshot status.

## Completion Checklist
- Each successful target has a selected HDF5 under `INPUT/SELECTED`.
- Each successful target has a density `.dat`.
- Each successful target has a velocity `*_v.dat`.
- Final report includes exact selected HDF5, density DAT, velocity DAT, and any caveats.
