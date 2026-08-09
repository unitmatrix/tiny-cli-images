#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import tempfile
import tomllib
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURES = ("amd64", "arm64")
IMAGE_RE = re.compile(r"[a-z0-9][a-z0-9-]*")
VERSION_RE = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
SHA256_RE = re.compile(r"sha256:([0-9a-f]{64})")
UPSTREAM_RE = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
TARGET_RE = re.compile(r"[A-Za-z0-9_.-]+")
SECTION_RE = re.compile(r"^\s*\[([^]]+)]\s*(?:#.*)?(?:\r?\n)?$")
ASSIGNMENT_RE = re.compile(
    r'^(\s*)([A-Za-z0-9_]+)(\s*=\s*)"([^"\r\n]*)"([^\r\n]*)(\r?\n)?$'
)


class UpdateError(Exception):
    """An expected release or manifest invariant was not satisfied."""


def read_manifest(path: Path, image: str) -> dict[str, Any]:
    try:
        with path.open("rb") as manifest_file:
            config = tomllib.load(manifest_file)
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise UpdateError(f"cannot read {path}: {error}") from error

    if config.get("name") != image:
        raise UpdateError(f"{path} does not describe the {image} image")

    version = config.get("version")
    if not isinstance(version, str) or VERSION_RE.fullmatch(version) is None:
        raise UpdateError(f"invalid current version in {path}")

    upstream = config.get("upstream")
    if not isinstance(upstream, str) or not UPSTREAM_RE.fullmatch(upstream):
        raise UpdateError(f"invalid upstream repository in {path}")

    if config.get("architectures") != list(ARCHITECTURES):
        raise UpdateError(
            f"{path} must declare exactly these architectures: "
            + ", ".join(ARCHITECTURES)
        )

    platforms = config.get("platform")
    if not isinstance(platforms, dict):
        raise UpdateError(f"platform table is missing or malformed in {path}")

    for architecture in ARCHITECTURES:
        platform = platforms.get(architecture)
        target = platform.get("target") if isinstance(platform, dict) else None
        if not isinstance(target, str) or TARGET_RE.fullmatch(target) is None:
            raise UpdateError(f"missing target for platform.{architecture} in {path}")

    return config


def fetch_release(upstream: str, version: str) -> dict[str, Any]:
    url = f"https://api.github.com/repos/{upstream}/releases/tags/v{version}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "tiny-cli-images-update",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise UpdateError(f"release v{version} does not exist in {upstream}") from error
        raise UpdateError(
            f"GitHub API request failed with HTTP {error.code}: {error.reason}"
        ) from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise UpdateError(f"GitHub API request failed: {error}") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise UpdateError("GitHub API returned invalid JSON") from error

    if not isinstance(payload, dict):
        raise UpdateError("GitHub API returned an unexpected release document")

    return payload


def release_digests(
    release: dict[str, Any], config: dict[str, Any], version: str
) -> dict[str, str]:
    if release.get("tag_name") != f"v{version}":
        raise UpdateError("release tag does not match the requested version")
    if release.get("draft") is not False:
        raise UpdateError(f"release v{version} is a draft or has no draft status")
    if release.get("prerelease") is not False:
        raise UpdateError(f"release v{version} is a prerelease or has no prerelease status")

    assets = release.get("assets")
    if not isinstance(assets, list):
        raise UpdateError("release assets are missing or malformed")
    if not all(isinstance(asset, dict) for asset in assets):
        raise UpdateError("release assets contain an unexpected value")

    upstream = config["upstream"]
    image = config["name"]
    digests: dict[str, str] = {}

    for architecture in ARCHITECTURES:
        target = config["platform"][architecture]["target"]
        asset_name = f"{image}-v{version}-{target}.tar.gz"
        matches = [asset for asset in assets if asset.get("name") == asset_name]

        if len(matches) != 1:
            raise UpdateError(
                f"expected exactly one release asset named {asset_name}; found {len(matches)}"
            )

        asset = matches[0]
        if asset.get("state") != "uploaded":
            raise UpdateError(f"release asset {asset_name} is not in the uploaded state")

        expected_url = (
            f"https://github.com/{upstream}/releases/download/v{version}/{asset_name}"
        )
        if asset.get("browser_download_url") != expected_url:
            raise UpdateError(f"release asset {asset_name} has an unexpected download URL")

        digest = asset.get("digest")
        if not isinstance(digest, str):
            raise UpdateError(f"release asset {asset_name} has no SHA-256 digest")

        match = SHA256_RE.fullmatch(digest)
        if match is None:
            raise UpdateError(f"release asset {asset_name} has an invalid SHA-256 digest")

        digests[architecture] = match.group(1)

    return digests


