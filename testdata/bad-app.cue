// `app` naming an app that does not exist. Only caught by checks.cue, and only
// when vet is run with -c.
package dars

schema: 1
apps: base: {name: "Base", description: "fixture"}
streams: lib: {app: "genral", kind: "library", package: "c7-lib", produced_by: "C7-Digital/x", summary: "s"}
