#!/usr/bin/env bash

set -euo pipefail

IMAGE="${1:?image required}"

echo "Testing ${IMAGE}"

test "$(docker image inspect --format '{{.Config.User}}' "${IMAGE}")" = "65532:65532"
test "$(docker image inspect --format '{{.Config.WorkingDir}}' "${IMAGE}")" = "/work"
test "$(docker image inspect --format '{{json .Config.Entrypoint}}' "${IMAGE}")" = '["/xh"]'

docker image inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "${IMAGE}" \
  | grep -Fxq 'HOME=/tmp'
docker image inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "${IMAGE}" \
  | grep -Fxq 'SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt'

docker run --rm "${IMAGE}" --version
docker run --rm "${IMAGE}" --help >/dev/null

output="$(
  docker run --rm \
    "${IMAGE}" \
    --offline \
    GET https://example.com
)"

grep -q "GET" <<<"${output}"

container="$(docker create "${IMAGE}")"
archive="$(mktemp)"

cleanup() {
  docker rm --force "${container}" >/dev/null 2>&1 || true
  rm -f "${archive}"
}

trap cleanup EXIT

docker export --output "${archive}" "${container}"
contents="$(tar -tf "${archive}" | sed -e 's#^\./##' -e 's#/$##')"

for expected in \
  xh \
  etc/ssl/certs/ca-certificates.crt \
  licenses/xh/LICENSE \
  tmp \
  work
do
  grep -Fxq "${expected}" <<<"${contents}"
done

if grep -Eq '(^|/)bin/(ba|da|a|z)?sh$' <<<"${contents}"; then
  echo "unexpected shell found in image" >&2
  exit 1
fi

echo "OK"
