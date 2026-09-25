from . import __version__ as app_version

app_name = "tsi"
app_title = "tsinterseats"
app_publisher = "Abdulla P I"
app_description = "tsinterseats"
app_email = "abdulla.pi@groupteampro.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/tsi/css/tsi.css"
# app_include_js = "/assets/tsi/js/tsi.js"

# include js, css files in header of web template
# web_include_css = "/assets/tsi/css/tsi.css"
# web_include_js = "/assets/tsi/js/tsi.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "tsi/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]
jinja = {
	"methods": [
		"tsi.job_app_custom.salary_details",
		"tsi.monthly_in_ot_custom.monthly_in_out",
        "tsi.leave_custom.leave_days_count"
	]
}
# fixtures = ["Client Script","Print Format","Report","Workspace"]
# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "tsi.utils.jinja_methods",
#	"filters": "tsi.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "tsi.install.before_install"
# after_install = "tsi.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "tsi.uninstall.before_uninstall"
# after_uninstall = "tsi.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "tsi.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

override_doctype_class = {
	"Salary Slip": "tsi.overrides.CustomSalarySlip",
    # "Attendance" : "tsi.overrides.CustomAttendance",
    # "Leave Application" : "tsi.overrides.CustomLeaveApplication",
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
#	"all": [
#		"tsi.tasks.all"
#	],
#	"daily": [
#		"tsi.tasks.daily"
#	],
#	"hourly": [
#		"tsi.tasks.hourly"
#	],
#	"weekly": [
#		"tsi.tasks.weekly"
#	],
#	"monthly": [
#		"tsi.tasks.monthly"
#	],
"cron":{
		"*/10 * * * *" :[
			'tsi.mark_attendance.mark_att_process'
		],
		"30 00 * * *" :[
			'tsi.employee_custom.update_relieving_date'
		],
        "*/10 * * * *" :[
			'tsi.mark_attendance.mark_canteen_coupons'
		],
	}
}

# Testing
# -------

# before_tests = "tsi.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "tsi.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "tsi.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["tsi.utils.before_request"]
# after_request = ["tsi.utils.after_request"]

# Job Events
# ----------
# before_job = ["tsi.utils.before_job"]
# after_job = ["tsi.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"tsi.auth.validate"
# ]
doc_events = {
	'Full and Final Statement': {
		'before_submit': 'tsi.F_and_F_custom.update_mis_status_on_submit'
	},
	# 'Leave Application': {
	# 	'validate': ['tsi.custom.validate_leave_dates' , 'tsi.custom.validate_leave_type_and_half_day','tsi.custom.validate_earn_leave','tsi.custom.validate_casual_leave','tsi.custom.validate_combined_leave']
	# },   
	'Employee Checkin':{
		'on_update': 'tsi.checkin_custom.update_att'
	},
	# "Attendance":
	# {
	# 	'on_update': ['tsi.mark_attendance.update_att','tsi.mark_attendance.mark_wh_ot_on_update']
	# },
	# 
    "Attendance":{
		'before_insert': ['tsi.tsinterseats.doctype.early_out.early_out.early']
	},
    "Employee":{
		"validate": "tsi.employee_custom.inactive_employee"
	},
    "Leave Application": {
		"after_insert": ["tsi.leave_custom.get_casual_leaves","tsi.leave_custom.cl_el_restriction","tsi.leave_custom.el_restriction"]
	},
    'Scheduled Job Log':{
       "validate":"tsi.schedule_custom.schedule_log_fail" 
	},
	"Overtime Request": {
        "before_save": "tsi.ot_custom.validate_overtime_reason_before_submit"
        
    },
    "DH Approval": {
        "before_save": "tsi.dh_custom.validate_dh_reason_before_submit"
        
    }
    
    # "On Duty Application":{
	# 	"validate": "tsi.custom.restrict_od"
	# },
	# "Payroll Entry": {
	# 	"before_submit": ["tsi.custom.update_attendance_bonus"]
	# },
}
