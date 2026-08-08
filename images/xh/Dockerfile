# syntax=docker/dockerfile:1

FROM alpine:3.24.1 AS fetch

ARG VERSION
ARG TARGETARCH
ARG SHA256_AMD64
ARG SHA256_ARM64

RUN apk add --no-cache \
    ca-certificates \
    curl

RUN set -eux; \
    case "${TARGETARCH}" in \
      amd64) \
        target="x86_64-unknown-linux-musl"; \
        expected="${SHA256_AMD64}" \
        ;; \
      arm64) \
        target="aarch64-unknown-linux-musl"; \
        expected="${SHA256_ARM64}" \
        ;; \
      *) \
        echo "Unsupported architecture: ${TARGETARCH}" >&2; \
        exit 1 \
        ;; \
    esac; \
    archive="xh-v${VERSION}-${target}.tar.gz"; \
    url="https://github.com/ducaale/xh/releases/download/v${VERSION}/${archive}"; \
    curl --fail --silent --show-error --location \
      "${url}" \
      --output /tmp/xh.tar.gz; \
    echo "${expected}  /tmp/xh.tar.gz" | sha256sum -c -; \
    mkdir -p /tmp/extract; \
    tar -xzf /tmp/xh.tar.gz -C /tmp/extract; \
    root="/tmp/extract/xh-v${VERSION}-${target}"; \
    mkdir -p \
      /rootfs/etc/ssl/certs \
      /rootfs/licenses/xh \
      /rootfs/tmp \
      /rootfs/work; \
    cp "${root}/xh" /rootfs/xh; \
    cp "${root}/LICENSE" /rootfs/licenses/xh/LICENSE; \
    cp /etc/ssl/certs/ca-certificates.crt \
      /rootfs/etc/ssl/certs/ca-certificates.crt; \
    chmod 0555 /rootfs/xh; \
    chmod 1777 /rootfs/tmp; \
    chown 65532:65532 /rootfs/work


FROM scratch

ARG VERSION
ARG REVISION

COPY --from=fetch /rootfs /

LABEL org.opencontainers.image.title="xh"
LABEL org.opencontainers.image.description="Minimal OCI image for xh"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.revision="${REVISION}"
LABEL org.opencontainers.image.source="https://github.com/ducaale/xh"
LABEL org.opencontainers.image.licenses="MIT"

USER 65532:65532

ENV HOME=/tmp
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

WORKDIR /work

ENTRYPOINT ["/xh"]
