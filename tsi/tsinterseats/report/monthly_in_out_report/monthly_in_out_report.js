// Copyright (c) 2023, Abdulla P I and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Monthly In Out Report"] = {
	// onload: function(report) {
    //     if (!frappe.user.has_role("HR Manager")) {
    //         let current_user = frappe.session.user;

            // Fetch employee details based on the user
            // frappe.call({
            //     method: "tsi.tsinterseats.report.monthly_in_out_report.monthly_in_out_report.get_emp_id",
            //     args: { user_id: current_user },
            //     callback: function(r) {
            //         if (r.message) {
			// 				report.set_filter_value('employee', r.message);
			// 				report.set_filter_property('employee', 'read_only', true);
							
            //         }
			// 	}
            // });
        // }
    // },
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"reqd": 1,
			// "default":frappe.datetime.month_start()
			on_change: function () {
				var from_date = frappe.query_report.get_filter_value('from_date')
				frappe.call({
					method: "tsi.tsinterseats.report.monthly_in_out_report.monthly_in_out_report.get_to_date",
					args: {
						from_date: from_date
					},
					callback(r) {
						frappe.query_report.set_filter_value('to_date', r.message);
						frappe.query_report.refresh();
					}
				})
			}
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd": 1,
			// "default":frappe.datetime.month_end()
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			// "reqd": frappe.user.has_role("HR Manager") ? 0 : 1,
			"read_only": frappe.user.has_role("HR Manager") || frappe.user.has_role("HOD") ? 0 : 1,
			
		},
		
		{
			"fieldname": "employee_catagory",
			"label": __("Employee Catagory"),
			"fieldtype": "Link",
			"options": "Employee Catagory",
			// "default":"",
			"read_only": frappe.user.has_role("HR Manager") ? 0 : 1,
		},
		
	]
};
