# Copyright (c) 2026, Neotec and contributors
# License: MIT. See license.txt
from __future__ import annotations

import frappe
from frappe.model.document import Document


class NeotecEscalationRule(Document):
	def validate(self):
		self._validate_fields_exist_on_target()
		self._validate_at_least_one_recipient()

	def _validate_fields_exist_on_target(self):
		meta = frappe.get_meta(self.target_doctype)
		for fieldname, label in ((self.watch_field, "Watch Field"), (self.timestamp_field, "Timestamp Field")):
			if fieldname in ("name", "creation", "modified"):
				continue  # standard fields on every doctype, not in meta.fields
			if not meta.has_field(fieldname):
				frappe.throw(
					frappe._("{0} '{1}' does not exist on {2}").format(label, fieldname, self.target_doctype)
				)

	def _validate_at_least_one_recipient(self):
		if not self.escalate_to_role and not self.escalate_to_user and self.channel != "Webhook":
			frappe.throw(frappe._("Set an Escalate To Role/User, or choose the Webhook channel."))
