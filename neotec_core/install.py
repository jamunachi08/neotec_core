# Copyright (c) 2026, Neotec and contributors
# License: MIT. See license.txt
from __future__ import annotations

import frappe

MIN_FRAPPE_MAJOR = 15


def enforce_supported_frappe_version() -> None:
	version = frappe.__version__
	major = int(version.split(".")[0])
	if major < MIN_FRAPPE_MAJOR:
		frappe.throw(
			f"neotec_core requires Frappe v{MIN_FRAPPE_MAJOR}+ (found v{version}). "
			"Please upgrade your bench before installing."
		)
