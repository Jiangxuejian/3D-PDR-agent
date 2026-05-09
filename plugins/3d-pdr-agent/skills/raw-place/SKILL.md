---
name: raw-place
description: 'Follow INPUT RAW directory structure for incoming data. Use when user provides a file path or download link and wants data placed in the correct RAW snapshot location, then optionally linked into SELECTED.'
argument-hint: 'Provide file/link plus target simulation and snapshot id.'
user-invocable: true
disable-model-invocation: false
---

# RAW Folder Data Placement

## When To Use
- User provides a INPUT snapshot file path and wants it organized correctly.
- User provides a download link and wants the file put in the right project location.
- User wants RAW to remain source-of-truth with optional SELECTED symlink.

## Inputs To Collect
- Input source type:
  - Local file path
  - URL/download link
- Simulation folder name (example: `M2e4_R10_Z1_S0_A2_B0.1_I1_Res271_n2_sol0.5_2`)
- Snapshot id (example: `810`)
- Expected filename (example: `snapshot_810.hdf5`)
- Optional: whether to create/update SELECTED symlink after placement.

## Procedure
1. Resolve and validate the target RAW path.
   - Target pattern:
     - `INPUT/RAW/<sim>/snapshots/<snapshot>/snapshot_<snapshot>.hdf5`
   - Ensure parent directories exist.

2. Place the source file into RAW.
   - If source is local file: copy/move into the RAW target path.
   - If source is URL: download directly to the RAW target path.
   - Validate file exists and has non-zero size.

3. Optionally mirror structure in SELECTED and link the snapshot.
   - Create:
     - `INPUT/SELECTED/<sim>/snapshots/<snapshot>/`
   - Create/update symlink:
     - `INPUT/SELECTED/<sim>/snapshots/<snapshot>/snapshot_<snapshot>.hdf5`
     - target = corresponding RAW file.

4. Report final paths and placement status.

## Decision Rules
- If both RAW and SELECTED contain conflicting files, keep RAW as source of truth and refresh SELECTED symlink.
- If user gives only snapshot id without simulation folder, search RAW for unique `snapshot_<id>.hdf5` match.
  - If multiple matches, ask user which simulation folder to use.
- Never overwrite a valid RAW source file without explicit user confirmation.

## Completion Checklist
- RAW path created and populated correctly.
- Incoming file/link placed in correct RAW snapshot location.
- SELECTED symlink created and valid when requested.
- Final report includes exact target paths and caveats.
