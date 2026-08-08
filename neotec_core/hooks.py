app_name = "neotec_core"
app_title = "Neotec Core"
app_publisher = "Neotec"
app_description = "Shared platform services (governance, evidence, standards, notifications) for the Neotec suite."
app_email = "dev@neotec.example"
app_license = "mit"

# Apps
# ------------------
# neotec_core has no dependency on any other Neotec app - it is the foundation.
required_apps = []

add_to_apps_screen = [
	{
		"name": "neotec_core",
		"logo": "/assets/neotec_core/logo.png",
		"title": "Neotec Core",
		"route": "/app/neotec-core",
		"has_permission": "neotec_core.neotec_core.api.has_app_permission",
	}
]

# Document Events
# ---------------
# neotec_core intentionally does NOT hook "*" globally - that would run on every
# doctype in the whole site, including core Frappe doctypes, which is invasive
# and hard to reason about. Instead, each vertical app opts in explicitly by
# pointing its own doc_events at these shared handlers only for the doctypes
# that need them, e.g. in neotec_pm/hooks.py:
#
#   doc_events = {
#       "PM WBS Task": {
#           "before_validate": "neotec_core.neotec_core.org_context.apply_company_branch_defaults",
#       },
#   }
#
# See neotec_core/org_context.py for the shared function itself.

# Scheduled Tasks
# ---------------
scheduler_events = {
	"hourly": [
		"neotec_core.neotec_core.notifications.run_escalation_sweep",
	],
	"daily": [
		"neotec_core.neotec_core.governance.expire_stale_policy_drafts",
	],
}

# Installation
# ------------
before_install = "neotec_core.install.enforce_supported_frappe_version"

after_install = "neotec_core.neotec_core.setup_data.after_install"
after_migrate = "neotec_core.neotec_core.setup_data.after_migrate"
