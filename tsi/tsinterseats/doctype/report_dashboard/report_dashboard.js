// Copyright (c) 2025, Abdulla P I and contributors
// For license information, please see license.txt

frappe.ui.form.on('Report Dashboard', {
	to_date(frm) {
        if (frm.doc.to_date < frm.doc.from_date) {
            frappe.throw(__('The "From Date" cannot be greater than the "To Date"'));
            return;
        }
    },
    validate(frm) {
        if (frm.doc.to_date < frm.doc.from_date) {
            frappe.throw(__('The "From Date" cannot be greater than the "To Date"'));
            frappe.validate = True
        }
    },
	download(frm) {
    if (frm.doc.to_date < frm.doc.from_date) {
        frappe.throw(__('The "From Date" cannot be greater than the "To Date"'));
        return;
    }

    if (frm.doc.reports == 'Earned Leave Report') {
        var path = "tsi.tsinterseats.doctype.report_dashboard.el_leave.download";
        var args = 'from_date=' + encodeURIComponent(frm.doc.from_date) +
                    '&to_date=' + encodeURIComponent(frm.doc.to_date);
        if (frm.doc.employee) {
            args += '&employee=' + encodeURIComponent(frm.doc.employee);
        }
        if (frm.doc.employee_category) {
            args += '&employee_catagory=' + encodeURIComponent(frm.doc.employee_category);
        }
        if (frm.doc.branch) {
            args += '&branch=' + encodeURIComponent(frm.doc.branch);
        }
    }
    if (frm.doc.reports == 'Test') {
        var path = "tsi.tsinterseats.doctype.report_dashboard.test_el_report.download";
        var args = 'from_date=' + encodeURIComponent(frm.doc.from_date) +
                    '&to_date=' + encodeURIComponent(frm.doc.to_date);
    }
    if (frm.doc.reports == 'Yearly Bonus') {
        var path = "tsi.tsinterseats.doctype.report_dashboard.yearly_bonus.download";
        var args = 'from_date=' + encodeURIComponent(frm.doc.from_date) +
                    '&to_date=' + encodeURIComponent(frm.doc.to_date);

        if (frm.doc.employee) {
            args += '&employee=' + encodeURIComponent(frm.doc.employee);
        }
        if (frm.doc.employee_category) {
            args += '&employee_catagory=' + encodeURIComponent(frm.doc.employee_category);
        }
        if (frm.doc.branch) {
            args += '&branch=' + encodeURIComponent(frm.doc.branch);
        }
    }
    

    if (path) {
        window.location.href = frappe.request.url +
            '?cmd=' + path + '&' + args;
    }
}

});
