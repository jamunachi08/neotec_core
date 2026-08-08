# Copyright (c) 2026, Neotec and contributors
# License: MIT. See license.txt
"""
Reference data for public-domain standards that every vertical maps its own
records onto. Keeping this in neotec_core means neotec_risk_grc, neotec_audit
and neotec_compliance all speak the same taxonomy instead of inventing three
incompatible ones.

Sources are all public frameworks - Basel Committee event-type categories,
COSO ERM components, ISO 31000 risk-criteria vocabulary, and ISA audit
assertions. None of this is proprietary to any vendor.
"""
from __future__ import annotations

import frappe

# Basel II/III operational risk event-type categories (public Basel Committee taxonomy)
BASEL_EVENT_TYPES = {
	"INTERNAL_FRAUD": "Basel:L1-Internal-Fraud",
	"EXTERNAL_FRAUD": "Basel:L1-External-Fraud",
	"EMPLOYMENT_PRACTICES": "Basel:L1-Employment-Practices-Workplace-Safety",
	"CLIENTS_PRODUCTS_PRACTICES": "Basel:L1-Clients-Products-Business-Practices",
	"DAMAGE_PHYSICAL_ASSETS": "Basel:L1-Damage-to-Physical-Assets",
	"BUSINESS_DISRUPTION": "Basel:L1-Business-Disruption-System-Failures",
	"EXECUTION_DELIVERY": "Basel:L1-Execution-Delivery-Process-Management",
}

# COSO ERM (2017) components - used to tag controls/policies by which
# component of the framework they belong to.
COSO_COMPONENTS = [
	"Governance & Culture",
	"Strategy & Objective-Setting",
	"Performance",
	"Review & Revision",
	"Information, Communication & Reporting",
]

# ISO 31000 risk criteria vocabulary - used for consistent likelihood/impact
# scale labelling across the suite.
ISO31000_LIKELIHOOD_SCALE = ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"]
ISO31000_IMPACT_SCALE = ["Insignificant", "Minor", "Moderate", "Major", "Severe"]

# ISA financial statement assertions - used by neotec_audit to tag findings
# and evidence against the assertion(s) they test.
ISA_ASSERTIONS = [
	"Existence",
	"Completeness",
	"Accuracy",
	"Valuation",
	"Rights & Obligations",
	"Presentation & Disclosure",
	"Cut-off",
]


@frappe.whitelist()
def get_standards_profile() -> dict:
	"""Single read-only endpoint every vertical's UI can call to populate
	dropdowns/legends consistently, instead of hardcoding these lists per app."""
	return {
		"basel_event_types": BASEL_EVENT_TYPES,
		"coso_components": COSO_COMPONENTS,
		"iso31000_likelihood_scale": ISO31000_LIKELIHOOD_SCALE,
		"iso31000_impact_scale": ISO31000_IMPACT_SCALE,
		"isa_assertions": ISA_ASSERTIONS,
	}


def classify_basel_event(event_type: str) -> str:
	return BASEL_EVENT_TYPES.get(str(event_type or "").upper(), "Basel:L1-Other")
