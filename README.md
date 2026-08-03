# Public Dars

Store public DARs that [C7.digital](c7.digital/) creates for applications on Canton Network.

## Release layout

This repository is the shared release registry for every C7 Canton Network
application. Releases are namespaced **per stream** so multiple apps — and the
shared model libraries they build on — can coexist without tag collisions.

Every release is immutable and **every asset carries its version in the
filename**. There is deliberately no moving `<stream>-latest` pointer: see
[Why there is no "latest"](#why-there-is-no-latest).

| Stream                               | Tag pattern                  | DAR asset                            |
| ------------------------------------ | ---------------------------- | ------------------------------------ |
| 7Trust (Domain-Verification)         | `domain-verification/v<ver>` | `domain-verification-model-<ver>.dar` |
| 7LOCK                                | `c7lock/v<ver>`              | `c7lock-model-<ver>.dar`             |
| Credential (shared library)          | `c7-credential-v1/v<ver>`    | `c7-credential-v1-<ver>.dar`         |
| KYC (shared library)                 | `c7-kyc/v<ver>`              | `c7-kyc-<ver>.dar`                   |
| Unlock delegation (shared library)   | `c7-unlock/v<ver>`           | `c7-unlock-<ver>.dar`                |

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

- Every release carries the version in the filename
  (e.g. `domain-verification-model-0.1.0.dar`, `c7-credential-v1-0.0.1.dar`) so
  each release URL is self-describing and immutable, and so a DAR remains
  identifiable once it has been downloaded.
- Releases are published with `make_latest: false`: there is no single
  "latest" across streams, so **do not rely on this repository's
  `/releases/latest`** — it is not a meaningful pointer here. Always pin a
  `<stream>/v<ver>` tag.

### Why there is no "latest"

Each stream briefly had a moving `<stream>-latest` release whose asset used the
*unversioned* filename (`c7lock-model.dar`) so that one fixed URL always served
the newest build. Those releases have been withdrawn.

The stable URL was convenient exactly once — at download time. Afterwards the
file is indistinguishable from any other build of the same stream: nothing in
`c7lock-model.dar` says which version it is, a lockfile or vendor script that
globs `c7lock-model-*.dar` will not match it, and two copies from different
releases look identical on disk. For artifacts whose whole purpose is to be
pinned and vendored by downstream consumers, that is the wrong trade.

To track the newest version, resolve it and then pin it:

```bash
gh release list --repo C7-Digital/public-dars | grep '^7LOCK'
gh release download c7lock/v0.2.6 --repo C7-Digital/public-dars -p 'c7lock-model-*.dar'
```

#### The withdrawal, for the record

Five pointer releases existed — `domain-verification-latest`,
`c7-credential-v1-latest`, `c7-kyc-latest`, `c7lock-latest`,
`c7-unlock-latest`. They were deleted here, by hand, on 2026-08-02; deleting a
release removes its assets, so no unversioned DAR is served from this registry
any more. A release deletion leaves its git tag behind, so the tags go too:

```bash
git push --delete origin <stream>-latest
```

Nothing recreates them: the publishing workflows in `C7-Digital/c7lock` and
`C7-Digital/domain-verification` no longer have the steps that did. That is
deliberately **not** a recurring cleanup step in those workflows — a one-time
deletion encoded as a step that runs on every release is a standing delete
grant on this public registry, long outliving the thing it was meant to undo,
and it would fire at whenever-the-next-release-happens rather than at a moment
someone chose.

If you pinned a `<stream>-latest` URL, it now 404s. Resolve and pin a
`<stream>/v<ver>` tag as above; that URL will not move again.

## License

[![CC BY-NC 4.0][cc-by-nc-shield]][cc-by-nc]

This work is licensed under a [Creative Commons Attribution-NonCommercial 4.0 International License][cc-by-nc].

[cc-by-nc]: https://creativecommons.org/licenses/by-nc/4.0/
[cc-by-nc-shield]: https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg
