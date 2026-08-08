# Contributing

Thank you for helping improve Tiny Images.

## Before making a change

Read [AGENTS.md](AGENTS.md) and [docs/PROJECT.md](docs/PROJECT.md). Keep
image-specific behavior under `images/<tool>/` and reusable orchestration under
`scripts/` or `.github/workflows/`.

Do not add another CLI image without prior discussion. The project deliberately
avoids tools that already have a strong official or community image.

## Updating xh

Use the update script with a stable upstream release version:

```sh
python3 scripts/update.py xh 0.26.2
```

Review the resulting `images/xh/image.toml` diff. Never use placeholder or
unverified checksums.

## Validation

Before submitting a pull request:

1. Run `python3 scripts/meta.py xh`.
2. Build both `linux/amd64` and `linux/arm64` images.
3. Run `images/xh/test.sh <local-image>` for each architecture.
4. Confirm that no unrelated files or generated artifacts are included.

Pull requests must not publish images. Production publication occurs only from
an approved `<tool>/v<version>` release tag.
