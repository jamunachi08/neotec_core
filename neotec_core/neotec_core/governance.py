# Copyright (c) 2026, Neotec and contributors
# License: MIT. See license.txt
"""
Shared governance engine used by every Neotec vertical:

  1. Policy versioning  - draft -> review -> approved -> retired, with a full
     version history per (app, policy_name).
  2. Evidence engine     - hash-chained "Audit Snapshot" records so any
     vertical can prove "this is exactly what the system showed on date X,
     under policy version Y" - this is what makes neotec_audit's opinions
     defensible and is the piece worth getting right before anything else.

Both are intentionally app-agnostic: every vertical calls the same functions
with its own app name as a namespace, so there is one implementation to audit
and test instead of four copies.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe.utils import now_datetime

POLICY_DOCTYPE = "Neotec Policy Version"
SNAPSHOT_DOCTYPE = "Neotec Audit Snapshot"

_VALID_TRANSITIONS = {
	"Draft": {"In Review"},
	"In Review": {"Approved", "Rejected", "Draft"},
	"Approved": {"Retired"},
	"Rejected": {"Draft"},
	"Retired": set(),
}


# ---------------------------------------------------------------------------
# Policy versioning
# ---------------------------------------------------------------------------

def submit_policy_version(
	app: str,
	policy_name: str,
	version: str,
	payload: dict,
	effective_from: str | None = None,
) -> dict:
	"""Create (or move to review) a policy version. `payload` is whatever
	config the calling vertical needs to version - e.g. a risk scoring
	config, a materiality formula, a set of escalation thresholds."""
	existing = frappe.db.exists(POLICY_DOCTYPE, {"app": app, "policy_name": policy_name, "version": version})
	if existing:
		frappe.throw(
			frappe._("Policy {0} v{1} already exists for {2}").format(policy_name, version, app)
		)

	doc = frappe.new_doc(POLICY_DOCTYPE)
	doc.update(
		{
			"app": app,
			"policy_name": policy_name,
			"version": version,
			"payload_json": json.dumps(payload, sort_keys=True, default=str),
			"status": "In Review",
			"effective_from": effective_from,
			"submitted_by": frappe.session.user,
			"submitted_on": now_datetime(),
		}
	)
	doc.insert(ignore_permissions=False)
	return {"name": doc.name, "status": doc.status}


def approve_policy_version(app: str, policy_name: str, version: str) -> dict:
	doc = _get_policy(app, policy_name, version)
	_transition(doc, "Approved")
	doc.approved_by = frappe.session.user
	doc.approved_on = now_datetime()
	doc.save()

	# Retire the previously-approved version of the same policy, if any -
	# a policy should have at most one currently-active version.
	frappe.db.set_value(
		POLICY_DOCTYPE,
		{
			"app": app,
			"policy_name": policy_name,
			"status": "Approved",
			"name": ["!=", doc.name],
		},
		"status",
		"Retired",
	)
	return {"name": doc.name, "status": doc.status}


def reject_policy_version(app: str, policy_name: str, version: str, reason: str = "") -> dict:
	doc = _get_policy(app, policy_name, version)
	_transition(doc, "Rejected")
	doc.rejection_reason = reason
	doc.save()
	return {"name": doc.name, "status": doc.status}


def get_active_policy(app: str, policy_name: str) -> dict | None:
	"""What every vertical's engine should call at runtime - the single
	currently-approved version of a named policy, or None if nothing has
	been approved yet (callers should fall back to a safe built-in default)."""
	name = frappe.db.get_value(
		POLICY_DOCTYPE,
		{"app": app, "policy_name": policy_name, "status": "Approved"},
		"name",
	)
	if not name:
		return None
	doc = frappe.get_doc(POLICY_DOCTYPE, name)
	return {
		"version": doc.version,
		"payload": json.loads(doc.payload_json or "{}"),
		"effective_from": doc.effective_from,
	}


def governance_overview(app: str) -> dict:
	rows = frappe.get_all(
		POLICY_DOCTYPE,
		filters={"app": app},
		fields=["policy_name", "version", "status", "submitted_on", "approved_on"],
		order_by="policy_name asc, version desc",
	)
	by_policy: dict[str, list] = {}
	for r in rows:
		by_policy.setdefault(r["policy_name"], []).append(r)
	return {
		"app": app,
		"policy_count": len(by_policy),
		"policies": by_policy,
	}


def expire_stale_policy_drafts(days: int = 30) -> None:
	"""Scheduled daily: nudge (does not auto-delete) drafts that have sat
	untouched too long, so the governance backlog doesn't silently rot."""
	from frappe.utils import add_days, nowdate

	stale = frappe.get_all(
		POLICY_DOCTYPE,
		filters={"status": "Draft", "modified": ["<", add_days(nowdate(), -days)]},
		fields=["name", "submitted_by", "policy_name", "app"],
	)
	for row in stale:
		frappe.get_doc(
			{
				"doctype": "ToDo",
				"allocated_to": row.submitted_by,
				"description": frappe._(
					"Policy draft '{0}' ({1}) has been idle for over {2} days."
				).format(row.policy_name, row.app, days),
				"reference_type": POLICY_DOCTYPE,
				"reference_name": row.name,
			}
		).insert(ignore_permissions=True)


