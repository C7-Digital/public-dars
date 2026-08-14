// `kind` outside the known set. Silently dropped the stream from the README
// table before validation existed — the failure this registry exists to prevent.
package dars

schema: 1
apps: base: {name: "Base", description: "fixture"}
streams: lib: {app: "base", kind: "libary", package: "c7-lib", produced_by: "C7-Digital/x", summary: "s"}
