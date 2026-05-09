
# 3D-PDR Agent Workspace

This repository provides a modular, agent-compatible workflow for running 3D-PDR and RT-synth simulations, with reusable skills and a repo-local Codex plugin.

![3D-PDR Agent workflow](docs/assets/workflow.svg)

## Features
- Canonical workflow skills in `plugins/3d-pdr-agent/skills/`
- Automated workflows for 3D-PDR and RT-synth
- Repo-local Codex plugin in `plugins/3d-pdr-agent/`
- Lightweight project metadata and helper scripts

## Directory Structure

- `INPUT/` — Simulation input data (formerly STARFORGE)
- `plugins/3d-pdr-agent/` — Codex plugin packaging and canonical workflow skills
- `3D-PDR-dev/` — Link or clone to your local 3D-PDR runtime codebase
- `RT-synth/` — Link or clone to your local RT-synth codebase

## Prerequisites

1. An AI agent platform (Claude Code, Codex, GitHub Copilot, Hermes Agent, OpenClaw, etc.)
2. 3D-PDR and RT-synth codebases (see below)

### Setting Up 3D-PDR and RT-synth

**Option 1: Link to local installations**

Place symlinks to your local 3D-PDR and RT-synth codebases in `./3D-PDR-dev` and `./RT-synth`.

**Option 2: Download codebases**

- [3D-PDR](https://github.com/itamos-ism/3D-PDR) → `./3D-PDR-dev`
- [RT-synth](https://github.com/itamos-ism/RT-synth) → `./RT-synth`

## Installation & Usage

Just ask your AI agent to handle the installation.

**For Claude Code:**

> Install the 3D-PDR and RT-synth skills from this repository. Ensure the agent has access to the `./3D-PDR-dev` and `./RT-synth` directories for script execution.

**For Codex Plugin:**

> Use the repo-local plugin in `plugins/3d-pdr-agent/`, registered by `.agents/plugins/marketplace.json`. Ensure Codex has access to `./3D-PDR-dev` and `./RT-synth` for script execution.


## Skill Workflow

The hydro workflow can begin with an optional preview step:

`preview-hydro -> curate-hydro -> run-pdr -> run-rtsynth -> render-rt`

If the user already knows the input HDF5 file under `INPUT/`, the minimal workflow starts at curation:

`curate-hydro -> run-pdr -> run-rtsynth`

- `preview-hydro` inspects raw hydro snapshots with diagnostics such as `scripts/starforge_raw_density_plots.py`.
- `curate-hydro` merges raw placement, SELECTED curation, density DAT conversion, and RTsynth velocity DAT generation.
- `run-pdr` creates the 3D-PDR-ready run folder and executes 3DPDR.
- `run-rtsynth` generates synthetic observables from completed 3D-PDR outputs.
- `render-rt` converts RTsynth products into PNG diagnostics.

## Contributing

Contributions are welcome. Update `plugins/3d-pdr-agent/skills/` as the canonical skill source.

---
For more details, see the documentation in each skill directory and the main workflow files.
