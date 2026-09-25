// Copyright (c) 2023, Abdulla P I and contributors
// For license information, please see license.txt

frappe.ui.form.on('Attendance Settings', {
	refresh:function(frm){
		frm.disable_save()
	},
	process_checkins(frm){
		if (frm.doc.employee){
			console.log("HI")
			frappe.call({
				"method": "tsi.mark_attendance.get_urc_to_ec",
				"args":{
					"from_date" : frm.doc.from_date,
					"to_date": frm.doc.to_date,
					"employee": frm.doc.employee 
				},
				freeze: true,
				freeze_message: 'Processing UnRegistered Employee Checkin to Employee Checkin....',
				callback(r){
					console.log(r.message)
					if(r.message == "ok"){
						frappe.msgprint("Checkins are created Successfully")
					}
				}
			})
		}
		else{
			console.log("HII")
			frappe.call({
				"method": "tsi.mark_attendance.get_urc_to_ec_without_employee",
				"args":{
					"from_date" : frm.doc.from_date,
					"to_date": frm.doc.to_date 
				},
				freeze: true,
				freeze_message: 'Processing UnRegistered Employee Checkin to Employee Checkin....',
				callback(r){
					console.log(r.message)
					if(r.message == "ok"){
						frappe.msgprint("Checkins are created Successfully")
					}
				}
			})
		}
	},
	process_attendance(frm){
		if (frm.doc.employee){
			// console.log("HI")
			frappe.call({
				"method": "tsi.mark_attendance.update_att_with_employee",
				"args":{
					"from_date" : frm.doc.from_date,
					"to_date": frm.doc.to_date,
					"employee": frm.doc.employee 
				},
				freeze: true,
				freeze_message: 'Processing Attendance....',
				callback(r){
					// console.log(r.message)
					if(r.message == "ok"){
						frappe.msgprint("Attendance are created Successfully")
					}
				}
			})
		}
		else{
			console.log("HII")
			frappe.call({
				"method": "tsi.mark_attendance.update_att_without_employee",
				"args":{
					"from_date" : frm.doc.from_date,
					"to_date": frm.doc.to_date 
				},
				freeze: true,
				freeze_message: 'Processing Attendance....',
				callback(r){
					console.log(r.message)
					if(r.message == "ok"){
						frappe.msgprint("Attendance are created Successfully")
					}
				}
			})
		}
	},
	submit_attendance(frm){
		if (frm.doc.employee){
			frappe.call({
				"method": "tsi.mark_attendance.att_draft_to_submit_with_employee",
				"args": {
					"from_date": frm.doc.from_date,
					"to_date": frm.doc.to_date,
					"employee": frm.doc.employee
				},
				freeze: true,
				freeze_message: "Submitting...",
				callback(r){
					if(r.message == 'ok'){
						frappe.msgprint("Attendance Submitted Successfully")
					}
				}
			})
		}
		else{
			frappe.call({
				"method": "tsi.mark_attendance.att_draft_to_submit_without_employee",
				"args": {
					"from_date": frm.doc.from_date,
					"to_date": frm.doc.to_date
				},
				freeze: true,
				freeze_message: "Submitting...",
				callback(r){
					if(r.message == "ok"){
						frappe.msgprint("Attendance Submitted Successfully")
					}
				}
			})
		}
	}
});
