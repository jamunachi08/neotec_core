# Copyright (c) 2026, Neotec and contributors
# License: MIT. See license.txt
from __future__ import annotations

from frappe.model.document import Document


class NeotecRiskTaxonomyEntry(Document):
	"""Reference data only - Basel/COSO/ISO31000/ISA taxonomy entries shipped
	as fixtures. No custom validation needed beyond the doctype schema."""

	pass
