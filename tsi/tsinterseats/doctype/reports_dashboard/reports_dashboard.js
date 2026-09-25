// Copyright (c) 2023, Abdulla P I and contributors
// For license information, please see license.txt

frappe.ui.form.on('Reports Dashboard', {
	start_date(frm) {
		frappe.call({
			method: 'tsi.tsinterseats.doctype.reports_dashboard.reports_dashboard.get_end_date',
			args: {
				frequency: "Monthly",
				start_date: frm.doc.start_date
			},
			callback: function (r) {
				if (r.message) {
					frm.set_value('end_date', r.message.end_date);
				}
			}
		});
	},
	print:function(frm){
		if(frm.doc.reports == "Monthly IN OUT Report-PDF"){
			var print_format ="Monthly IN OUT Report-PDF";
			var f_name = frm.doc.account
			window.open(frappe.urllib.get_full_url("/api/method/frappe.utils.print_format.download_pdf?"
				+ "doctype=" + encodeURIComponent("Reports Dashboard")
				+ "&name=" + encodeURIComponent(f_name)
				+ "&trigger_print=1"
				+ "&format=" + print_format
				+ "&no_letterhead=0"
			));
		}
	},
	download:function(frm){
		if (frm.doc.reports == 'Salary Summary Report') {
			var path = 'tsi.tsinterseats.doctype.reports_dashboard.salary_summary_report.download'
			var args = 'start_date=%(start_date)s&end_date=%(end_date)s'
		}
		
		if (frm.doc.reports == 'PF Excel Report') {
			var path = 'tsi.tsinterseats.doctype.reports_dashboard.pf_excel_report.download'
			var args = 'start_date=%(start_date)s&end_date=%(end_date)s'
		}
		if (frm.doc.reports == 'Monthly TDS Report') {
			var path = 'tsi.tsinterseats.doctype.reports_dashboard.monthly_tds_report.download'
			var args = 'start_date=%(start_date)s&end_date=%(end_date)s'
		}
		if (frm.doc.reports == 'ESI Excel Report') {
			var path = 'tsi.tsinterseats.doctype.reports_dashboard.esi_report.download'
			var args = 'start_date=%(start_date)s&end_date=%(end_date)s'
		}
		if (frm.doc.reports == 'PF Text File Report') {
			var path = 'tsi.tsinterseats.doctype.reports_dashboard.pf_text_file.get_data_pf'
			var args = 'start_date=%(start_date)s&end_date=%(end_date)s'
		}
		if (frm.doc.reports == 'Summary of PF Contribution Report') {
			var path = 'tsi.tsinterseats.doctype.reports_dashboard.summary_of_pf_contribution.download'
			var args = 'start_date=%(start_date)s&end_date=%(end_date)s'
		}
        if (frm.doc.reports == 'Summary of Labour Welfare Fund Deduction Report') {
			var path = 'tsi.tsinterseats.doctype.reports_dashboard.summary_of_welfare_fund.download'
			var args = 'start_date=%(start_date)s&end_date=%(end_date)s'
		}
		if (frm.doc.reports == 'Summary Of Worker Salary Report') {
			var path = 'tsi.tsinterseats.doctype.reports_dashboard.summary_of_worker_salary_report.download'
			var args = 'start_date=%(start_date)s&end_date=%(end_date)s'
		}
		if (frm.doc.reports == 'Summary Of Factory Staff Salary Report') {
			var path = 'tsi.tsinterseats.doctype.reports_dashboard.summary_of_factory_staff_salary_report.download'
			var args = 'start_date=%(start_date)s&end_date=%(end_date)s'
		}
		if (frm.doc.reports == 'Summary of Administration Staff Salary Report') {
			var path = 'tsi.tsinterseats.doctype.reports_dashboard.summary_of_administration_staff_salary_report.download'
			var args = 'start_date=%(start_date)s&end_date=%(end_date)s'
		}
		if (frm.doc.reports == 'Summary Of Worker Total Salary Report') {
			var path = 'tsi.tsinterseats.doctype.reports_dashboard.summary_of_worker_total_salary_report.download'
			var args = 'start_date=%(start_date)s&end_date=%(end_date)s'
		}
		if (frm.doc.reports == 'Summary Of Production Total Salary Report') {
			var path = 'tsi.tsinterseats.doctype.reports_dashboard.summary_of_production_total_salary_report.download'
			var args = 'start_date=%(start_date)s&end_date=%(end_date)s'
		}
		if (frm.doc.reports == 'Summary Of Staff Salary Report') {
			var path = 'tsi.tsinterseats.doctype.reports_dashboard.summary_of_staff_salary_report.download'
			var args = 'start_date=%(start_date)s&end_date=%(end_date)s'
		}
		if (frm.doc.reports == 'Summary of ESI Deduction Report') {
			var path = 'tsi.tsinterseats.doctype.reports_dashboard.summary_of_esi_deduction_report.download'
			var args = 'start_date=%(start_date)s&end_date=%(end_date)s'
		}
		if (frm.doc.reports == 'Summary of Labour Welfare Fund deduction Report') {
			var path = 'tsi.tsinterseats.doctype.reports_dashboard.summary_of_labour_welfare_fund_deduction_report.download'
			var args = 'start_date=%(start_date)s&end_date=%(end_date)s'
		}
		if (frm.doc.reports == 'Summary of PT Deduction Report') {
			var path = 'tsi.tsinterseats.doctype.reports_dashboard.summary_of_pt_deduction_report.download'
			var args = 'start_date=%(start_date)s&end_date=%(end_date)s'
		}
		if (frm.doc.reports == 'Summary for Journal Voucher') {
			var path = 'tsi.tsinterseats.doctype.reports_dashboard.summary_for_journal_voucher.download'
			var args = 'start_date=%(start_date)s&end_date=%(end_date)s'
		}
		if (frm.doc.reports == 'Cost Center Allocation') {
			var path = 'tsi.tsinterseats.doctype.reports_dashboard.cost_center_allocation.download'
			var args = 'start_date=%(start_date)s&end_date=%(end_date)s'
		}
		if (frm.doc.reports == 'Workers Salary - Allocation to Cost Center Report') {
			var path = 'tsi.tsinterseats.doctype.reports_dashboard.worker_salary_allocation_to_cost_center_report.download'
			var args = 'start_date=%(start_date)s&end_date=%(end_date)s'
		}
		if (frm.doc.reports == 'Staff Salary - Allocation to Cost Center Report') {
			var path = 'tsi.tsinterseats.doctype.reports_dashboard.staff_salary_allocation_to_cost_center_report.download'
			var args = 'start_date=%(start_date)s&end_date=%(end_date)s'
		}
		else if (frm.doc.reports == 'Bulk Salary Slip Report') {
			if(frm.doc.start_date && frm.doc.end_date){
			frappe.call({
				method:"tsi.tsinterseats.doctype.reports_dashboard.bulk_salary_slip_report.enqueue_download_multi_pdf",
				args:{
					doctype:"Salary Slip",
					category:frm.doc.category,
					start_date: frm.doc.start_date,
					end_date: frm.doc.end_date		
				},
				callback(r){
					if(r){
						console.log(r)
					}
				}
			})
			}
		}
		if (path) {
			window.location.href = repl(frappe.request.url +
				'?cmd=%(cmd)s&%(args)s', {
				cmd: path,
				args: args,
				start_date : frm.doc.start_date,
				end_date : frm.doc.end_date,
			});
		}
		if(frm.doc.reports == 'Salary Summary Register'){
			frappe.call({
				method : 'tsi.tsinterseats.doctype.reports_dashboard.salary_summary_register.download',
				args : {
					start_date : frm.doc.start_date,
					end_date : frm.doc.end_date,
					department: frm.doc.department,
					category : frm.doc.category
				}
			})
		}

		if(frm.doc.reports == 'Attendance Register'){
			frappe.call({
				method : 'tsi.tsinterseats.doctype.reports_dashboard.attendance_register.download',
				args : {
					start_date : frm.doc.start_date,
					end_date : frm.doc.end_date,
					department: frm.doc.department
				}
			})
		}
		if(frm.doc.reports == 'Monthly In/Out Report'){
			frappe.call({
				method : 'tsi.tsinterseats.doctype.reports_dashboard.monthly_in_out_report.download',
				args : {
					start_date : frm.doc.start_date,
					end_date : frm.doc.end_date,
					employee: frm.doc.employee
				}
			})
			
		}
		if(frm.doc.reports == 'Staff Salary Register'){
			frappe.call({
				method : 'tsi.tsinterseats.doctype.reports_dashboard.staff_salary_register.download',
				args : {
					start_date : frm.doc.start_date,
					end_date : frm.doc.end_date,
					department: frm.doc.department,
					category : frm.doc.category
				}
			})
		}
		if(frm.doc.reports == 'Worker Salary Register'){
			frappe.call({
				method : 'tsi.tsinterseats.doctype.reports_dashboard.worker_salary_register.download',
				args : {
					start_date : frm.doc.start_date,
					end_date : frm.doc.end_date,
					department: frm.doc.department,
					category : frm.doc.category
				}
			})
		}
		if(frm.doc.reports == 'Monthly Salary Register'){
			frappe.call({
				method : 'tsi.tsinterseats.doctype.reports_dashboard.monthly_salary_register.download',
				args : {
					start_date : frm.doc.start_date,
					end_date : frm.doc.end_date,
					department: frm.doc.department,
					category : frm.doc.category
				}
			})
		}

		// var path = "tsi.tsinterseats.doctype.reports_dashboard.attendance_register.download"
		// var args = 'start_date=%(start_date)s&end_date=%(end_date)s&department=%(department)s'
		// if(path){
		// 	window.location.href = repl(frappe.request.url+
		// 		'?cmd=%(cmd)s&%(args)s',{
		// 			cmd:path,
		// 			args:args,
		// 			start_date:frm.doc.start_date,
		// 			end_date:frm.doc.end_date,
		// 			department:frm.doc.department
					

		// 		}
		// 	)
		// }
		
	}
});
