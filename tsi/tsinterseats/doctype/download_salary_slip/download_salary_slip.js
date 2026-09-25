// Copyright (c) 2025, Abdulla P I and contributors
// For license information, please see license.txt

frappe.ui.form.on('Download Salary Slip', {
	refresh(frm) {
        const user = frappe.session.user;
        if ( frappe.session.user == 'Administrator') {
            frm.set_value("employee_id", user);
        }
        const currentYear = new Date().getFullYear();
        frm.set_value("year", currentYear);

        if ( frappe.session.user != 'Administrator') {
            frappe.db.get_value(
                "Employee",
                { user_id: frappe.session.user },
                ["employee", "employee_name", "employee_catagory"],
                (r) => {
                    if (r) {
                        frm.set_value("employee_id", r.employee);
                        frm.set_value("employee_name", r.employee_name);
                        frm.set_value("employee_category", r.employee_catagory);
                    }
                }
            );
            if ((!frappe.user.has_role('HR Manager')) || (!frappe.user.has_role('HR User'))) {
                frm.set_df_property("employee_id", "read_only", 1);
            }
        } 
        else {
            frm.set_df_property("employee_id", "read_only", 0);
        }
        frm.disable_save();
    },
    month(frm) {
        frm.trigger("get_slip");
    },
    year(frm) {
        frm.trigger("get_slip");
    },
    employee_id(frm) {
        frm.trigger("get_slip");
    },
    async get_slip(frm) {
        if (frm.doc.employee_id && frm.doc.month && frm.doc.year) {
            try {
                const response = await frm.call("get_salary_slip");
				// console.log(response.message)
                if (response.message) {
                    frm.set_value("salary_slip", response.message[0].name);
                } 
                else {
                    frm.set_value("salary_slip", "");
                    frappe.throw("Salary Slip Not Found");
                }
            } catch (error) {
                console.error("Error fetching salary slip:", error);
                frappe.throw("Salary Slip Not Found");
            }
        }
    },
    async download(frm) {
        if (frm.doc.employee_id && frm.doc.month && frm.doc.year) {
            await frm.trigger("get_slip");
            if (frm.doc.salary_slip) {
                const f_name = frm.doc.salary_slip;
                const print_format = "Salary Slip New";
				window.open(
					frappe.urllib.get_full_url(`/api/method/frappe.utils.print_format.download_pdf?
						doctype=${encodeURIComponent("Salary Slip")}
						&name=${encodeURIComponent(frm.doc.salary_slip)}
						&format=${encodeURIComponent('Salary Slip New')}`)
				);
            } 
            else {
                frappe.throw("Salary Slip Not Found");
            }
        } 
        else if (!frm.doc.employee_id) {
            frappe.throw("Please choose Employee ID");
        } 
        else if (!frm.doc.month) {
            frappe.throw("Please choose Month");
        } 
        else if (!frm.doc.year) {
            frappe.throw("Please choose Year");
        }
    },
});
