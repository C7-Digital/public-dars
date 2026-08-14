package dars

// DO NOT rename these to `_appExists` / `_depsExist`. They look like internals,
// but CUE does not evaluate hidden fields — hiding them does not tidy them, it
// switches them off, and vet then passes on a manifest that names an app or a
// dependency which does not exist. `cue cmd selftest` fails if that happens.

// ── Referential integrity ───────────────────────────────────────────────────
// The part a per-field schema cannot express: that a string names something
// that exists. CUE gets it by referencing the key, so a missing one is a
// "field not found" error carrying the offending path.

appExists: {
	for sid, s in streams {
		(sid): apps[s.app].name
	}
}

depsExist: {
	for sid, s in streams
	for _, d in [if s.depends_on != _|_ {s.depends_on}, []][0] {
		"\(sid)->\(d)": streams[d].package
	}
}
