# AGENTS.md

## Project

This repository publishes minimal OCI images for command-line tools.

## Principles

- Prefer upstream release artifacts over rebuilding upstream source.
- Verify upstream artifacts before packaging.
- Use minimal runtimes; prefer `scratch` for suitable static binaries.
- Run containers as non-root.
- Support linux/amd64 and linux/arm64 where available.
- Do not include shells or package managers unless required.
- Publish SBOMs, provenance, and signed release images.
- Never silently use unverified upstream artifacts.

## Repository structure

Image-specific files belong in:

    images/<tool>/

Shared automation belongs in:

    scripts/
    .github/workflows/

Do not prematurely generalize Dockerfiles.

## Development

Before making changes:

1. Inspect the existing implementation.
2. Preserve established architecture unless there is a concrete reason to change it.
3. Run relevant tests.
4. Keep changes scoped to the requested image/tool.
