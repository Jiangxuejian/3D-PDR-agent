---
name: rt-vis
description: "Convert RTsynth post-processed output files (column density _cds.dat and integrated-intensity _CO10.dat) to PNG images. Use when: visualising RTsynth products, making images from RT outputs, plotting column density maps, plotting CO line maps, converting all RT .dat files to images, batch image generation from Products/RTsynth."
argument-hint: "Optionally specify: target directory, file pattern (cds or CO10), coolant/line tag, mask threshold, overwrite flag."
user-invocable: true
disable-model-invocation: false
---

# RT-vis

Convert RTsynth post-processed `.dat` output files to publication-quality PNG images.
Outputs are written next to their source files (same directory, same stem, `.png` extension).

## When To Use
- You have RTsynth outputs (e.g., `RT_*_cds.dat`, `RT_*_CO10.dat`) either in a sims folder or under `Products/RTsynth/`.
- You want PNG images for all angles/directions in a batch.
- You want to inspect column density or integrated-intensity maps visually.

## Inputs To Collect
Before running, confirm:
- **Target directory** — folder containing the `.dat` files, or the root to search recursively.
  - Default when running after `/rt-prod`: `Products/RTsynth/<sim>/snapshots/<snapshot>/<sims_*>/`
- **File type** — column density (`_cds.dat`) or integrated intensity (`_CO10.dat`); drives pattern + threshold defaults.
- **Overwrite** — whether to regenerate existing `.png` files (default: skip).

## Default Parameters By File Type

| Type | `--pattern` | `--col` | `--threshold` | `--vmax-factor` |
|------|-------------|---------|---------------|-----------------|
| Column density (H₂) | `RT_snapshot_*_cds.dat` | `2` | `1e13` | `1e10` |
| Integrated intensity (CO 1-0) | `RT_snapshot_*_CO10.dat` | `2` | `1e-6` | `1e6` |

Adjust `--threshold` and `--vmax-factor` if the images look washed out or mostly black.

## Procedure

### 1. Locate target directory
Resolve the directory containing `.dat` files.
- If invoked after `/rt-prod`, use the Products destination path reported in that skill's completion summary.
- If invoked directly, ask the user or infer from workspace structure.
- For recursive batch over all snapshots/sims, use `--recursive` with the Products root.

### 2. Run the visualisation script

**Column density maps:**
```bash
conda run -n pdfchem python /home/xjiang/data/3D-PDR-agent/.github/skills/rt-vis/scripts/rt_vis.py \
  --dir <target_dir> \
  --pattern "RT_snapshot_*_cds.dat" \
  --col 2 --name NH2 --threshold 1e13 --vmax-factor 1e10
```

**Integrated-intensity maps (CO 1-0):**
```bash
conda run -n pdfchem python /home/xjiang/data/3D-PDR-agent/.github/skills/rt-vis/scripts/rt_vis.py \
  --dir <target_dir> \
  --pattern "RT_snapshot_*_CO10.dat" \
  --col 2 --name ICO --threshold 1e-6 --vmax-factor 1e6
```

**Batch over all runs under Products/RTsynth (recursive):**
```bash
conda run -n pdfchem python /home/xjiang/data/3D-PDR-agent/.github/skills/rt-vis/scripts/rt_vis.py \
  --dir Products/RTsynth \
  --pattern "RT_snapshot_*_cds.dat" \
  --recursive
```

Add `--overwrite` to regenerate existing images.  
Add `--dry-run` to list matched files without writing anything.

### 3. Validate outputs
After the script finishes, confirm:
- The script printed `[OK]` for all expected files (not `[SKIP]` or `[ERROR]`).
- At least one `.png` file exists next to the source `.dat` files.
- Sample a few images (edge-on vs. face-on angles) to check they are not all black (threshold too high) or all saturated (threshold too low).

### 4. Report completion
Report:
- Total rendered / skipped / errors.
- Sample image paths for the user to inspect.
- Suggested threshold tuning if any image looks pathological.

## Tuning Guide
| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Image mostly black | Threshold too high | Lower `--threshold` by 1–2 dex |
| Image fully saturated | `vmax` too low | Increase `--vmax-factor` |
| Few isolated bright pixels | Threshold correct, diffuse emission masked | Acceptable; lower threshold only if science requires it |

## Script Reference
[scripts/rt_vis.py](./scripts/rt_vis.py) — full CLI visualisation script (wraps `image.py` logic; adds argparse, recursive search, overwrite guard, dry-run).

## Dependencies
Required Python packages: `pandas`, `numpy`, `matplotlib`.

Known working environments in this workspace:
- `pdfchem` conda env — confirmed working (`conda run -n pdfchem python ...`)
- `mercury` conda env — confirmed working
- `starforge` env — missing `pandas`; install with `conda install -n starforge pandas` if preferred

Replace `python` in the commands above with `conda run -n pdfchem python` if the base environment lacks these packages.
