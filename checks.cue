package dars

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
