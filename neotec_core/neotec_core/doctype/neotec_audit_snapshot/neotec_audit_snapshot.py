# Copyright (c) 2026, Neotec and contributors
# License: MIT. See license.txt
from __future__ import annotations

import frappe
from frappe.model.document import Document


class NeotecAuditSnapshot(Document):
	def validate(self):
		if not self.is_new():
			frappe.throw(
				frappe._(
					"Audit Snapshots are immutable evidence records and cannot be edited "
					"once created. Record a new snapshot instead."
				)
			)

	def on_trash(self):
		frappe.throw(
			frappe._(
				"Audit Snapshots cannot be deleted - they are the evidence trail. "
				"If this record was created in error, note it in a new snapshot instead."
			)
		)
