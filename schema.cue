// The shape of dars.cue, plus the rules a per-field schema cannot express.
//
// Kept out of dars.cue so `cue cmd selftest` can vet a fixture against it —
// see testdata/.
package dars

#Repo: =~"^[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9._-]+$"

#App: {
	name:        string & !=""
	description: string & !=""
	repo?:       #Repo
}

#Stream: {
	app:  string & !=""     // must be a key of `apps` — see appExists below
	kind: "app-model" | "library" // each kind needs a table in registry_tool.cue
	// The Daml package NAME: the SCU resolution key on-ledger, not the filename.
	package:     =~"^[a-z][a-z0-9-]*[a-z0-9]$"
	produced_by: #Repo
	summary:     string & !=""

	// Defaulted, not optional, so readers can just iterate/compare instead of
	// repeating a conditional at every use site.
	depends_on: [...string] | *[]
	notes:      string | *""
}

schema: 1
apps: [string]:    #App
streams: [string]: #Stream

// ── Referential integrity ───────────────────────────────────────────────────
// That a string names something that exists. CUE reports a missing key as
// "field not found", carrying the offending path.
//
// DO NOT rename these to `_appExists` / `_depsExist`. They look like internals,
// but CUE does not evaluate hidden fields — hiding them does not tidy them, it
// switches them off, and vet then passes on a manifest naming an app or a
// dependency that does not exist. `cue cmd selftest` fails if that happens.

appExists: {
	for sid, s in streams {(sid): apps[s.app].name}
}

depsExist: {
	for sid, s in streams for _, d in s.depends_on {"\(sid)->\(d)": streams[d].package}
}
