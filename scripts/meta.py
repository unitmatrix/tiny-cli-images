#!/usr/bin/env python3

from __future__ import annotations

import os
import re
import sys
import tomllib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
IMAGE_RE = re.compile(r"[a-z0-9][a-z0-9-]*")
VERSION_RE = re.compile(r"([0-9]+)\.([0-9]+)\.([0-9]+)")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
ARCHITECTURES = ("amd64", "arm64")


def fail(message: str) -> None:
    raise SystemExit(f"error: {message}")


def load_config(image: str) -> dict[str, Any]:
    if IMAGE_RE.fullmatch(image) is None:
        fail(f"invalid image name: {image}")

    path = ROOT / "images" / image / "image.toml"
    try:
        with path.open("rb") as config_file:
            config = tomllib.load(config_file)
    except FileNotFoundError:
        fail(f"unknown image: {image}")
    except (OSError, tomllib.TOMLDecodeError) as error:
        fail(f"cannot read {path.relative_to(ROOT)}: {error}")

    if config.get("name") != image:
        fail(f"manifest name does not match image directory: {image}")

    return config


def metadata(config: dict[str, Any]) -> dict[str, str]:
    description = config.get("description")
    if not isinstance(description, str) or not description or "\n" in description:
        fail("manifest description must be a non-empty single-line string")

    version = config.get("version")
    if not isinstance(version, str):
        fail("manifest version must be a string")

    version_match = VERSION_RE.fullmatch(version)
    if version_match is None:
        fail(f"manifest version is not X.Y.Z: {version}")

    upstream = config.get("upstream")
    if not isinstance(upstream, str) or upstream.count("/") != 1:
        fail("manifest upstream must use the form owner/repository")

    if config.get("architectures") != list(ARCHITECTURES):
        fail("manifest must declare amd64 and arm64 in that order")

    license_name = config.get("license")
    if not isinstance(license_name, str) or not license_name or "\n" in license_name:
        fail("manifest license must be a non-empty single-line string")

    values = {
        "name": config["name"],
        "description": description,
        "version": version,
        "upstream": upstream,
        "license": license_name,
    }

    platforms = config.get("platform")
    if not isinstance(platforms, dict):
        fail("manifest platform table is missing")

    for architecture in ARCHITECTURES:
        platform = platforms.get(architecture)
        if not isinstance(platform, dict):
            fail(f"manifest platform.{architecture} table is missing")

        target = platform.get("target")
        checksum = platform.get("sha256")
        if not isinstance(target, str) or not target:
            fail(f"manifest platform.{architecture}.target is invalid")
        if not isinstance(checksum, str) or SHA256_RE.fullmatch(checksum) is None:
            fail(f"manifest platform.{architecture}.sha256 is invalid")

        values[f"target_{architecture}"] = target
        values[f"sha_{architecture}"] = checksum

    return values


def write_values(values: dict[str, str]) -> None:
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as output_file:
            for key, value in values.items():
                print(f"{key}={value}", file=output_file)
    else:
        for key, value in values.items():
            print(f"{key}={value}")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: meta.py <image>")

    write_values(metadata(load_config(sys.argv[1])))


if __name__ == "__main__":
    main()
