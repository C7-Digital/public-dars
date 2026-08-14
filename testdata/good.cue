// Positive control. If this ever FAILS to vet, the fixtures below are proving
// nothing — a setup where everything errors would pass a suite that only
// checks for failure.
package dars

schema: 1
apps: base: {name: "Base", description: "fixture"}
streams: {
	lib: {app: "base", kind: "library", package: "c7-lib", produced_by: "C7-Digital/x", summary: "s"}
	app: {app: "base", kind: "app-model", package: "c7-app", produced_by: "C7-Digital/x", summary: "s", depends_on: ["lib"]}
}
