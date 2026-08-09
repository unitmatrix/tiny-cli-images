# xh Docker and OCI container image

Minimal, non-root, multi-architecture container image for
[xh](https://github.com/ducaale/xh), a friendly and fast HTTP client. The image
packages the upstream Linux musl binary in a `scratch` runtime with CA
certificates and is published as `ghcr.io/unitmatrix/xh`.

## Usage

<!-- tiny-cli-images:version:xh:start -->

```sh
docker run --rm ghcr.io/unitmatrix/xh:0.26.2 https://example.com
```

Mount files under `/work`, which is the image's working directory:

```sh
docker run --rm \
  --volume "$PWD:/work" \
  ghcr.io/unitmatrix/xh:0.26.2 \
  GET https://example.com
```

The image runs as UID/GID `65532:65532`. It contains no shell or package
manager, and its entrypoint is `/xh`.

## Platforms

- `linux/amd64`
- `linux/arm64`

## Pinning

Each release publishes only its full upstream version tag, such as `0.26.2`.

<!-- tiny-cli-images:version:xh:end -->

The image does not publish `latest` or shortened version tags. For immutable
deployments, use the digest shown by the GitHub Release and release workflow:

```text
ghcr.io/unitmatrix/xh@sha256:<digest>
```

The upstream version and verified artifact checksums are committed in
[`image.toml`](image.toml).
