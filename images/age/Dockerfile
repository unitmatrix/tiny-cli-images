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
        target="linux-amd64"; \
        expected="${SHA256_AMD64}" \
        ;; \
      arm64) \
        target="linux-arm64"; \
        expected="${SHA256_ARM64}" \
        ;; \
      *) \
        echo "Unsupported architecture: ${TARGETARCH}" >&2; \
        exit 1 \
        ;; \
    esac; \
    archive="age-v${VERSION}-${target}.tar.gz"; \
    url="https://github.com/FiloSottile/age/releases/download/v${VERSION}/${archive}"; \
    curl --fail --silent --show-error --location \
      "${url}" \
      --output /tmp/age.tar.gz; \
    echo "${expected}  /tmp/age.tar.gz" | sha256sum -c -; \
    mkdir -p /tmp/extract; \
    tar -xzf /tmp/age.tar.gz -C /tmp/extract; \
    root="/tmp/extract/age"; \
    mkdir -p \
      /rootfs/licenses/age \
      /rootfs/tmp \
      /rootfs/work; \
    for binary in age age-inspect age-keygen age-plugin-batchpass; do \
      cp "${root}/${binary}" "/rootfs/${binary}"; \
      chmod 0555 "/rootfs/${binary}"; \
    done; \
    cp "${root}/LICENSE" /rootfs/licenses/age/LICENSE; \
    chmod 1777 /rootfs/tmp; \
    chown 65532:65532 /rootfs/work


FROM scratch

ARG VERSION
ARG REVISION

COPY --from=fetch /rootfs /

LABEL org.opencontainers.image.title="age"
LABEL org.opencontainers.image.description="Minimal OCI image for age"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.revision="${REVISION}"
LABEL org.opencontainers.image.source="https://github.com/FiloSottile/age"
LABEL org.opencontainers.image.licenses="BSD-3-Clause"

USER 65532:65532

ENV HOME=/tmp
ENV PATH=/

WORKDIR /work

ENTRYPOINT ["/age"]
