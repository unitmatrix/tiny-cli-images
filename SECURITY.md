# Security Policy

## Supported versions

Security fixes are applied to the latest published image version. Published
images remain available by version tag and immutable OCI digest, but older
versions may contain known upstream or packaging vulnerabilities.

## Reporting a vulnerability

Please report vulnerabilities privately through GitHub's security advisory
feature for this repository. Do not open a public issue for an unpatched
vulnerability.

Include the affected image and digest, reproduction details, and the expected
security impact when possible. Reports concerning xh itself may also need to be
coordinated with the [upstream xh project](https://github.com/ducaale/xh/security).

## Supply-chain concerns

Reports about mismatched upstream artifacts, checksums, signatures,
provenance, SBOMs, or registry contents are in scope. A release must never
silently substitute an unverified artifact.
