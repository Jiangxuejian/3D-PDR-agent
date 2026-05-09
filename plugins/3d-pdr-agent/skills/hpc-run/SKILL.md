---
name: hpc-run
description: 'Sync INPUT/SELECTED, scripts, and 3D-PDR-dev to an HPC host, preserve folder structure under a target remote path, and submit the HPC run script.'
argument-hint: 'Provide the HPC host, remote target path, and optionally the source folders to sync.'
user-invocable: true
disable-model-invocation: false
---

# HPC Sync and Run

## When To Use
- You want to push local INPUT/SELECTED, `scripts`, and `3D-PDR-dev` to an HPC environment.
- You want to preserve the local folder structure on the remote host.
- You want to run 3D-PDR with input/output organized in a snapshot-local run folder.
- You want to submit the existing HPC job script `scripts/run-on-HPC.sh` after syncing.

## Inputs To Collect
- Remote host alias or address (example: `shuguang`).
- Remote target base path (example: `/public/home/zncszzp/Thomas/xjiang/3D-PDR-agent`).
- Source folders to sync:
  - `INPUT/SELECTED`
  - `scripts`
  - `3D-PDR-dev`
- Snapshot run inputs:
   - Snapshot folder under SELECTED (example: `INPUT/SELECTED/<sim>/snapshots/810`)
   - Params file to use (example: `params_810_local.dat`)
   - Run folder name (example: `sims_<UV>_<resolution>_<run_id>`)
- Optional sync settings:
  - `--dry-run` to preview the transfer.
  - `--delete` to mirror source deletions remotely.

## Procedure
1. Confirm the local source folders exist:
   - `INPUT/SELECTED`
   - `scripts`
   - `3D-PDR-dev`
2. Ensure the remote base path exists:
   - `ssh <host> mkdir -p <remote-path>`
3. Run the helper script bundled with this skill:
   - `<this-skill>/scripts/sync_to_hpc.sh <host> <remote-path> INPUT/SELECTED scripts 3D-PDR-dev`
   - This preserves the local directory structure under the remote base path.
4. Organize snapshot-local run directory on HPC.
   - Build run folder inside the snapshot folder:
     - `<remote-path>/INPUT/SELECTED/<sim>/snapshots/<snapshot>/<run_dir>/`
   - Ensure run folder contains:
     - copied params file (for example `params_<snapshot>_local.dat`)
     - `chemfiles` symlink pointing to `<remote-path>/3D-PDR-dev/chemfiles`
5. Submit the remote run script from the snapshot run folder:
   - `ssh <host> "sbatch --chdir <snapshot-run-dir> --export=ALL,RUN_DIR=<snapshot-run-dir>,PARAMS_FILE=<params-file>,BINARY=<remote-path>/3D-PDR-dev/3DPDR <remote-path>/scripts/run-on-HPC.sh"`
6. Verify the submission output and remote job ID.

## Decision Rules
- Prefer `--dry-run` when first syncing to confirm behavior.
- Preserve remote folder structure exactly as the local source directories.
- If the remote path already contains old files, use `--delete` only when you want a mirror.
- Keep run I/O snapshot-local in `<run_dir>` to isolate outputs per run.
- Submit with `--chdir <snapshot-run-dir>` and export `RUN_DIR`, `PARAMS_FILE`, and `BINARY`.

## Completion Checklist
- Remote base path exists on the HPC host.
- `INPUT/SELECTED`, `scripts`, and `3D-PDR-dev` are synced to the remote path.
- `scripts/run-on-HPC.sh` is present on the remote host.
- Snapshot-local `<run_dir>` exists and contains the intended params file.
- The remote job is submitted with `sbatch`.
- The job submission returns a valid SLURM job ID.
