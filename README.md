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
| Credential (shared library)          | `c7-credential-v1/v<ver>`    | `c7-credential-v1-latest`     | `c7-credential-v1[-<ver>].dar`       |
| KYC (shared library)                 | `c7-kyc/v<ver>`             | `c7-kyc-latest`               | `c7-kyc[-<ver>].dar`                 |
| Unlock delegation (shared library)   | `c7-unlock/v<ver>`           | `c7-unlock-latest`            | `c7-unlock[-<ver>].dar`              |

### Shared model libraries

`c7-credential-v1`, `c7-kyc` and `c7-unlock` are **app-agnostic Daml building
blocks**, not applications. They are published here so any Canton app can vendor
them as neutral compiled artifacts and codegen against them, independent of the
app that happens to build them:

- **`c7-credential-v1`** — the generic `Credential` interface plus the
  `AnyValue` claim union: an issuer-agnostic, typed credential mechanism. This
  is the forward-compatibility surface for the Canton Network Credentials
  Standard. The `-v1` is the interface major (a future incompatible interface
  ships as `c7-credential-v2` and coexists on a participant).
- **`c7-kyc`** — the C7 KYC vocabulary (`digital.c7/kyc-*` key constants) plus
  `KYCCertifier` (an issuer delegates attestation to a certifier over an
  allowed-key set) and `KYCAttestation` (typed `AnyValue` claims). Built on
  top of the `c7-credential-v1` DAR. No `-v<major>` — it carries upgradeable
  templates, so version progression rides Daml SCU.
- **`c7-unlock`** — `AuthorizeUnlock`, a holder-signed, owner-controlled
  delegation over splice-amulet `LockedAmulet`s. Its `AuthorizeUnlock_Unlock`
  choice runs with `{holder} ∪ {owner}` authority, which lets the owner exercise
  `LockedAmulet_UnlockV2` **before expiry** from a single wallet signature — the
  pre-expiry unlock a CIP-0103 wallet session cannot otherwise perform.
  `holder` / `owner` / `operator` are plain parties, so it is reusable by any
  app that locks Amulet, not just the one that builds it.

All three use the `c7-` package-name prefix (the C7 org namespace, mirroring
`splice-*` in the ecosystem) so the names don't collide with another vendor's
`credential` / `kyc` / `unlock` DAR on a shared participant — package name is an
on-ledger SCU resolution key, not just a filename. All three are versioned
independently of any application, so a consumer pins `c7-credential-v1/v<ver>`,
`c7-kyc/v<ver>` or `c7-unlock/v<ver>` and is unaffected by app release cadence.
`c7-credential-v1` and `c7-kyc` are produced by the 7Trust
(Domain-Verification) build and `c7-unlock` by the 7LOCK build, but all are
owned as shared infrastructure — a stream only moves when its own DAR changes,
not when the app that builds it releases.

- The **versioned releases** carry the version in the filename
  (e.g. `domain-verification-model-0.1.0.dar`, `c7-credential-v1-0.0.1.dar`) so
  each release URL is self-describing and immutable.
- The **`<stream>-latest` releases** carry the DAR with the *unversioned*
  filename (e.g. `domain-verification-model.dar`, `c7-credential-v1.dar`) so a fixed
  download URL always resolves to the newest DAR:
  `https://github.com/C7-Digital/public-dars/releases/download/<stream>-latest/<asset>.dar`
  (e.g. `.../download/c7-credential-v1-latest/c7-credential-v1.dar`).
- Releases are published with `make_latest: false`: there is no single
  "latest" across streams, so **do not rely on this repository's
  `/releases/latest`** — it is not a meaningful pointer here. Always pick the
  per-stream tag (a `<stream>/v<ver>` pin, or the moving `<stream>-latest`).

## License

[![CC BY-NC 4.0][cc-by-nc-shield]][cc-by-nc]

This work is licensed under a [Creative Commons Attribution-NonCommercial 4.0 International License][cc-by-nc].

[cc-by-nc]: https://creativecommons.org/licenses/by-nc/4.0/
[cc-by-nc-shield]: https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg
