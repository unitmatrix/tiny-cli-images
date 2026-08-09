# age Docker and OCI container image

Minimal, non-root, multi-architecture container image for
[age](https://github.com/FiloSottile/age), a simple, modern, and secure file
encryption tool. The image packages the upstream static Linux binaries in a
`scratch` runtime and is published as `ghcr.io/unitmatrix/age`.

## Usage

Encrypt a file for a recipient:

<!-- tiny-cli-images:version:age:start -->

```sh
docker run --rm --interactive \
  ghcr.io/unitmatrix/age:1.3.1 \
  --encrypt \
  --recipient age1... \
  < document.txt \
  > document.txt.age
```

Decrypt with an identity mounted under `/work`:

```sh
docker run --rm --interactive \
  --volume "$PWD:/work:ro" \
  ghcr.io/unitmatrix/age:1.3.1 \
  --decrypt \
  --identity /work/key.txt \
  < document.txt.age
```

The image runs as UID/GID `65532:65532`. Its entrypoint is `/age`; the
upstream `age-keygen`, `age-inspect`, and `age-plugin-batchpass` companion
binaries are also available at the filesystem root. For example:

```sh
docker run --rm \
  --entrypoint /age-keygen \
  ghcr.io/unitmatrix/age:1.3.1
```

## Platforms

- `linux/amd64`
- `linux/arm64`

## Pinning

Each release publishes only its full upstream version tag, such as `1.3.1`.

<!-- tiny-cli-images:version:age:end -->

The image does not publish `latest` or shortened version tags. For immutable
deployments, use the digest shown by the GitHub Release and release workflow:

```text
ghcr.io/unitmatrix/age@sha256:<digest>
```

The upstream version and verified artifact checksums are committed in
[`image.toml`](image.toml).
