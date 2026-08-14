// `app` naming an app that does not exist. Caught only by schema.cue's
// `appExists` rule, which is the thing selftest exists to prove still runs.
package dars

schema: 1
apps: base: {name: "Base", description: "fixture"}
streams: lib: {app: "genral", kind: "library", package: "c7-lib", produced_by: "C7-Digital/x", summary: "s"}
