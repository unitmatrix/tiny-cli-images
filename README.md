# Tiny CLI Images — Minimal Docker and OCI Images

Minimal, secure, multi-architecture Docker and OCI container images for useful
command-line tools. Images are published to GitHub Container Registry (GHCR)
for `linux/amd64` and `linux/arm64`. Release images run as non-root, include
SBOM and provenance attestations, and are signed with Sigstore.

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

## Container image catalog

| Tool | Container image | Purpose | Platforms | Runtime |
|---|---|---|---|---|
| [age](images/age/README.md) | `ghcr.io/unitmatrix/age` | File encryption | amd64, arm64 | scratch |
| [xh](images/xh/README.md) | `ghcr.io/unitmatrix/xh` | HTTP client | amd64, arm64 | scratch |

## age encryption container image

The age image packages the [age encryption tool](https://github.com/FiloSottile/age)
in a minimal, non-root container without a shell or package manager.

<!-- tiny-cli-images:version:age:start -->

```sh
docker run --rm ghcr.io/unitmatrix/age:1.3.1-r1 --version
```

<!-- tiny-cli-images:version:age:end -->

See [the age image documentation](images/age/README.md) for usage and release
details.

## xh HTTP client container image

The xh image packages the [xh HTTP client](https://github.com/ducaale/xh) in a
minimal, non-root container with CA certificates for HTTPS requests.

<!-- tiny-cli-images:version:xh:start -->

```sh
docker run --rm ghcr.io/unitmatrix/xh:0.26.2-r1 \
  https://example.com
```

<!-- tiny-cli-images:version:xh:end -->

See [the xh image documentation](images/xh/README.md) for usage and release
details.

## Development

Project decisions are documented in [docs/PROJECT.md](docs/PROJECT.md).
Contributions and security reports are covered by [CONTRIBUTING.md](CONTRIBUTING.md)
and [SECURITY.md](SECURITY.md).
