# Tiny Images — Project Context

## Goal

Tiny Images publishes small, secure OCI images for useful command-line tools
that do not already have a strong official or established community image.

The first supported tool is `xh`. Do not add another tool without an explicit
project decision. Common tools whose OCI distribution is already well covered,
including jq, yq, crane, oras, cosign, kubectl, Helm, and Git, are intentionally
out of scope.

## Repository model

This is a GitHub monorepo. Each CLI has its own independently published GHCR
package while CI, signing, SBOM generation, update automation, and security
policy are shared.

Image-specific behavior belongs under `images/<tool>/`. Reusable orchestration
belongs under `scripts/` and `.github/workflows/`.

Do not create a universal Dockerfile prematurely. Release infrastructure should
be generic before image Dockerfiles are generalized. Shared Dockerfile
abstractions should only be extracted after multiple images demonstrate real
duplication.

## Repository structure

```text
.
├── AGENTS.md
├── README.md
├── LICENSE
├── SECURITY.md
├── CONTRIBUTING.md
├── docs/
│   └── PROJECT.md
├── images/
│   └── xh/
│       ├── image.toml
│       ├── Dockerfile
│       ├── README.md
│       └── test.sh
├── scripts/
│   ├── meta.py
│   └── update.py
└── .github/
    ├── dependabot.yml
    └── workflows/
        ├── ci.yml
        ├── release.yml
        └── upstream.yml
```

## xh image

Upstream is [ducaale/xh](https://github.com/ducaale/xh). The image consumes
upstream static Linux musl release artifacts instead of compiling xh.

Supported platforms and upstream targets are:

| OCI architecture | Upstream target |
|---|---|
| `amd64` | `x86_64-unknown-linux-musl` |
| `arm64` | `aarch64-unknown-linux-musl` |

`images/xh/image.toml` pins the upstream version and SHA-256 digest for each
artifact. Release builds must use exactly those values. Checksums must be real
verified digests, never placeholders.

The xh Dockerfile uses a temporary fetch stage and verifies the archive before
extracting it. The final image uses `scratch` and contains approximately:

```text
/
├── xh
├── etc/ssl/certs/ca-certificates.crt
├── licenses/xh/LICENSE
├── tmp/
└── work/
```

Runtime configuration is:

```text
USER 65532:65532
HOME=/tmp
SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
WORKDIR=/work
ENTRYPOINT=["/xh"]
```

No shell or package manager belongs in the final image.

## Metadata and updates

`scripts/meta.py` reads `images/<tool>/image.toml` and exposes the name,
version, upstream repository, platform targets, and checksums to GitHub
Actions.

`scripts/update.py xh <version>` queries the GitHub Releases API, rejects
missing, draft, or prerelease releases, requires both expected musl artifacts
and valid SHA-256 digests, and updates only the relevant values in
`images/xh/image.toml`.

The initial updater may contain xh-specific release knowledge. A complex asset
template system is intentionally deferred until more images reveal common
requirements.

## Continuous integration

Pull requests that affect images, scripts, or workflows build and exercise both
`linux/amd64` and `linux/arm64`, using QEMU where necessary. Builds verify
upstream checksums and run deterministic smoke tests without pushing images.

Smoke tests cover at least `xh --version` and `xh --help`. Network integration
tests should remain separate where practical.

## Releases

Images are released independently from tags in this form:

```text
<tool>/v<version>
```

For example, `xh/v0.26.2` publishes:

```text
ghcr.io/<owner>/xh:0.26.2
```

Only the full upstream version tag is published. Floating tags such as
`latest` and shortened version tags such as `0.26` are not published. Users can
also pin the image by its immutable OCI digest.

The release workflow must:

1. Parse the tool and version from the tag.
2. Verify that the tag version equals the committed manifest version.
3. Build and publish `linux/amd64` and `linux/arm64` as one OCI image.
4. Publish SBOM and build provenance attestations.
5. Sign the resulting digest using keyless OIDC signing.
6. Expose the immutable OCI digest.

Release workflows use minimal GitHub Actions permissions. Third-party actions
should ultimately be pinned to full commit SHAs.

## Upstream detection

The scheduled upstream workflow detects new stable xh releases but never
publishes them directly. The intended flow is:

```text
upstream release
      ↓
detection and update issue or PR
      ↓
metadata update
      ↓
CI verification and review
      ↓
release tag
      ↓
OCI publication
```

## Supply-chain rules

- Never build a dynamically resolved `latest` upstream release during
  publication.
- Never weaken verification to make an update pass.
- Never silently substitute another artifact.
- Versioned images must remain traceable to an exact upstream release.
- Publish SBOMs, provenance, and signatures for released images.
- Prefer OIDC/keyless signing over long-lived signing secrets.

The catalog is the product. Simplicity and supply-chain trust take priority over
maximal abstraction.