def render_manifest(path: Path, version: str, digests: dict[str, str]) -> str:
    try:
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    except OSError as error:
        raise UpdateError(f"cannot read {path}: {error}") from error

    replacements = {
        (None, "version"): version,
        ("platform.amd64", "sha256"): digests["amd64"],
        ("platform.arm64", "sha256"): digests["arm64"],
    }
    replaced = {key: 0 for key in replacements}
    section: str | None = None
    output: list[str] = []

    for line in lines:
        section_match = SECTION_RE.fullmatch(line)
        if section_match:
            section = section_match.group(1)
            output.append(line)
            continue

        assignment_match = ASSIGNMENT_RE.fullmatch(line)
        if assignment_match:
            key = (section, assignment_match.group(2))
            if key in replacements:
                replaced[key] += 1
                line = (
                    f"{assignment_match.group(1)}{assignment_match.group(2)}"
                    f'{assignment_match.group(3)}"{replacements[key]}"'
                    f"{assignment_match.group(5)}{assignment_match.group(6) or ''}"
                )

        output.append(line)

    invalid = [
        f"{field_section or 'root'}.{key}"
        for (field_section, key), count in replaced.items()
        if count != 1
    ]
    if invalid:
        raise UpdateError(
            "manifest fields were missing or duplicated: " + ", ".join(invalid)
        )

    return "".join(output)


def documentation_paths(image: str) -> list[Path]:
    paths = {
        ROOT / "README.md",
        ROOT / "CONTRIBUTING.md",
        *(ROOT / "docs").rglob("*.md"),
        *(ROOT / "images" / image).rglob("*.md"),
    }
    return sorted(paths)


def render_documentation(image: str, version: str) -> dict[Path, str]:
    image_readme = ROOT / "images" / image / "README.md"
    start_marker = f"<!-- tiny-cli-images:version:{image}:start -->"
    end_marker = f"<!-- tiny-cli-images:version:{image}:end -->"
    version_pattern = re.compile(
        r"(?<![0-9.])[0-9]+\.[0-9]+\.[0-9]+(?:-r[1-9][0-9]*)?(?![0-9.])"
    )
    updates: dict[Path, str] = {}
    marked_paths: set[Path] = set()

    for path in documentation_paths(image):
        try:
            current = path.read_text(encoding="utf-8")
        except OSError as error:
            raise UpdateError(f"cannot read {path}: {error}") from error

        if current.count(start_marker) != current.count(end_marker):
            raise UpdateError(f"unbalanced {image} version markers in {path}")

        position = 0
        output: list[str] = []
        blocks = 0

        while True:
            start = current.find(start_marker, position)
            if start == -1:
                output.append(current[position:])
                break

            content_start = start + len(start_marker)
            end = current.find(end_marker, content_start)
            nested_start = current.find(start_marker, content_start, end)

            if end == -1 or nested_start != -1:
                raise UpdateError(f"malformed {image} version markers in {path}")

            content = current[content_start:end]
            rendered_content, replacements = version_pattern.subn(version, content)
            if replacements == 0:
                raise UpdateError(
                    f"version marker for {image} contains no version in {path}"
                )

            output.extend(
                (
                    current[position:content_start],
                    rendered_content,
                    end_marker,
                )
            )
            position = end + len(end_marker)
            blocks += 1

        if blocks == 0:
            continue

        marked_paths.add(path)
        rendered = "".join(output)
        if rendered != current:
            updates[path] = rendered

    if image_readme not in marked_paths:
        raise UpdateError(
            f"{image_readme} contains no version marker for {image}"
        )

    return updates


def write_atomic(path: Path, content: str) -> None:
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent, prefix=f".{path.name}.", text=True
        )
    except OSError as error:
        raise UpdateError(f"cannot prepare an update for {path}: {error}") from error
    temporary_path = Path(temporary_name)

    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary_path, mode)
        os.replace(temporary_path, path)
    except OSError as error:
        temporary_path.unlink(missing_ok=True)
        raise UpdateError(f"cannot update {path}: {error}") from error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update a pinned CLI image from a stable upstream release."
    )
    parser.add_argument("image", help="image name")
    parser.add_argument("version", help="stable upstream version, without a v prefix")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if IMAGE_RE.fullmatch(args.image) is None:
        raise UpdateError(f"invalid image name: {args.image}")
    if VERSION_RE.fullmatch(args.version) is None:
        raise UpdateError("version must use the form X.Y.Z without a v prefix")

    manifest_path = ROOT / "images" / args.image / "image.toml"
    config = read_manifest(manifest_path, args.image)
    release = fetch_release(config["upstream"], args.version)
    digests = release_digests(release, config, args.version)
    updated = render_manifest(manifest_path, args.version, digests)
    current = manifest_path.read_text(encoding="utf-8")
    documentation: dict[Path, str] = {}

    if config["version"] != args.version:
        documentation = render_documentation(args.image, args.version)

    if updated == current and not documentation:
        print(f"{args.image} {args.version} is already pinned")
        return 0

    if updated != current:
        write_atomic(manifest_path, updated)
        print(f"updated {manifest_path.relative_to(ROOT)} to {args.version}")
    for path, content in documentation.items():
        write_atomic(path, content)
        print(f"updated {path.relative_to(ROOT)} to {args.version}")
    for architecture in ARCHITECTURES:
        print(f"{architecture}: {digests[architecture]}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except UpdateError as error:
        raise SystemExit(f"error: {error}") from error
