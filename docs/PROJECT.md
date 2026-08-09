# Tiny Images — Project Context

## Goal

Tiny Images publishes small, secure OCI images for useful command-line tools
that do not already have a strong official or established community image.

The supported tools are `age` and `xh`. Do not add another tool without an
explicit project decision. Common tools whose OCI distribution is already well
covered, including jq, yq, crane, oras, cosign, kubectl, Helm, and Git, are
intentionally out of scope.

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
│   ├── age/
│   │   ├── image.toml
│   │   ├── Dockerfile
│   │   ├── README.md
│   │   └── test.sh
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

## age image

Upstream is [FiloSottile/age](https://github.com/FiloSottile/age). The image
consumes the upstream static Linux release archives for `amd64` and `arm64`.
It includes the `age`, `age-keygen`, `age-inspect`, and
`age-plugin-batchpass` binaries shipped in those archives, with `/age` as the
entrypoint. The final image uses `scratch` and runs as UID/GID `65532:65532`.

## Metadata and updates

`scripts/meta.py` reads `images/<tool>/image.toml` and exposes the name,
description, version, upstream repository, license, platform targets, and
checksums to GitHub Actions. Release builds publish this metadata as OCI labels
and as manifest and image-index annotations so multi-architecture GHCR package
pages display the image description and link back to this repository.

`scripts/update.py <tool> <version>` queries the GitHub Releases API, rejects
missing, draft, or prerelease releases, requires both expected platform
artifacts and valid SHA-256 digests, and updates the relevant values in
`images/<tool>/image.toml`. When the version changes, it also rewrites semantic
versions inside invisible `tiny-cli-images:version:<tool>` Markdown comment
blocks. Both current upstreams name release archives as
`<tool>-v<version>-<target>.tar.gz`, so no more general asset-template system is
needed yet.

## Continuous integration

Pull requests that affect images, scripts, or workflows build and exercise each
affected image on both `linux/amd64` and `linux/arm64`, using QEMU where
necessary. Image-local changes build only that image; changes to shared scripts
or workflows build every supported image. Builds verify upstream checksums and
run deterministic smoke tests without pushing images. A stable `CI result` job
summarizes the dynamically selected image jobs for branch protection.

Smoke tests cover at least `<tool> --version` and `<tool> --help`, plus
deterministic image-specific behavior. Network integration tests should remain
separate where practical.

## Releases

Images are released independently from tags in this form:

```text
<tool>/v<upstream-version>[-r<packaging-revision>]
```

Normal upstream releases use the exact upstream version in both the release tag
and image tag. A packaging revision is an exceptional recovery mechanism used
only when GitHub has permanently reserved the original tag after deletion of an
immutable release. In that case, an explicitly numbered suffix is appended,
for example `<tool>/v<upstream-version>-r1`. It does not change the upstream
binary version or verified checksums.

The Release workflow can also be dispatched manually with an existing release
tag. It builds the tagged source for traceability while reading package-page
metadata and documentation from the current catalog, then recreates the image,
attestations, signature, and GitHub Release without moving the tag. This is the
recovery path for a deliberately deleted GHCR package or mutable GitHub
Release. A deleted immutable GitHub Release cannot reuse its tag; publish the
next packaging revision instead.

A push to `main` whose commit subject matches `Update <tool> to <version>`,
optionally followed by GitHub's squash-merge suffix ` (#<pull-request>)`,
creates the corresponding release tag. For example:

<!-- tiny-cli-images:version:age:start -->

`Update age to 1.3.1` creates `age/v1.3.1`.

<!-- tiny-cli-images:version:age:end -->

Other commit subjects do not create a tag. The Tag workflow can also be
dispatched manually from the default branch with an explicit tag override;
both automatic and manual tags must match an existing image and its committed
manifest version. Packaging revision tags are created only through this manual
override for immutable-release recovery. Existing tags are never moved.

<!-- tiny-cli-images:version:xh:start -->

For example, `xh/v0.26.2-r1` publishes:

```text
ghcr.io/<owner>/xh:0.26.2-r1
```

<!-- tiny-cli-images:version:xh:end -->

A packaging revision such as `<tool>/v<upstream-version>-r1` instead publishes
`ghcr.io/<owner>/<tool>:<upstream-version>-r1`. Floating tags such as `latest`
and shortened version tags such as `0.26` are not published. Users can also pin
the image by its immutable OCI digest.

The release workflow must:

1. Parse the tool, upstream version, and optional packaging revision from the
   tag.
2. Verify that the upstream version equals the committed manifest version.
3. Build and publish `linux/amd64` and `linux/arm64` as one OCI image.
4. Publish SBOM and build provenance attestations.
5. Sign the resulting digest using keyless OIDC signing.
6. Expose the immutable OCI digest.
7. Create or update a GitHub Release with the image reference, digest,
   supported platforms, upstream release link, and supply-chain details.

Release workflows use minimal GitHub Actions permissions. Third-party actions
should ultimately be pinned to full commit SHAs.

## Upstream detection

The scheduled upstream workflow detects new stable releases for every supported
image but never publishes them directly. The intended flow is:

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
