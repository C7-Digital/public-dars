#!/usr/bin/env python3
"""The registry's map, kept honest against its territory.

Three subcommands:

    generate   join dars.toml with the live Releases API -> the README table
    check      fail if the map and the territory disagree (CI gate)
    verify     confirm a .dar file is what its release claims it is

Design rule, and the reason this stays small: **if the Releases API can answer
it, dars.toml must not.** Versions, dates, asset names and URLs are already
authoritative there, so nothing here re-types them; a human only ever writes
what the API cannot know — which app a DAR serves, whether it is a library or an
app model, its Daml package name, and what it depends on.

Stdlib only (`tomllib` is 3.11+). Shells out to `gh` so it inherits GitHub auth
rather than handling a token itself.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tomllib
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import darmeta  # noqa: E402

REPO = "C7-Digital/public-dars"
ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "dars.toml"
README = ROOT / "README.md"

BEGIN = "<!-- BEGIN GENERATED — edit dars.toml, not this block -->"
END = "<!-- END GENERATED -->"


# ── inputs ──────────────────────────────────────────────────────────────────

def load_manifest() -> dict:
    return tomllib.loads(MANIFEST.read_text())


def releases() -> list[dict]:
    """Published releases, newest first. Drafts are not part of the registry."""
    out = subprocess.run(
        ["gh", "release", "list", "--repo", REPO, "--limit", "300",
         "--json", "tagName,name,publishedAt,isDraft"],
        capture_output=True, text=True, check=True,
    ).stdout
    return [r for r in json.loads(out) if not r["isDraft"]]


def split_tag(tag: str) -> tuple[str, str] | None:
    """`c7lock/v0.2.6` -> ('c7lock', '0.2.6'). The tag is the index."""
    if "/v" not in tag:
        return None
    stream, _, version = tag.partition("/v")
    return (stream, version) if stream and version else None


def vkey(v: str):
    """Order 0.10.0 above 0.9.0; fall back to string for anything odd."""
    try:
        return (0, tuple(int(p) for p in v.split(".")))
    except ValueError:
        return (1, v)


# ── the join ────────────────────────────────────────────────────────────────

def build_index(manifest: dict, rels: list[dict]) -> tuple[dict, list[str]]:
    """Returns (index, undeclared_tags)."""
    streams = manifest["streams"]
    published: dict[str, list[str]] = defaultdict(list)
    undeclared: list[str] = []

    for r in rels:
        parsed = split_tag(r["tagName"])
        if not parsed:
            continue  # not a stream release; ignore rather than guess
        stream, version = parsed
        (published[stream] if stream in streams else undeclared).append(
            version if stream in streams else r["tagName"])

    for versions in published.values():
        versions.sort(key=vkey, reverse=True)

    index = {"schema": 1, "repo": REPO, "streams": {}}
    for sid, s in sorted(streams.items()):
        vs = published.get(sid, [])
        latest = vs[0] if vs else None
        asset = f"{s['package']}-{latest}.dar" if latest else None
        index["streams"][sid] = {
            "app": s["app"],
            "kind": s["kind"],
            "package": s["package"],
            "depends_on": s.get("depends_on", []),
            "produced_by": s["produced_by"],
            "summary": s["summary"],
            "latest": latest,
            "versions": vs,
            "tag": f"{sid}/v{latest}" if latest else None,
            "asset": asset,
            "url": (f"https://github.com/{REPO}/releases/download/{sid}/v{latest}/{asset}"
                    if latest else None),
        }
    return index, sorted(set(undeclared))


def render(manifest: dict, index: dict) -> str:
    apps = manifest["apps"]
    lines = [BEGIN, ""]
    for kind, heading in (("app-model", "Application models"),
                          ("library", "Shared libraries")):
        rows = [(sid, e) for sid, e in index["streams"].items() if e["kind"] == kind]
        if not rows:
            continue
        lines += [f"#### {heading}", "",
                  "| Stream | Supports | Latest | Tag to pin | Daml package | Depends on | Produced by |",
                  "| ------ | -------- | ------ | ---------- | ------------ | ---------- | ----------- |"]
        for sid, e in rows:
            latest = f"`{e['latest']}`" if e["latest"] else "_unreleased_"
            tag = f"`{e['tag']}`" if e["tag"] else "—"
            deps = ", ".join(f"`{d}`" for d in e["depends_on"]) or "—"
            producer = e["produced_by"].split("/")[-1]
            lines.append(f"| `{sid}` | {apps[e['app']]['name']} | {latest} | {tag} "
                         f"| `{e['package']}` | {deps} | `{producer}` |")
        lines.append("")

    lines += ["#### What each stream is", ""]
    for sid, s in sorted(manifest["streams"].items()):
        lines += [f"**`{sid}`** — {s['summary']}", ""]
        notes = s.get("notes", "").strip()
        if notes:
            lines += [notes, ""]

    lines += ["_Generated by `tools/registry.py generate`. "
              "Versions come from the Releases API; everything else from `dars.toml`._", "", END]
    return "\n".join(lines)


def splice_readme(block: str) -> str:
    text = README.read_text()
    if BEGIN in text and END in text:
        head = text.split(BEGIN)[0]
        tail = text.split(END, 1)[1]
        return head + block + tail
    raise SystemExit(f"README.md is missing the {BEGIN!r} / {END!r} markers")


# ── subcommands ─────────────────────────────────────────────────────────────

def cmd_generate(_args) -> int:
    manifest = load_manifest()
    index, undeclared = build_index(manifest, releases())
    README.write_text(splice_readme(render(manifest, index)))
    for tag in undeclared:
        print(f"::warning::released but not declared in dars.toml: {tag}", file=sys.stderr)
    print(f"wrote README.md ({len(index['streams'])} streams)")
    return 0


def cmd_check(_args) -> int:
    """The gate. Non-zero on any disagreement between map and territory."""
    manifest = load_manifest()
    index, undeclared = build_index(manifest, releases())
    problems = 0

    for tag in undeclared:
        print(f"::error::`{tag}` is published but its stream is not declared in dars.toml. "
              f"Add it there (with a summary) before releasing.", file=sys.stderr)
        problems += 1

    for sid, e in index["streams"].items():
        if not e["latest"]:
            print(f"::notice::`{sid}` is declared but has never been released.", file=sys.stderr)
        for dep in e["depends_on"]:
            if dep not in index["streams"]:
                print(f"::error::`{sid}` declares depends_on `{dep}`, which is not a stream.",
                      file=sys.stderr)
                problems += 1
        if e["app"] not in manifest["apps"]:
            print(f"::error::`{sid}` declares app `{e['app']}`, which is not defined.",
                  file=sys.stderr)
            problems += 1

    # The generated table must already be up to date, so a stale README can
    # never be merged.
    if README.exists() and splice_readme(render(manifest, index)) != README.read_text():
        print("::error::README.md's generated block is stale — run "
              "`tools/registry.py generate`.", file=sys.stderr)
        problems += 1

    print("OK — map matches territory." if not problems else f"{problems} problem(s).")
    return 1 if problems else 0


def cmd_verify(args) -> int:
    """Confirm a .dar is what its stream/tag claims. Works offline, no dpm."""
    manifest = load_manifest()
    streams = manifest["streams"]
    if args.stream not in streams:
        print(f"::error::unknown stream `{args.stream}`", file=sys.stderr)
        return 1

    meta = darmeta.read(args.dar)
    expected_pkg = streams[args.stream]["package"]
    problems = []

    if meta["package"] != expected_pkg:
        problems.append(f"package is `{meta['package']}`, expected `{expected_pkg}`")
    if args.version and meta["version"] != args.version:
        problems.append(f"version is `{meta['version']}`, expected `{args.version}`")

    print(json.dumps({**meta, "stream": args.stream}, indent=2))
    for p in problems:
        print(f"::error::{args.dar}: {p}", file=sys.stderr)
    return 1 if problems else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("generate", help="regenerate the README stream table")
    sub.add_parser("check", help="fail if map and territory disagree")
    v = sub.add_parser("verify", help="confirm a .dar matches its stream")
    v.add_argument("stream")
    v.add_argument("dar")
    v.add_argument("--version", help="also assert the DAR's internal version")

    args = ap.parse_args()
    return {"generate": cmd_generate, "check": cmd_check, "verify": cmd_verify}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
