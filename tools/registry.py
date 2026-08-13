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

# ── the schema, stated rather than implied ──────────────────────────────────
# TOML has no schema of its own, so dars.toml's shape would otherwise live only
# in whatever this file happens to subscript. Declared here so it is readable in
# one place and enforced in one place; `validate_manifest` is the only thing
# that gets to decide a manifest is well-formed, and both `generate` and `check`
# go through it.

KINDS = ("app-model", "library")  # every kind must have a table in `render`

APP_FIELDS = {
    "required": {"name": str, "description": str},
    "optional": {"repo": str},
}

STREAM_FIELDS = {
    "required": {"app": str, "kind": str, "package": str,
                 "produced_by": str, "summary": str},
    "optional": {"depends_on": list, "notes": str},
}


def _check_table(where: str, table: dict, spec: dict, problems: list[str]) -> None:
    """Required keys present, no unknown keys, right types. Unknown keys are an
    error rather than a shrug: a typo'd `pakcage` would otherwise be silently
    dropped and then explode as a KeyError somewhere unhelpful."""
    allowed = {**spec["required"], **spec["optional"]}
    for key, ty in spec["required"].items():
        if key not in table:
            problems.append(f"{where}: missing required key `{key}`")
    for key, value in table.items():
        if key not in allowed:
            problems.append(f"{where}: unknown key `{key}`")
        elif not isinstance(value, allowed[key]):
            problems.append(f"{where}: `{key}` should be "
                            f"{allowed[key].__name__}, got {type(value).__name__}")


def validate_manifest(manifest: dict) -> list[str]:
    """Everything wrong with this manifest, as human sentences."""
    problems: list[str] = []

    for key in ("schema", "apps", "streams"):
        if key not in manifest:
            problems.append(f"dars.toml: missing top-level `{key}`")
    if problems:
        return problems
    if manifest["schema"] != 1:
        problems.append(f"dars.toml: unsupported schema {manifest['schema']!r}; this tool reads 1")

    for aid, app in manifest["apps"].items():
        _check_table(f"apps.{aid}", app, APP_FIELDS, problems)

    for sid, s in manifest["streams"].items():
        where = f"streams.{sid}"
        _check_table(where, s, STREAM_FIELDS, problems)
        if s.get("kind") not in KINDS:
            # The one that silently loses a stream: `render` only emits a table
            # per known kind, so an unrecognised kind drops the row while every
            # other check stays green.
            problems.append(f"{where}: kind `{s.get('kind')}` is not one of {list(KINDS)}")
        if s.get("app") not in manifest["apps"]:
            problems.append(f"{where}: app `{s.get('app')}` is not defined under [apps.*]")
        for dep in s.get("depends_on", []):
            if not isinstance(dep, str):
                problems.append(f"{where}: depends_on entries must be strings")
            elif dep not in manifest["streams"]:
                problems.append(f"{where}: depends_on `{dep}` is not a stream")
            elif dep == sid:
                problems.append(f"{where}: depends_on itself")
    return problems


# ── inputs ──────────────────────────────────────────────────────────────────

def load_manifest() -> dict:
    """Parse and validate. Nothing downstream may see an unvalidated manifest —
    that is what keeps the schema from being 'whatever the code subscripts'."""
    manifest = tomllib.loads(MANIFEST.read_text())
    problems = validate_manifest(manifest)
    if problems:
        for p in problems:
            print(f"::error::{p}", file=sys.stderr)
        raise SystemExit(f"dars.toml is invalid ({len(problems)} problem(s))")
    return manifest


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
    tabled = 0
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
            tabled += 1
        lines.append("")

    # Every stream must reach exactly one table. Validation already rejects an
    # unknown `kind`, so this cannot fire today — it is here for the next person
    # who adds a third kind to KINDS and forgets to give it a heading above,
    # which would otherwise drop those streams from the table while every other
    # check stayed green.
    if tabled != len(index["streams"]):
        missing = sorted(set(index["streams"]) - {
            sid for sid, e in index["streams"].items() if e["kind"] in KINDS})
        raise SystemExit(
            f"render covered {tabled} of {len(index['streams'])} streams; "
            f"no table for: {', '.join(missing) or '(unknown)'}")

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

    # dars.toml's own shape (required keys, unknown keys, types, `kind`, `app`,
    # `depends_on`) was already enforced by load_manifest -> validate_manifest,
    # which exits before we get here. What is left is the part that needs the
    # live API: does the map match the territory.
    for sid, e in index["streams"].items():
        if not e["latest"]:
            print(f"::notice::`{sid}` is declared but has never been released.", file=sys.stderr)

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
