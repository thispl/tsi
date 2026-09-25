// Copyright (c) 2023, Abdulla P I and contributors
// For license information, please see license.txt

frappe.ui.form.on('Overtime Request', {
	// refresh: function(frm) {

	// }
	validate(frm){
		if (frm.doc.ot_from_od == 1){
			frm.set_df_property('od_date', 'reqd', 1)
		if (!frm.doc.on_duty_application){
			frappe.validated = false
			frappe.msgprint('On Duty Application is not found.');
		}
		
	}
	},
	setup: function(frm) {
		frm.set_query('on_duty_application', () => {
		   return {
			   filters: {
				   "docstatus": 1
			   }
		   }
	   })
	  
	
   },
	ot_hour(frm){
		if (frm.doc.ot_hours){
			frm.set_value("ot_hours", frm.doc.ot_hours+frm.doc.ot_hour);
			}
		else{
			var ot_hour = frm.doc.ot_hour;
			frm.set_value("ot_hours", ot_hour);
			
		}


	},
	od_date(frm){
		if (frm.doc.od_date && frm.doc.ot_from_od==1 && frm.doc.employee){
			frm.set_value('ot_date',frm.doc.od_date)
				frappe.call({
					'method':'tsi.tsinterseats.doctype.overtime_request.overtime_request.on_duty_application',
					'args':{
						employee: frm.doc.employee,
						od_date:frm.doc.od_date
					},
					callback(r){
						if (r.message) {
							console.log(r.message)
							frm.set_value("on_duty_application", r.message[0]);
							frm.set_value("session_from_time", r.message[1]);
							frm.set_value("session_to_time", r.message[2]);
							// frm.set_value("ot_hour", r.message[3]);
							frm.set_df_property('ot_date', 'reqd', 0)
							frm.set_value("from_time", '00:00:00');
							frm.set_value("to_time", '00:00:00');
							frm.set_value("total_worked_hours", '00:00:00');
							frm.set_df_property('from_time', 'hidden', 1)
							frm.set_df_property('to_time', 'hidden', 1)
							frm.set_df_property('total_worked_hours', 'hidden', 1)
	
						
						}
						else{
							frappe.msgprint('On Duty Application is not found.');
							frappe.validated = false
						}
					}
				})
		}
	},
	ot_from_od(frm){
		if (frm.doc.ot_from_od==1){
		frm.set_value('ot_date',frm.doc.od_date)
		if(frm.doc.employee && frm.doc.od_date){
			frappe.call({
				'method':'tsi.tsinterseats.doctype.overtime_request.overtime_request.on_duty_application',
				'args':{
					employee: frm.doc.employee,
					od_date:frm.doc.od_date
				},
				callback(r){
					if (r.message) {
						console.log(r.message)
						frm.set_value("on_duty_application", r.message[0]);
						frm.set_value("session_from_time", r.message[1]);
						frm.set_value("session_to_time", r.message[2]);
						// frm.set_value("ot_hour", r.message[3]);
						frm.set_df_property('ot_date', 'reqd', 0)
						frm.set_value("from_time", '00:00:00');
						frm.set_value("to_time", '00:00:00');
						frm.set_value("total_worked_hours", '00:00:00');
						frm.set_df_property('from_time', 'hidden', 1)
						frm.set_df_property('to_time', 'hidden', 1)
						frm.set_df_property('total_worked_hours', 'hidden', 1)

					
					}
					else{
						frappe.msgprint('On Duty Application is not found.');
						frappe.validated = false
					}
				}
			})
		}

	}
	else{
		frm.set_value("on_duty_application", '');
	}
	}
});
