# Copyright (c) 2026, Neotec and contributors
# License: MIT. See license.txt
"""
Shared org-context defaulting.

Any vertical app (neotec_pm, neotec_risk_grc, ...) can call
`apply_company_branch_defaults` from its own `doc_events` hook for the specific
doctypes that need it. This keeps the behaviour centralised in one place
without forcing it onto every doctype in the system.

Usage in a vertical app's hooks.py:

    doc_events = {
        "PM WBS Task": {
            "before_validate": "neotec_core.neotec_core.org_context.apply_company_branch_defaults",
        },
    }
"""
from __future__ import annotations

import frappe


def apply_company_branch_defaults(doc, method: str | None = None) -> None:
	"""Fill in Company / Branch / Cost Center from the user's default context
	whenever the document leaves those fields blank.

	This never overrides a value the user (or an integration) has already set -
	it only fills gaps, so it is safe to attach broadly.
	"""
	if not frappe.session.user or frappe.session.user == "Guest":
		return

	defaults = frappe.defaults.get_defaults(frappe.session.user) or {}

	if hasattr(doc, "company") and not doc.company:
		doc.company = defaults.get("company") or frappe.defaults.get_global_default("company")

	if hasattr(doc, "branch") and not doc.branch:
		user_branch = frappe.db.get_value("User", frappe.session.user, "branch") if _has_branch_field() else None
		doc.branch = user_branch

	if hasattr(doc, "cost_center") and not doc.cost_center and doc.company:
		doc.cost_center = frappe.db.get_value("Company", doc.company, "cost_center")


def _has_branch_field() -> bool:
	# Guard for sites where the User doctype hasn't been customised with a
	# 'branch' field - avoids a noisy DB error on every save.
	meta = frappe.get_meta("User")
	return meta.has_field("branch")


def get_effective_scope(user: str | None = None) -> dict:
	"""Return the (company, branch, cost_center, roles) scope a user is
	currently operating in - used by permission_query_conditions across the
	whole suite so row-level security logic lives in exactly one place."""
	user = user or frappe.session.user
	defaults = frappe.defaults.get_defaults(user) or {}
	return {
		"company": defaults.get("company"),
		"branch": frappe.db.get_value("User", user, "branch") if _has_branch_field() else None,
		"roles": frappe.get_roles(user),
	}
