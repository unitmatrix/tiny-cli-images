#!/usr/bin/env bash

set -euo pipefail

IMAGE="${1:?image required}"

echo "Testing ${IMAGE}"

test "$(docker image inspect --format '{{.Config.User}}' "${IMAGE}")" = "65532:65532"
test "$(docker image inspect --format '{{.Config.WorkingDir}}' "${IMAGE}")" = "/work"
test "$(docker image inspect --format '{{json .Config.Entrypoint}}' "${IMAGE}")" = '["/age"]'

docker image inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "${IMAGE}" \
  | grep -Fxq 'HOME=/tmp'
docker image inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "${IMAGE}" \
  | grep -Fxq 'PATH=/'

docker run --rm "${IMAGE}" --version
docker run --rm "${IMAGE}" --help >/dev/null
docker run --rm --entrypoint /age-keygen "${IMAGE}" --version
docker run --rm --entrypoint /age-inspect "${IMAGE}" --version

temporary="$(mktemp -d)"
container=""

cleanup() {
  if [[ -n "${container}" ]]; then
    docker rm --force "${container}" >/dev/null 2>&1 || true
  fi
  rm -rf "${temporary}"
}

trap cleanup EXIT

docker run --rm --entrypoint /age-keygen "${IMAGE}" \
  >"${temporary}/key.txt"
recipient="$(sed -n 's/^# public key: //p' "${temporary}/key.txt")"
test -n "${recipient}"

printf '%s' 'tiny age round trip' \
  | docker run --rm --interactive \
      "${IMAGE}" \
      --encrypt \
      --recipient "${recipient}" \
  >"${temporary}/encrypted.age"

chmod 0755 "${temporary}"
chmod 0644 "${temporary}/key.txt" "${temporary}/encrypted.age"

output="$(
  docker run --rm --interactive \
    --volume "${temporary}:/work:ro" \
    "${IMAGE}" \
    --decrypt \
    --identity /work/key.txt \
    /work/encrypted.age
)"

test "${output}" = "tiny age round trip"

container="$(docker create "${IMAGE}")"
docker export --output "${temporary}/rootfs.tar" "${container}"
contents="$(tar -tf "${temporary}/rootfs.tar" | sed -e 's#^\./##' -e 's#/$##')"

for expected in \
  age \
  age-inspect \
  age-keygen \
  age-plugin-batchpass \
  licenses/age/LICENSE \
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
