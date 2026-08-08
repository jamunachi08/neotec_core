# Copyright (c) 2026, Neotec and contributors
# License: MIT. See license.txt
from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from neotec_core.neotec_core.governance import create_audit_snapshot, verify_audit_chain

TEST_APP = "neotec_test_app"
TEST_PROCESS = "test_process"


class TestNeotecAuditSnapshot(FrappeTestCase):
	def tearDown(self):
		frappe.db.delete("Neotec Audit Snapshot", {"app": TEST_APP})

	def test_chain_builds_and_verifies_clean(self):
		create_audit_snapshot(TEST_APP, TEST_PROCESS, {"x": 1}, {"y": 2})
		create_audit_snapshot(TEST_APP, TEST_PROCESS, {"x": 2}, {"y": 4})
		create_audit_snapshot(TEST_APP, TEST_PROCESS, {"x": 3}, {"y": 6})

		result = verify_audit_chain(TEST_APP, TEST_PROCESS)
		self.assertTrue(result["valid"])
		self.assertEqual(result["chain_length"], 3)

	def test_tampering_with_a_snapshot_breaks_the_chain(self):
		create_audit_snapshot(TEST_APP, TEST_PROCESS, {"x": 1}, {"y": 2})
		create_audit_snapshot(TEST_APP, TEST_PROCESS, {"x": 2}, {"y": 4})

		first = frappe.get_all(
			"Neotec Audit Snapshot", filters={"app": TEST_APP, "process_name": TEST_PROCESS}, order_by="creation asc"
		)[0]
		# Bypass the controller's immutability guard directly at the DB layer
		# to simulate an attempted tamper, exactly like an attacker would.
		frappe.db.set_value("Neotec Audit Snapshot", first.name, "outputs_json", '{"y": 999}')

		result = verify_audit_chain(TEST_APP, TEST_PROCESS)
		self.assertFalse(result["valid"])
		self.assertEqual(result["broken_at"], first.name)

	def test_snapshot_cannot_be_edited_through_the_controller(self):
		create_audit_snapshot(TEST_APP, TEST_PROCESS, {"x": 1}, {"y": 2})
		doc = frappe.get_last_doc("Neotec Audit Snapshot", filters={"app": TEST_APP})
		doc.outputs_json = '{"y": 999}'
		with self.assertRaises(frappe.ValidationError):
			doc.save()

	def test_snapshot_cannot_be_deleted(self):
		create_audit_snapshot(TEST_APP, TEST_PROCESS, {"x": 1}, {"y": 2})
		doc = frappe.get_last_doc("Neotec Audit Snapshot", filters={"app": TEST_APP})
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc("Neotec Audit Snapshot", doc.name)
