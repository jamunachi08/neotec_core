# Copyright (c) 2026, Neotec and contributors
# License: MIT. See license.txt
"""Idempotent seeding of the neotec_core reference data.

Runs on after_install and after_migrate. Every record is created only when it
is absent, so re-running is a no-op and an operator's edits to a seeded record
survive the next migrate. Deliberately does not use Frappe fixtures: fixture
sync overwrites live records on every migrate and cannot express "create if
missing, otherwise leave alone".
"""

from __future__ import annotations

import json
import os

import frappe

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def _load(filename: str) -> list[dict]:
	path = os.path.normpath(os.path.join(_DATA_DIR, filename))
	if not os.path.exists(path):
		frappe.log_error(f"neotec_core seed data missing: {filename}", "neotec_core setup")
		return []
	with open(path, encoding="utf-8") as fh:
		return json.load(fh)


def seed_suite_roles() -> None:
	"""Create the suite roles if absent. Never touches an existing Role."""
	for row in _load("suite_roles.json"):
		role_name = row.get("role_name")
		if not role_name or frappe.db.exists("Role", role_name):
			continue
		doc = frappe.new_doc("Role")
		doc.update(row)
		doc.insert(ignore_permissions=True)


def seed_risk_taxonomy() -> None:
	"""Create the Basel-aligned operational risk taxonomy if absent."""
	for row in _load("risk_taxonomy.json"):
		code = row.get("code")
		if not code or frappe.db.exists("Neotec Risk Taxonomy Entry", {"code": code}):
			continue
		doc = frappe.new_doc("Neotec Risk Taxonomy Entry")
		doc.update(row)
		doc.insert(ignore_permissions=True)


def after_install() -> None:
	seed_suite_roles()
	seed_risk_taxonomy()
	frappe.db.commit()


def after_migrate() -> None:
	seed_suite_roles()
	seed_risk_taxonomy()
	frappe.db.commit()