def _get_policy(app: str, policy_name: str, version: str):
	name = frappe.db.get_value(POLICY_DOCTYPE, {"app": app, "policy_name": policy_name, "version": version}, "name")
	if not name:
		frappe.throw(frappe._("Policy {0} v{1} not found for {2}").format(policy_name, version, app))
	return frappe.get_doc(POLICY_DOCTYPE, name)


def _transition(doc, target_status: str) -> None:
	allowed = _VALID_TRANSITIONS.get(doc.status, set())
	if target_status not in allowed:
		frappe.throw(
			frappe._("Cannot move policy from {0} to {1}").format(doc.status, target_status)
		)
	doc.status = target_status


# ---------------------------------------------------------------------------
# Evidence engine - hash-chained audit snapshots
# ---------------------------------------------------------------------------

def create_audit_snapshot(
	app: str,
	process_name: str,
	inputs: dict,
	outputs: dict,
	policy_ref: str | None = None,
) -> dict:
	"""Record an immutable, hash-chained snapshot of "what the system
	produced, from what inputs, under what policy". Each snapshot links to
	the hash of the previous snapshot for the same (app, process_name), so
	any retroactive tampering breaks the chain and is detectable by
	`verify_audit_chain`.
	"""
	prev_hash = frappe.db.get_value(
		SNAPSHOT_DOCTYPE,
		{"app": app, "process_name": process_name},
		"snapshot_hash",
		order_by="creation desc",
	) or "GENESIS"

	timestamp = now_datetime().isoformat()
	canonical_inputs = json.dumps(inputs, sort_keys=True, default=str)
	canonical_outputs = json.dumps(outputs, sort_keys=True, default=str)

	snapshot_hash = _chain_hash(prev_hash, canonical_inputs, canonical_outputs, policy_ref, timestamp)

	doc = frappe.new_doc(SNAPSHOT_DOCTYPE)
	doc.update(
		{
			"app": app,
			"process_name": process_name,
			"inputs_json": canonical_inputs,
			"outputs_json": canonical_outputs,
			"policy_ref": policy_ref,
			"prev_hash": prev_hash,
			"snapshot_hash": snapshot_hash,
			"recorded_by": frappe.session.user,
			"recorded_on": timestamp,
		}
	)
	# Neotec Audit Snapshot deliberately grants no role direct "create"
	# permission (see its doctype JSON) - the only sanctioned way to add a
	# snapshot is through this function, so we insert as the system here.
	doc.insert(ignore_permissions=True)
	return {"name": doc.name, "snapshot_hash": snapshot_hash}


def verify_audit_chain(app: str, process_name: str) -> dict:
	"""Walk the full chain for a process and confirm every link's hash is
	consistent with its recorded inputs/outputs/prev_hash. Returns the first
	broken link, if any - this is the function a statutory auditor would
	actually run before relying on the trail."""
	rows = frappe.get_all(
		SNAPSHOT_DOCTYPE,
		filters={"app": app, "process_name": process_name},
		fields=["name", "inputs_json", "outputs_json", "policy_ref", "prev_hash", "snapshot_hash", "recorded_on"],
		order_by="creation asc",
	)

	expected_prev = "GENESIS"
	for row in rows:
		if row.prev_hash != expected_prev:
			return {"valid": False, "broken_at": row.name, "reason": "prev_hash mismatch"}
		recomputed = _chain_hash(
			row.prev_hash, row.inputs_json, row.outputs_json, row.policy_ref, str(row.recorded_on)
		)
		if recomputed != row.snapshot_hash:
			return {"valid": False, "broken_at": row.name, "reason": "hash mismatch - data may have been altered"}
		expected_prev = row.snapshot_hash

	return {"valid": True, "chain_length": len(rows), "head_hash": expected_prev}


def _chain_hash(prev_hash: str, inputs_json: str, outputs_json: str, policy_ref: str | None, timestamp: str) -> str:
	material = "|".join([prev_hash, inputs_json, outputs_json, policy_ref or "", timestamp])
	return hashlib.sha256(material.encode("utf-8")).hexdigest()
