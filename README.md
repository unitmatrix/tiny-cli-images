# Tiny Images

Minimal OCI images for useful command-line tools.

## Principles

- One primary CLI per image
- Minimal runtime
- Non-root by default
- Multi-architecture
- Upstream artifacts verified by SHA-256
- SBOM included
- Build provenance included
- Keyless Sigstore signatures
- Immutable version tags
- No unnecessary shell or package manager

## Images

| Image | amd64 | arm64 | Runtime |
|---|---|---|---|
| age | ✓ | ✓ | scratch |
| xh | ✓ | ✓ | scratch |

## age

<!-- tiny-cli-images:version:age:start -->

```sh
docker run --rm ghcr.io/unitmatrix/age:1.3.0 --version
```

<!-- tiny-cli-images:version:age:end -->

See [the age image documentation](images/age/README.md) for usage and release
details.

## xh

<!-- tiny-cli-images:version:xh:start -->

```sh
docker run --rm ghcr.io/unitmatrix/xh:0.26.2 \
  https://example.com
```

<!-- tiny-cli-images:version:xh:end -->

See [the xh image documentation](images/xh/README.md) for usage and release
details.

## Development

Project decisions are documented in [docs/PROJECT.md](docs/PROJECT.md).
Contributions and security reports are covered by [CONTRIBUTING.md](CONTRIBUTING.md)
and [SECURITY.md](SECURITY.md).
