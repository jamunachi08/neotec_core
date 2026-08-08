# Neotec Core

Shared platform services for the Neotec suite (`neotec_pm`, `neotec_risk_grc`,
`neotec_audit`, `neotec_compliance`): org-context defaulting, versioned
governance/policy workflow, a hash-chained evidence engine, a public-standards
reference library (Basel/COSO/ISO 31000/ISA), and a generic escalation engine.

This app has **no dependency on any other Neotec app** - it is the foundation
every vertical installs first.

## Why this exists

Each vertical needs the same handful of cross-cutting services (who am I
acting as, what policy version is currently active, prove this record wasn't
tampered with, escalate this if it's overdue). Building those once here means
one implementation to test and audit, instead of four slightly different
copies.

## Installation

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app /path/to/neotec_core
bench install-app neotec_core
```

## Key modules

| Module | Purpose |
|---|---|
| `neotec_core.org_context` | Company/Branch/Cost Center defaulting, opt-in per doctype |
| `neotec_core.governance` | Policy versioning (draft→review→approved→retired) + hash-chained audit snapshots |
| `neotec_core.standards` | Basel / COSO / ISO 31000 / ISA reference data and lookups |
| `neotec_core.notifications` | Generic rule-based escalation engine (hourly sweep) |
| `neotec_core.api` | Whitelisted endpoints wrapping the above for vertical apps and the UI |

## Running tests

```bash
bench --site your-site.local run-tests --app neotec_core
```

## License

MIT - see `license.txt`. Copyright (c) 2026 Neotec.
