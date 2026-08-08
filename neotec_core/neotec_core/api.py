# Copyright (c) 2026, Neotec and contributors
# License: MIT. See license.txt
from __future__ import annotations

import json

import frappe

from .governance import (
	approve_policy_version as _approve_policy_version,
	create_audit_snapshot as _create_audit_snapshot,
	get_active_policy as _get_active_policy,
	governance_overview as _governance_overview,
	reject_policy_version as _reject_policy_version,
	submit_policy_version as _submit_policy_version,
	verify_audit_chain as _verify_audit_chain,
)


def has_app_permission() -> bool:
	"""Anyone with a Neotec-suite role can see the Core app on the apps
	screen; fine-grained doctype permissions still apply underneath."""
	return bool(
		set(frappe.get_roles(frappe.session.user))
		& {"System Manager", "Neotec Suite Admin", "Neotec Suite User"}
	)


@frappe.whitelist()
def get_standards_profile() -> dict:
	from .standards import get_standards_profile as _profile

	return _profile()


@frappe.whitelist()
def submit_policy_version(app: str, policy_name: str, version: str, payload: str, effective_from: str | None = None) -> dict:
	obj = json.loads(payload) if isinstance(payload, str) else payload
	if not isinstance(obj, dict):
		frappe.throw(frappe._("payload must be a JSON object"))
	return _submit_policy_version(app, policy_name, version, obj, effective_from)


@frappe.whitelist()
def approve_policy_version(app: str, policy_name: str, version: str) -> dict:
	return _approve_policy_version(app, policy_name, version)


@frappe.whitelist()
def reject_policy_version(app: str, policy_name: str, version: str, reason: str = "") -> dict:
	return _reject_policy_version(app, policy_name, version, reason)


@frappe.whitelist()
def get_active_policy(app: str, policy_name: str) -> dict | None:
	return _get_active_policy(app, policy_name)


@frappe.whitelist()
def get_governance_overview(app: str) -> dict:
	return _governance_overview(app)


@frappe.whitelist()
def create_audit_snapshot(app: str, process_name: str, inputs: str, outputs: str, policy_ref: str | None = None) -> dict:
	in_obj = json.loads(inputs) if isinstance(inputs, str) else inputs
	out_obj = json.loads(outputs) if isinstance(outputs, str) else outputs
	if not isinstance(in_obj, dict) or not isinstance(out_obj, dict):
		frappe.throw(frappe._("inputs/outputs must be JSON objects"))
	return _create_audit_snapshot(app, process_name, in_obj, out_obj, policy_ref)


@frappe.whitelist()
def verify_audit_chain(app: str, process_name: str) -> dict:
	return _verify_audit_chain(app, process_name)
