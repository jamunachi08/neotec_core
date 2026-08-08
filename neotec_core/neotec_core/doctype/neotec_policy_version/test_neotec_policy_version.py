# Copyright (c) 2026, Neotec and contributors
# License: MIT. See license.txt
from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from neotec_core.neotec_core.governance import (
	approve_policy_version,
	get_active_policy,
	submit_policy_version,
)

TEST_APP = "neotec_test_app"


class TestNeotecPolicyVersion(FrappeTestCase):
	def tearDown(self):
		frappe.db.delete("Neotec Policy Version", {"app": TEST_APP})

	def test_submit_creates_in_review_version(self):
		result = submit_policy_version(TEST_APP, "risk_scoring_config", "v1", {"max_score": 100})
		doc = frappe.get_doc("Neotec Policy Version", result["name"])
		self.assertEqual(doc.status, "In Review")

	def test_duplicate_version_is_rejected(self):
		submit_policy_version(TEST_APP, "risk_scoring_config", "v1", {"max_score": 100})
		with self.assertRaises(frappe.ValidationError):
			submit_policy_version(TEST_APP, "risk_scoring_config", "v1", {"max_score": 200})

	def test_approve_retires_previous_active_version(self):
		submit_policy_version(TEST_APP, "risk_scoring_config", "v1", {"max_score": 100})
		approve_policy_version(TEST_APP, "risk_scoring_config", "v1")

		submit_policy_version(TEST_APP, "risk_scoring_config", "v2", {"max_score": 150})
		approve_policy_version(TEST_APP, "risk_scoring_config", "v2")

		v1_status = frappe.db.get_value(
			"Neotec Policy Version", {"app": TEST_APP, "policy_name": "risk_scoring_config", "version": "v1"}, "status"
		)
		self.assertEqual(v1_status, "Retired")

		active = get_active_policy(TEST_APP, "risk_scoring_config")
		self.assertEqual(active["version"], "v2")
		self.assertEqual(active["payload"]["max_score"], 150)

	def test_approved_payload_is_immutable(self):
		submit_policy_version(TEST_APP, "immutable_check", "v1", {"threshold": 10})
		approve_policy_version(TEST_APP, "immutable_check", "v1")

		doc = frappe.get_doc(
			"Neotec Policy Version",
			{"app": TEST_APP, "policy_name": "immutable_check", "version": "v1"},
		)
		doc.payload_json = '{"threshold": 999}'
		with self.assertRaises(frappe.ValidationError):
			doc.save()
