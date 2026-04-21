#!/usr/bin/env python3
import argparse
import os
import re
import shutil
from pathlib import Path


def parse_uv_label(params_path: Path) -> str:
    text = params_path.read_text()
    lines = text.splitlines()
    pdr_start = None
    for idx, line in enumerate(lines):
        if 'PDR parameters' in line:
            pdr_start = idx
            break
    if pdr_start is None:
        raise ValueError(f'Could not locate PDR parameters section in {params_path}')
    # Skip the header line after the section label and any separator lines
    for line in lines[pdr_start + 1:]:
        line = line.strip()
        if not line or line.startswith('='):
            continue
        if '!' in line:
            line = line.split('!', 1)[0].strip()
        if not line:
            continue
        match = re.search(r'[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?', line)
        if match:
            uv_value = match.group(0)
            sanitized = re.sub(r'[^A-Za-z0-9]+', 'p', uv_value)
            sanitized = sanitized.strip('p') or uv_value
            return sanitized
    raise ValueError(f'No numeric value found in PDR parameters section of {params_path}')


def main() -> None:
    parser = argparse.ArgumentParser(description='Auto-generate a 3D-PDR run folder from params.dat and copy the params file there.')
    parser.add_argument('snapshot_dir', help='Selected snapshot directory containing the HDF5 and/or run files.')
    parser.add_argument('--params-file', default=None, help='Path to the params file to copy and parse. Defaults to params_<snapshot>_local.dat inside snapshot_dir.')
    parser.add_argument('--run-id', default='run001', help='Run identifier used to build the output folder name.')
    parser.add_argument('--resolution', default='N128', help='Resolution label used to build the output folder name.')
    parser.add_argument('--output-folder', default=None, help='Explicit output folder name. If omitted, uses sims_<UV>_<resolution>_<run_id>.')
    parser.add_argument('--chemfiles-target', default=None, help='Path to 3D-PDR chemfiles directory. If omitted, auto-detect from repository root.')
    args = parser.parse_args()

    snapshot_dir = Path(args.snapshot_dir).expanduser().resolve()
    if not snapshot_dir.is_dir():
        raise SystemExit(f'Error: snapshot_dir is not a directory: {snapshot_dir}')

    params_path = Path(args.params_file) if args.params_file else None
    if params_path is None:
        params_path = snapshot_dir / f'params_{snapshot_dir.name}_local.dat'
        if not params_path.exists():
            # fallback to any params file in the snapshot folder
            matches = list(snapshot_dir.glob('params*.dat'))
            if len(matches) == 1:
                params_path = matches[0]
    elif not params_path.is_absolute():
        params_path = snapshot_dir / params_path

    if not params_path.exists():
        raise SystemExit(f'Error: params file not found: {params_path}')

    uv_label = parse_uv_label(params_path)
    resolution_label = args.resolution
    run_id = args.run_id
    output_folder_name = args.output_folder or f'sims_{uv_label}_{resolution_label}_{run_id}'
    output_dir = snapshot_dir / output_folder_name
    output_dir.mkdir(parents=True, exist_ok=True)

    destination = output_dir / params_path.name
    lines = params_path.read_text().splitlines()
    if len(lines) < 7:
        raise SystemExit(f'Error: unexpected params file format in {params_path}')

    input_name = lines[4].split('!', 1)[0].strip()
    output_name = lines[6].split('!', 1)[0].strip()
    if not input_name or not output_name:
        raise SystemExit(f'Error: could not parse I/O names from {params_path}')

    rewritten_lines = lines[:]
    rewritten_lines[3] = '..'
    rewritten_lines[4] = input_name
    rewritten_lines[5] = '.'
    rewritten_lines[6] = output_name
    destination.write_text('\n'.join(rewritten_lines) + '\n')

    chemfiles_target = None
    if args.chemfiles_target:
        chemfiles_target = Path(args.chemfiles_target).expanduser().resolve()
    else:
        for parent in snapshot_dir.parents:
            candidate = parent / '3D-PDR-dev' / 'chemfiles'
            if candidate.is_dir():
                chemfiles_target = candidate.resolve()
                break

    if chemfiles_target is not None and chemfiles_target.is_dir():
        link_path = output_dir / 'chemfiles'
        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()
        rel_target = Path(os.path.relpath(str(chemfiles_target), start=str(output_dir)))
        link_path.symlink_to(rel_target)
    elif args.chemfiles_target:
        raise SystemExit(f'Error: chemfiles target not found: {args.chemfiles_target}')

    print(output_dir)
    print(f'Copied params file to {destination}')
    if chemfiles_target is not None and chemfiles_target.is_dir():
        print(f'Linked chemfiles -> {rel_target}')
    print(f'UV label = {uv_label}')
    print(f'Output folder = {output_folder_name}')


if __name__ == '__main__':
    main()
