# Contributing

Thank you for helping improve Tiny Images.

## Before making a change

Read [AGENTS.md](AGENTS.md) and [docs/PROJECT.md](docs/PROJECT.md). Keep
image-specific behavior under `images/<tool>/` and reusable orchestration under
`scripts/` or `.github/workflows/`.

Do not add another CLI image without prior discussion. The project deliberately
avoids tools that already have a strong official or community image.

## Updating an image

Use the update script with a stable upstream release version:

<!-- tiny-cli-images:version:age:start -->

```sh
python3 scripts/update.py age 1.3.2
```

<!-- tiny-cli-images:version:age:end -->

<!-- tiny-cli-images:version:xh:start -->

```sh
python3 scripts/update.py xh 0.26.2
```

<!-- tiny-cli-images:version:xh:end -->

Review the resulting manifest and documentation diffs. The updater changes the
version and digests in `images/<tool>/image.toml`, then refreshes Markdown
blocks identified by invisible `tiny-cli-images:version` comments. Never use
placeholder or unverified checksums.

## Validation

Before submitting a pull request:

1. Run `python3 scripts/meta.py <tool>`.
2. Build both `linux/amd64` and `linux/arm64` images.
3. Run `images/<tool>/test.sh <local-image>` for each architecture.
4. Confirm that no unrelated files or generated artifacts are included.

Pull requests must not publish images. Production publication occurs only from
an approved `<tool>/v<version>` release tag.
