---
name: run-3dpdr-snapshot
description: 'Run 3D-PDR for one or more STARFORGE selected snapshots. Use when you need to create a snapshot-local output folder named sims_<UV>_<resolution>_<run_id>, prepare local params, and execute 3DPDR with outputs written in that folder.'
argument-hint: 'Provide snapshot path(s) or id(s), and optionally UV label, resolution label, run_id, and force mode.'
user-invocable: true
disable-model-invocation: false
---

# Run 3D-PDR Snapshot

## When To Use
- User wants to run 3D-PDR for one or more selected STARFORGE snapshots.
- User wants outputs isolated under `sims_<UV>_<resolution>_<run_id>` inside each snapshot folder.
- User wants a repeatable path from HDF5 to DAT to 3DPDR outputs.

## Inputs To Collect
- Snapshot targets:
  - One or more selected snapshot folders, or
  - Snapshot ids with simulation folder.
- Optional run settings:
  - Run id (`run_id`, default `run001`)
  - UV label (`UV`, default `Draine`)
  - Resolution label (`resolution`, default `N128`)
  - Output folder name (default `sims_<UV>_<resolution>_<run_id>`)
  - Output prefix (default: `snapshot_<id>_run`)
  - Regridding bounds for DAT conversion (`left-edge`, `right-edge`, default left=`25 25 25`, right=`75 75 75`)
  - Grid size `N` for DAT conversion (default 128)
  - Rerun mode (`force`, default off)

## Procedure
1. Resolve each snapshot folder in SELECTED.
   - Expected path:
     - `STARFORGE/SELECTED/<sim>/snapshots/<snapshot>/`
   - Required input file:
     - `snapshot_<snapshot>.hdf5` symlink or file.

2. Create local output folder and runtime links.
   - Compute output folder name:
     - `run_dir = sims_<UV>_<resolution>_<run_id>`
   - Use helper script:
     - `./scripts/auto_generate_run_dir.py <snapshot_folder> --run-id <run_id> --resolution <resolution>`
     - This reads UV from `params*.dat`, creates the named run folder, and copies the params file into it.
   - Create:
     - `STARFORGE/SELECTED/<sim>/snapshots/<snapshot>/<run_dir>/`
   - Ensure chemfiles are available in run folder:
     - create or refresh `<run_dir>/chemfiles` symlink to `3D-PDR-dev/chemfiles`

3. Generate DAT in the snapshot folder.
   - Run converter on the selected snapshot HDF5.
   - Write output DAT to:
     - `STARFORGE/SELECTED/<sim>/snapshots/<snapshot>/snapshot_<snapshot>.dat`
   - If DAT already exists and `force` is off, keep existing DAT and continue.
   - If `force` is on, overwrite DAT.
   - Validate DAT is non-empty and has physically reasonable max number density.

4. Create a short-path local params file inside `<run_dir>`.
   - Create or copy:
     - `STARFORGE/SELECTED/<sim>/snapshots/<snapshot>/<run_dir>/params_<snapshot>_local.dat`
   - The helper script should copy the source params file into the run folder.
   - Use local relative paths to avoid Fortran fixed-length truncation:
     - `indir = ..`
     - `input = snapshot_<snapshot>.dat`
     - `outdir = .`
     - `output = <prefix>`

5. Run 3DPDR from `<run_dir>`.
   - Command pattern:
     - `cd <snapshot>/<run_dir> && <repo>/3D-PDR-dev/3DPDR -p=params_<snapshot>_local.dat`
   - If expected output files already exist and `force` is off, skip execution and report skipped.
   - If `force` is on, rerun and overwrite outputs with the same prefix.
   - Use sync for short runs, async for long runs.

6. Validate outputs and summarize.
   - Check expected output files in `<run_dir>`, including at least:
     - `<prefix>.UV.fin`
     - `<prefix>.rayDir.fin`
     - `<prefix>.rayAV.fin`
   - If run continues into chemistry, confirm progress line appears.

## Decision Rules
- Default output folder is `sims_<UV>_<resolution>_<run_id>` with defaults `UV=Draine`, `resolution=N128`, `run_id=run001`.
- Default conversion bounds are left=`25 25 25` and right=`75 75 75` unless user overrides.
- Default rerun behavior is skip-if-exists; only rerun when `force` is explicitly enabled.
- If the DAT conversion reports near-zero densities, regenerate with bounds inside dataset domain before running 3DPDR.
- If 3DPDR fails with CVODE NaN step size errors, treat as invalid DAT/region first, then rerun after conversion fix.
- If path strings are long, always run from snapshot-local `<run_dir>` using short relative params values.
- For batch runs, continue other snapshots after a single snapshot failure and report per-snapshot status.

## Completion Checklist
- Snapshot-local `<run_dir>` folder exists for each target snapshot.
- `<run_dir>/params_<snapshot>_local.dat` exists and uses short relative paths.
- 3DPDR run launched from `<run_dir>` for each target snapshot.
- Output artifacts are written to `<run_dir>` and verified.
- Final report includes run command, output paths, and any caveats.
