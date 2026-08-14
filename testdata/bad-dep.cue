// `depends_on` naming a stream that does not exist. Same as above: checks.cue + -c.
package dars

schema: 1
apps: base: {name: "Base", description: "fixture"}
streams: lib: {app: "base", kind: "library", package: "c7-lib", produced_by: "C7-Digital/x", summary: "s", depends_on: ["nope"]}
