# Public Dars

Store public DARs that [C7.digital](c7.digital/) creates for applications on Canton Network.

## Release layout

This repository is the shared release registry for every C7 Canton Network
application. Releases are namespaced **per application** so multiple apps can
coexist without tag collisions, and every app additionally has a moving
`<app>-latest` release that always points at the newest version.

| Application                          | Versioned tag pattern        | Moving "latest" tag           | DAR asset                            |
| ------------------------------------ | ---------------------------- | ----------------------------- | ------------------------------------ |
| 7Trust (Domain-Verification)         | `domain-verification/v<ver>` | `domain-verification-latest`  | `domain-verification-model[-<ver>].dar` |
| 7LOCK                                | `c7lock/v<ver>`              | `c7lock-latest`               | `c7lock-model[-<ver>].dar`           |

- The **versioned releases** carry the version in the filename
  (e.g. `domain-verification-model-0.1.0.dar`) so each release URL is
  self-describing and immutable.
- The **`<app>-latest` releases** carry the DAR with the *unversioned*
  filename (e.g. `domain-verification-model.dar`) so a fixed download URL
  always resolves to the newest DAR:
  `https://github.com/C7-Digital/public-dars/releases/download/<app>-latest/<app>-model.dar`.
- All releases are published with `make_latest: false`; this repository's
  `/releases/latest` is therefore deliberately unset — there is no single
  "latest" across applications. Pick the per-app stream.

## License

[![CC BY-NC 4.0][cc-by-nc-shield]][cc-by-nc]

This work is licensed under a [Creative Commons Attribution-NonCommercial 4.0 International License][cc-by-nc].

[cc-by-nc]: https://creativecommons.org/licenses/by-nc/4.0/
[cc-by-nc-shield]: https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg
