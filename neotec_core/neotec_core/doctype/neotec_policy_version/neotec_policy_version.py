# Copyright (c) 2026, Neotec and contributors
# License: MIT. See license.txt
from __future__ import annotations

import json

import frappe
from frappe.model.document import Document


class NeotecPolicyVersion(Document):
	def validate(self):
		self._validate_payload_is_json_object()
		self._validate_immutable_once_approved()

	def _validate_payload_is_json_object(self):
		try:
			obj = json.loads(self.payload_json or "{}")
		except (json.JSONDecodeError, TypeError):
			frappe.throw(frappe._("Payload must be valid JSON."))
		if not isinstance(obj, dict):
			frappe.throw(frappe._("Payload must be a JSON object, not a list or scalar."))

	def _validate_immutable_once_approved(self):
		"""Once a policy version has been Approved, its payload must never
		change silently - any change requires a brand new version, submitted
		and re-approved through the workflow. This is what makes the
		version history trustworthy for audit evidence."""
		if self.is_new() or self.status != "Approved":
			return
		before = self.get_doc_before_save()
		if before and before.payload_json != self.payload_json:
			frappe.throw(
				frappe._(
					"Payload of an Approved policy version cannot be edited. "
					"Submit a new version instead."
				)
			)
