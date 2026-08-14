// A typo'd field name. Closed definitions reject it; without that it would be
// dropped silently and resurface as a missing-key error somewhere unhelpful.
package dars

schema: 1
apps: base: {name: "Base", description: "fixture"}
streams: lib: {app: "base", kind: "library", pakcage: "c7-lib", produced_by: "C7-Digital/x", summary: "s"}
