# Public Dars

Store public DARs that [C7.digital](c7.digital/) creates for applications on Canton Network.

## Release layout

This repository is the shared release registry for every C7 Canton Network
application. Releases are namespaced **per stream** so multiple apps — and the
shared model libraries they build on — can coexist without tag collisions, and
every stream additionally has a moving `<stream>-latest` release that always
points at the newest version.

| Stream                               | Versioned tag pattern        | Moving "latest" tag           | DAR asset                            |
| ------------------------------------ | ---------------------------- | ----------------------------- | ------------------------------------ |
| 7Trust (Domain-Verification)         | `domain-verification/v<ver>` | `domain-verification-latest`  | `domain-verification-model[-<ver>].dar` |
| 7LOCK                                | `c7lock/v<ver>`              | `c7lock-latest`               | `c7lock-model[-<ver>].dar`           |
| Credential (shared library)          | `credential/v<ver>`          | `credential-latest`           | `credential[-<ver>].dar`             |
| KYC (shared library)                 | `kyc/v<ver>`                 | `kyc-latest`                  | `kyc[-<ver>].dar`                    |

### Shared model libraries

`credential` and `kyc` are **app-agnostic Daml building blocks**, not
applications. They are published here so any Canton app can vendor them as
neutral compiled artifacts and codegen against them, independent of the app
that happens to build them:

- **`credential`** — the generic `Credential` interface plus the `AnyValue`
  claim union: an issuer-agnostic, typed credential mechanism. This is the
  forward-compatibility surface for the Canton Network Credentials Standard.
- **`kyc`** — the C7 KYC vocabulary (`digital.c7/kyc-*` key constants) plus
  `KYCCertifier` (an issuer delegates attestation to a certifier over an
  allowed-key set) and `KYCAttestation` (typed `AnyValue` claims). Built on
  top of the `credential` DAR.

Both are versioned independently of any application (currently **v0.0.1**), so
a consumer pins `credential/v<ver>` / `kyc/v<ver>` and is unaffected by app
release cadence. They are produced by the 7Trust (Domain-Verification) build
but owned as shared infrastructure.

- The **versioned releases** carry the version in the filename
  (e.g. `domain-verification-model-0.1.0.dar`, `credential-0.0.1.dar`) so each
  release URL is self-describing and immutable.
- The **`<stream>-latest` releases** carry the DAR with the *unversioned*
  filename (e.g. `domain-verification-model.dar`, `credential.dar`) so a fixed
  download URL always resolves to the newest DAR:
  `https://github.com/C7-Digital/public-dars/releases/download/<stream>-latest/<asset>.dar`
  (e.g. `.../download/credential-latest/credential.dar`).
- All releases are published with `make_latest: false`; this repository's
  `/releases/latest` is therefore deliberately unset — there is no single
  "latest" across streams. Pick the per-stream tag.

## License

[![CC BY-NC 4.0][cc-by-nc-shield]][cc-by-nc]

This work is licensed under a [Creative Commons Attribution-NonCommercial 4.0 International License][cc-by-nc].

[cc-by-nc]: https://creativecommons.org/licenses/by-nc/4.0/
[cc-by-nc-shield]: https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg
