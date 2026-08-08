# Copyright (c) 2026, Neotec and contributors
# License: MIT. See license.txt
"""
Rule-based escalation engine.

Rather than hardcoding "if SLA breached and severity >= High, escalate" logic
into every vertical, each vertical registers "Neotec Escalation Rule" records
naming: which doctype to watch, which field/value combination counts as a
breach, how many hours of inactivity trigger escalation, and who/what to
notify. `run_escalation_sweep` (hourly, see hooks.py) evaluates every active
rule generically.
"""
from __future__ import annotations

import frappe
from frappe.utils import now_datetime, time_diff_in_hours

RULE_DOCTYPE = "Neotec Escalation Rule"


def run_escalation_sweep() -> None:
	rules = frappe.get_all(
		RULE_DOCTYPE,
		filters={"is_active": 1},
		fields=[
			"name",
			"target_doctype",
			"watch_field",
			"watch_value",
			"timestamp_field",
			"threshold_hours",
			"escalate_to_role",
			"escalate_to_user",
			"channel",
			"webhook_url",
		],
	)
	for rule in rules:
		_evaluate_rule(rule)


def _evaluate_rule(rule: dict) -> None:
	if not frappe.db.exists("DocType", rule.target_doctype):
		return

	meta = frappe.get_meta(rule.target_doctype)
	if not (meta.has_field(rule.watch_field) and meta.has_field(rule.timestamp_field)):
		# Misconfigured rule - skip quietly rather than raising in a scheduled job.
		return

	candidates = frappe.get_all(
		rule.target_doctype,
		filters={rule.watch_field: rule.watch_value, "neotec_escalated": ["!=", 1]}
		if meta.has_field("neotec_escalated")
		else {rule.watch_field: rule.watch_value},
		fields=["name", rule.timestamp_field],
	)

	now = now_datetime()
	for row in candidates:
		reference_time = row.get(rule.timestamp_field)
		if not reference_time:
			continue
		hours_elapsed = time_diff_in_hours(now, reference_time)
		if hours_elapsed >= rule.threshold_hours:
			_escalate(rule, row.name, hours_elapsed)


def _escalate(rule: dict, docname: str, hours_elapsed: float) -> None:
	message = frappe._(
		"{0} {1} has been in state '{2}' for {3:.1f}h, past the {4}h escalation threshold."
	).format(rule.target_doctype, docname, rule.watch_value, hours_elapsed, rule.threshold_hours)

	if rule.escalate_to_user:
		frappe.get_doc(
			{
				"doctype": "ToDo",
				"allocated_to": rule.escalate_to_user,
				"description": message,
				"reference_type": rule.target_doctype,
				"reference_name": docname,
				"priority": "High",
			}
		).insert(ignore_permissions=True)

	if rule.escalate_to_role:
		users = frappe.get_all(
			"Has Role", filters={"role": rule.escalate_to_role, "parenttype": "User"}, pluck="parent"
		)
		for user in users:
			frappe.publish_realtime(
				event="neotec_escalation",
				message={"docname": docname, "doctype": rule.target_doctype, "text": message},
				user=user,
			)

	if rule.channel == "Webhook" and rule.webhook_url:
		frappe.enqueue(_post_webhook, queue="short", webhook_url=rule.webhook_url, message=message)

	meta = frappe.get_meta(rule.target_doctype)
	if meta.has_field("neotec_escalated"):
		frappe.db.set_value(rule.target_doctype, docname, "neotec_escalated", 1)

	frappe.logger("neotec_core").info(message)


def _post_webhook(webhook_url: str, message: str) -> None:
	import requests

	try:
		requests.post(webhook_url, json={"text": message}, timeout=5)
	except Exception:
		frappe.log_error(title="Neotec escalation webhook failed")
