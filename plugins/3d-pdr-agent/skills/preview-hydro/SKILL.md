---
name: preview-hydro
description: "Inspect INPUT/RAW hydrodynamical snapshots before curation. Use when users want density diagnostics, quick-look plots, or a sanity check before choosing snapshots for 3D-PDR."
argument-hint: "Optionally provide RAW root, simulation folder, snapshot id, output directory, limit, and force mode."
user-invocable: true
disable-model-invocation: false
---

# Preview Hydro

## When To Use
- User wants to inspect raw hydrodynamical simulation snapshots before selecting them.
- User wants density slices, regridded central-box diagnostics, histograms, or density percentiles.
- User is deciding which snapshots are scientifically reasonable to curate for 3D-PDR.
- User asks for a preview/check/diagnostic pass over files under `INPUT/RAW`.

## Inputs To Collect
- RAW location:
  - Default: `INPUT/RAW`
  - Optional specific simulation folder or HDF5 file.
- Optional output location:
  - Default: next to each input HDF5 file.
  - Alternative: a diagnostics folder such as `Products/HydroPreview/`.
- Optional controls:
  - `--limit <N>` for quick test runs.
  - `--force` to regenerate existing diagnostics.

## Procedure
1. Locate candidate hydro snapshot files.
   - Default search root:
     - `INPUT/RAW`
   - Accepted file suffixes:
     - `.hdf5`
     - `.h5`

2. Run the preview diagnostic script.
   - Example quick check:
     - `python scripts/starforge_raw_density_plots.py --raw-root INPUT/RAW --limit 1`
   - Example with a dedicated output folder:
     - `python scripts/starforge_raw_density_plots.py --raw-root INPUT/RAW --output-root Products/HydroPreview --limit 3`
   - Example forced regeneration:
     - `python scripts/starforge_raw_density_plots.py --raw-root INPUT/RAW --output-root Products/HydroPreview --force`

3. Inspect produced diagnostics.
   - Per snapshot, expected outputs include:
     - `*_slice_plot.png`
     - `*_regridded_density_grid_slice.png`
     - `*_density_histogram.png`
     - `*_density_percentiles.txt`

4. Recommend next curation step.
   - If a snapshot looks physically reasonable, hand it to `/curate-hydro`.
   - If densities look near-zero, saturated, or malformed, report the warning and suggest checking units, fields, or region bounds before curation.

## Decision Rules
- This skill is diagnostic only; it should not modify `INPUT/SELECTED`.
- Do not generate 3D-PDR `.dat` or RTsynth velocity files here; that belongs to `/curate-hydro`.
- If the user already knows which HDF5 file to use, skip preview and start the minimal workflow at `/curate-hydro`.
- Use `--limit 1` for first-pass environment checks.

## Completion Checklist
- Candidate HDF5 files were found or a clear no-files warning was reported.
- Diagnostic plots and percentile files were generated or skipped idempotently.
- The final report lists sample output paths and any warnings.
- The next recommended action is either `/curate-hydro` or a data/units/bounds check.
