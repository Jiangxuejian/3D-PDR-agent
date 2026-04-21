#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
  cat <<EOF
Usage: $0 <remote-host> <remote-base-path> <source-folder> [<source-folder> ...]

Example:
  $0 shuguang /public/home/zncszzp/Thomas/xjiang/3D-PDR-agent STARFORGE/SELECTED scripts 3D-PDR-dev
EOF
  exit 1
fi

remote_host=$1
remote_base_path=$2
shift 2
sources=("$@")

EXCLUDES=(
  --exclude='.git/'
  --exclude='*.swp'
  --exclude='*.tmp'
  --exclude='*~'
  --exclude='__pycache__/'
  --exclude='.DS_Store'
)

# Detect a common absolute local root if all sources share one.
local_root=""
if [[ "${#sources[@]}" -gt 0 ]]; then
  first_src="${sources[0]}"
  if [[ "$first_src" = /* ]]; then
    local_root="$first_src"
    for src in "${sources[@]}"; do
      if [[ "$src" != /* ]]; then
        local_root=""
        break
      fi
      while [[ "$src" != "$local_root" && "${src#$local_root}" == "$src" ]]; do
        local_root="${local_root%/*}"
      done
    done
  fi
  if [[ -n "$local_root" && "$local_root" = /* ]]; then
    local_root="${local_root%/}"
  else
    local_root=""
  fi
fi

ssh "$remote_host" "mkdir -p '$remote_base_path'"

for src in "${sources[@]}"; do
  if [[ ! -e "$src" ]]; then
    echo "Source path does not exist: $src" >&2
    exit 2
  fi

  if [[ "$src" = /* ]]; then
    if [[ -n "$local_root" && "$src" == "$local_root" ]]; then
      if [[ -d "$src" ]]; then
        src_path="${src%/}/"
        dest="$remote_base_path/"
        ssh "$remote_host" "mkdir -p '$dest'"
        echo "Syncing $src_path -> $remote_host:$dest"
        rsync -avz --compress-level=1 --progress --chmod=Du=rwx,Dgo=rx,Fu=rw,Fgo=r "${EXCLUDES[@]}" "$src_path" "$remote_host":"$dest"
        continue
      fi
      dest="$remote_base_path/"
    elif [[ -n "$local_root" && "$src" == "$local_root"* ]]; then
      rel_path="${src#$local_root/}"
      if [[ -d "$src" ]]; then
        src_path="${src%/}/"
        dest="$remote_base_path/$rel_path/"
        ssh "$remote_host" "mkdir -p '$dest'"
        echo "Syncing $src_path -> $remote_host:$dest"
        rsync -avz --compress-level=1 --progress --chmod=Du=rwx,Dgo=rx,Fu=rw,Fgo=r "${EXCLUDES[@]}" "$src_path" "$remote_host":"$dest"
        continue
      fi
      dest="$remote_base_path/$(dirname "$rel_path")/"
    else
      base_name=$(basename "$src")
      if [[ -d "$src" ]]; then
        src_path="${src%/}/"
        dest="$remote_base_path/$base_name/"
        ssh "$remote_host" "mkdir -p '$dest'"
        echo "Syncing $src_path -> $remote_host:$dest"
        rsync -avz --compress-level=1 --progress --chmod=Du=rwx,Dgo=rx,Fu=rw,Fgo=r "${EXCLUDES[@]}" "$src_path" "$remote_host":"$dest"
        continue
      fi
      dest="$remote_base_path/$base_name"
    fi
  else
    dest="$remote_base_path/"
  fi

  echo "Syncing $src -> $remote_host:$dest"
  if [[ "$src" = /* ]]; then
    rsync -avz --compress-level=1 --progress --chmod=Du=rwx,Dgo=rx,Fu=rw,Fgo=r "${EXCLUDES[@]}" "$src" "$remote_host":"$dest"
  else
    rsync -avz --compress-level=1 --progress --chmod=Du=rwx,Dgo=rx,Fu=rw,Fgo=r --relative "${EXCLUDES[@]}" "$src" "$remote_host":"$dest"
  fi
 done

echo "Sync complete."
