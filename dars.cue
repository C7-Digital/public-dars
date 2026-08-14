// dars.cue — what the GitHub Releases API cannot tell you.
//
// Stream-level semantics only. No versions, dates, URLs or asset names: those
// are authoritative in the Releases API, and a second copy here would be a copy
// that goes stale.
//
// Shape is declared in schema.cue and enforced by `cue vet`.
package dars

schema: 1

apps: {
	"7trust": {
		name:        "7Trust"
		description: "Domain ownership verification on Canton"
		repo:        "C7-Digital/domain-verification"
	}
	"7lock": {
		name:        "7LOCK"
		description: "Canton Coin lending marketplace"
		repo:        "C7-Digital/c7lock"
	}
	general: {
		name:        "General"
		description: "App-agnostic Daml building blocks. Usable by any Canton app, C7 or otherwise."
	}
}

streams: {
	"domain-verification": {
		app:         "7trust"
		kind:        "app-model"
		package:     "domain-verification-model"
		produced_by: "C7-Digital/domain-verification"
		summary:     "The on-ledger model behind 7Trust: verification requests, DomainOwnershipToken, AddressBook, TermsOfService."
	}

	c7lock: {
		app:         "7lock"
		kind:        "app-model"
		package:     "c7lock-model"
		produced_by: "C7-Digital/c7lock"
		summary:     "The on-ledger model behind 7LOCK: the loan lifecycle, self-locks, custody and unlocking agreements."
	}

	"c7-credential-v1": {
		app:         "general"
		kind:        "library"
		package:     "c7-credential-v1"
		produced_by: "C7-Digital/domain-verification"
		summary:     "Generic Credential interface plus the AnyValue claim union — an issuer-agnostic, typed credential mechanism."
		notes: """
			The `-v1` is the **interface major**, not a version number. A future incompatible
			interface ships as `c7-credential-v2` and coexists on the same participant.
			Positioned as the forward-compatibility surface for a Canton Network
			Credentials Standard.
			"""
	}

	"c7-kyc": {
		app:         "general"
		kind:        "library"
		package:     "c7-kyc"
		depends_on: ["c7-credential-v1"]
		produced_by: "C7-Digital/domain-verification"
		summary:     "C7 KYC vocabulary (`digital.c7/kyc-*` keys), KYCCertifier delegation and KYCAttestation typed claims."
		notes: """
			No `-v<major>`: it carries upgradeable **templates**, so version progression rides
			Daml SCU rather than a new package name. Consumed by ARTEX for its on-ledger
			KYC gate — which is exactly why it is filed under `general` and not `7trust`.
			"""
	}

	"c7-lei": {
		app:         "general"
		kind:        "library"
		package:     "c7-lei"
		produced_by: "C7-Digital/domain-verification"
		summary:     "GLEIF Legal Entity Identifier records: the LEI template with ISO-17442 MOD 97-10 validation enforced on-ledger."
		notes: """
			Structurally self-contained — no cross-DAR references — so it ships on its own
			cadence rather than tracking the 7Trust model.
			"""
	}

	"c7-unlock": {
		app:         "general"
		kind:        "library"
		package:     "c7-unlock"
		produced_by: "C7-Digital/c7lock"
		summary:     "AuthorizeUnlock: a holder-signed, owner-controlled delegation over splice-amulet LockedAmulets."
		notes: """
			`AuthorizeUnlock_Unlock` runs with `{holder} ∪ {owner}` authority, which lets the
			owner exercise `LockedAmulet_UnlockV2` **before** expiry from a single wallet
			signature — the pre-expiry unlock a CIP-0103 wallet session cannot otherwise
			perform. holder/owner/operator are plain parties, so any app that locks Amulet
			can use it, not just the one that builds it.
			"""
	}
}
