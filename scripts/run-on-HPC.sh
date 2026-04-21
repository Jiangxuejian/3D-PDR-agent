#!/bin/bash
#SBATCH -J 3DPDR-JXJ
#SBATCH --nodes=1
#SBATCH --mem=0
#SBATCH --exclusive
#SBATCH -p normal
#SBATCH -t 960:00:00
#SBATCH -o out.%j
#SBATCH -e err.%j

ulimit -s unlimited
module load compiler/gcc/11.4.0
export I_MPI_PMI_LIBRARY=/opt/gridview/slurm/lib/libpmi.so
export OMP_NUM_THREADS=56

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Defaults can be overridden via sbatch --export=ALL,RUN_DIR=...,PARAMS_FILE=...,BINARY=...
RUN_DIR="${RUN_DIR:-$PWD}"
PARAMS_FILE="${PARAMS_FILE:-}"
BINARY="${BINARY:-$PROJECT_ROOT/3D-PDR-dev/3DPDR}"

if [[ -z "$PARAMS_FILE" ]]; then
	if compgen -G "$RUN_DIR/params*_local.dat" > /dev/null; then
		PARAMS_FILE="$(basename "$(ls -1 "$RUN_DIR"/params*_local.dat | head -n 1)")"
	elif compgen -G "$RUN_DIR/params*.dat" > /dev/null; then
		PARAMS_FILE="$(basename "$(ls -1 "$RUN_DIR"/params*.dat | head -n 1)")"
	else
		echo "[ERROR] No params file found in $RUN_DIR" >&2
		exit 2
	fi
fi

if [[ ! -x "$BINARY" ]]; then
	echo "[ERROR] 3DPDR binary not executable: $BINARY" >&2
	exit 3
fi

if [[ ! -d "$RUN_DIR" ]]; then
	echo "[ERROR] RUN_DIR does not exist: $RUN_DIR" >&2
	exit 4
fi

cd "$RUN_DIR"
echo "[INFO] RUN_DIR=$RUN_DIR"
echo "[INFO] PARAMS_FILE=$PARAMS_FILE"
echo "[INFO] BINARY=$BINARY"

time srun -n 1 "$BINARY" -p="$PARAMS_FILE"