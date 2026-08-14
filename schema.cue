// The shape of dars.cue, stated once and enforced by `cue vet`.
//
// Definitions (#Foo) are closed: an unknown field is an error with no extra
// work, which is one of the two hand-rolled halves of the Python validator.
package dars

#Repo: =~"^[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9._-]+$"

#App: {
	name:        string & !=""
	description: string & !=""
	repo?:       #Repo
}

#Stream: {
	// Which product this DAR serves. Must be a key of `apps` — enforced below.
	app: string & !=""

	// Every kind needs a matching table in registry.py's `render`.
	kind: "app-model" | "library"

	// The Daml package NAME: the SCU resolution key on-ledger, not the filename.
	package: =~"^[a-z][a-z0-9-]*[a-z0-9]$"

	produced_by: #Repo
	summary:     string & !=""

	// Other streams this DAR data-depends on. Defaulted rather than optional so
	// every use site can just iterate it — `*` puts the fallback in the schema
	// once instead of repeating a conditional at each reader.
	depends_on: [...string] | *[]
	notes:      string | *""
}

schema: 1
apps: [string]:    #App
streams: [string]: #Stream
