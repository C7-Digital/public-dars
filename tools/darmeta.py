#!/usr/bin/env python3
"""Read a DAR's true identity from its own bytes. Stdlib only, no dpm.

A DAR is a ZIP carrying a JAR-style META-INF/MANIFEST.MF:

    Name: c7lock-model-0.2.6
    Sdk-Version: 3.4.11
    Main-Dalf: c7lock-model-0.2.6-<64 hex>/c7lock-model-0.2.6-<64 hex>.dalf

so package name, version, SDK version and the main package id are all
recoverable without dpm on PATH. The package id matters because SCU resolves on
(name, version) while the ledger addresses packages by id — two DARs can share a
name and version and still be different bytes.
"""
import hashlib
import re
import zipfile

MAIN_DALF_ID = re.compile(r"-([0-9a-f]{64})\.dalf$")


def unfold(manifest: str) -> dict[str, str]:
    """JAR manifests wrap at 72 columns; a continuation starts with one space."""
    out, key = {}, None
    for raw in manifest.splitlines():
        if not raw.strip():
            continue
        if raw.startswith(" ") and key:
            out[key] += raw[1:]
        elif ":" in raw:
            key, _, val = raw.partition(":")
            key = key.strip()
            out[key] = val.strip()
    return out


def read(path: str) -> dict:
    with zipfile.ZipFile(path) as z:
        mf = unfold(z.read("META-INF/MANIFEST.MF").decode("utf-8", "replace"))

    name_version = mf.get("Name", "")
    # `Name` is `<package>-<version>`; version is the last dash-delimited field
    # that starts with a digit, since package names contain dashes too.
    pkg, version = name_version, ""
    if "-" in name_version:
        head, _, tail = name_version.rpartition("-")
        if tail and tail[0].isdigit():
            pkg, version = head, tail

    m = MAIN_DALF_ID.search(mf.get("Main-Dalf", ""))

    with open(path, "rb") as fh:
        sha = hashlib.sha256(fh.read()).hexdigest()

    return {
        "package": pkg,
        "version": version,
        "sdk_version": mf.get("Sdk-Version", ""),
        "main_package_id": m.group(1) if m else "",
        "sha256": sha,
    }


if __name__ == "__main__":
    import json
    import sys
    print(json.dumps(read(sys.argv[1]), indent=2))
