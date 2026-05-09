
# 3D-PDR Agent Workspace

This repository provides a modular, agent-compatible workflow for running 3D-PDR and RT-synth simulations, with robust skill/plugin support for Claude Code, Codex, GitHub Copilot, and similar AI agents.

## Features
- Modular skills for document/data processing (see `skills-repo/`)
- Automated workflows for 3D-PDR and RT-synth
- Compatible with Claude Code, Codex Plugin, and other agent platforms
- Lightweight project metadata and helper scripts

## Directory Structure

- `INPUT/` — Simulation input data (formerly STARFORGE)
- `skills-repo/` — Modular skills for agent/plugin use
	- `skills/` — Skill definitions (e.g., pdf, docx)
	- `.agents/skills/` — Codex Plugin skill links
	- `.claude/skills/` — Claude Code skill links
	- `tests/` — Skill validation scripts
- `3D-PDR/` — Link or clone to your local 3D-PDR codebase
- `RTsynth/` — Link or clone to your local RT-synth codebase

## Prerequisites

1. An AI agent platform (Claude Code, Codex, GitHub Copilot, Hermes Agent, OpenClaw, etc.)
2. 3D-PDR and RT-synth codebases (see below)

### Setting Up 3D-PDR and RT-synth

**Option 1: Link to local installations**

Place symlinks to your local 3D-PDR and RT-synth codebases in `./3D-PDR` and `./RTsynth`.

**Option 2: Download codebases**

- [3D-PDR](https://github.com/itamos-ism/3D-PDR) → `./3D-PDR`
- [RT-synth](https://github.com/itamos-ism/RT-synth) → `./RTsynth`

## Installation & Usage

**For Claude Code:**

> Install the 3D-PDR and RTsynth skills from this repository. Ensure the agent has access to the `./3D-PDR` and `./RTsynth` directories for script execution.

**For Codex Plugin:**

> Install the skills from this repository and ensure access to the `./3D-PDR` and `./RTsynth` directories for script execution.

## Contributing

Contributions are welcome! Please see `skills-repo/CHANGELOG.md` for recent updates and `skills-repo/README.md` for skill/plugin authoring guidelines.

---
For more details, see the documentation in each skill directory and the main workflow files.