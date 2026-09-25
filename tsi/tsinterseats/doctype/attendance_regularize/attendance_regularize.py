# Copyright (c) 2025, Abdulla P I and contributors
# For license information, please see license.txt

# import frappe
from __future__ import unicode_literals
from email import message
import re
from frappe import _
import frappe
from frappe.model.document import Document
from datetime import date, timedelta, datetime,time
from frappe.utils import (getdate, cint, add_months, date_diff, add_days,

	nowdate, get_datetime_str, cstr, get_datetime, now_datetime, format_datetime,today, format_date)
# import pandas as pd
import math
from frappe.utils import add_months, cint, flt, getdate, time_diff_in_hours
import datetime as dt
from datetime import datetime, timedelta
from tsi.mark_attendance import update_att_with_employee

class AttendanceRegularize(Document):
    # def on_cancel(self):
    #     if frappe.db.exists("Attendance", self.attendance_marked):

    #         # Clear regularization link
    #         frappe.db.set_value("Attendance", self.attendance_marked, "attendance_regularize", "")
    #         ot_id = frappe.db.get_value("Attendance", self.attendance_marked, "overtime_request")
    #         ot_id1 = frappe.db.get_value("Attendance", self.attendance_marked, "*", as_dict=True)
    #         att_data = frappe.db.get_value("Attendance", self.attendance_marked, "*", as_dict=True)
    #         # 🔧 in_time test (Remove or use this safely if needed)
    #         in_time = None
    #         if in_time:
    #             print(in_time.time())
    #         else:
    #             print("in_time is None")  # Debug message, remove in production

    #         # Reset shift/in/out/ot fields only if no backup exists (use blank string if not available)
    #         if not self.attendance_shift:
    #             frappe.db.set_value("Attendance", self.attendance_marked, "shift","")
    #         if not self.first_in_time:
    #             frappe.db.set_value("Attendance", self.attendance_marked, "in_time", self.first_in_time or None)
    #         if not self.last_out_time:
    #             frappe.db.set_value("Attendance", self.attendance_marked, "out_time", self.last_out_time or None)
    #         if not self.extra_time and not self.extra_time == '00:00:00':
    #             frappe.db.set_value("Attendance", self.attendance_marked, "total_overtime_hours", self.extra_time or '00:00:00')
    #             frappe.db.set_value("Attendance", self.attendance_marked, "overtime_hours", self.extra_time or '0.000')
    #             if att_data.overtime_hours and float(att_data.overtime_hours) < 0.5:
    #                 frappe.db.set_value("Attendance", self.attendance_marked, "overtime_request", "")
    #                 if frappe.db.exists("Overtime Request",{ot_id1.attendance:att_data.name}):
    #                     frappe.delete_doc("Overtime Request", ot_id)
    #             frappe.db.set_value("Attendance", self.attendance_marked, "overtime_request", self.extra_time or ' ')

    #         if self.attendance_shift:
    #             frappe.db.set_value("Attendance", self.attendance_marked, "shift", self.attendance_shift)
    #         if self.first_in_time:
    #             frappe.db.set_value("Attendance", self.attendance_marked, "in_time", self.first_in_time)
    #         if self.last_out_time:
    #             frappe.db.set_value("Attendance", self.attendance_marked, "out_time", self.last_out_time)
    #         if self.extra_time:
    #             frappe.db.set_value("Attendance", self.attendance_marked, "total_overtime_hours", self.extra_time)
    #         # Update calculations
                     

    #         if ot_id:
    #             # Sync Attendance values to OT Request
    #             frappe.db.set_value("Overtime Request", ot_id, "from_time", att_data.in_time)
    #             frappe.db.set_value("Overtime Request", ot_id, "to_time", att_data.out_time)
    #             frappe.db.set_value("Overtime Request", ot_id, "biometric_checkin", att_data.in_time)
    #             frappe.db.set_value("Overtime Request", ot_id, "biometric_checkinout", att_data.out_time)
    #             frappe.db.set_value("Overtime Request", ot_id, "ot_hours", att_data.overtime_hours)
    #             frappe.db.set_value("Overtime Request", ot_id, "total_worked_hours", att_data.total_working_hours)
    #             frappe.db.set_value("Overtime Request", ot_id, "shift", att_data.shift)

    #         # If OT hours < 0.5, remove link & delete OT
    #         if att_data.overtime_hours and float(att_data.overtime_hours) < 0.5:
    #             frappe.db.set_value("Attendance", self.attendance_marked, "overtime_request", "")
    #             if ot_id:
    #                 frappe.delete_doc("Overtime Request", ot_id)
    #         update_att_with_employee(self.attendance_date, self.attendance_date, self.employee)   
    def on_cancel(self):
        if frappe.db.exists("Attendance", self.attendance_marked):
            frappe.db.set_value("Attendance", self.attendance_marked, "attendance_regularize", "")
            update_att_with_employee(self.attendance_date,self.attendance_date,self.employee)
            
            if self.attendance_shift:
                frappe.db.set_value("Attendance", self.attendance_marked, "shift", self.attendance_shift)
            if self.first_in_time:
                frappe.db.set_value("Attendance", self.attendance_marked, "in_time", self.first_in_time)
            if self.last_out_time:
                frappe.db.set_value("Attendance", self.attendance_marked, "out_time", self.last_out_time)
            if self.extra_time:
                frappe.db.set_value("Attendance", self.attendance_marked, "total_overtime_hours", self.extra_time)

            if not self.attendance_shift:
                frappe.db.set_value("Attendance", self.attendance_marked, "shift","")
            if not self.first_in_time:
                frappe.db.set_value("Attendance", self.attendance_marked, "in_time", self.first_in_time or None)
            if not self.last_out_time:
                frappe.db.set_value("Attendance", self.attendance_marked, "out_time", self.last_out_time or None)
            if ( not self.extra_time and not self.extra_time == '00:00:00'):
                frappe.db.set_value("Attendance", self.attendance_marked, "total_overtime_hours", self.extra_time or '00:00:00')
                frappe.db.set_value("Attendance", self.attendance_marked, "overtime_hours", self.extra_time or '0.000')
                frappe.db.set_value("Attendance", self.attendance_marked, "total_working_hours", '00:00:00')
                frappe.db.set_value("Attendance", self.attendance_marked, "working_hours", '0.0')
                frappe.db.set_value("Attendance", self.attendance_marked, "extra_hours", '0.000')
                frappe.db.set_value("Attendance", self.attendance_marked, "total_extra_hours", '00:00:00')

            # ot_id = frappe.db.get_value("Attendance", self.attendance_marked, "overtime_request")
            att_data = frappe.db.get_value("Attendance", self.attendance_marked, "*", as_dict=True)
            ot_id = att_data.overtime_request

            # if att_data.overtime_request:
            #     frappe.db.set_value("Overtime Request", ot_id, "from_time", att_data.in_time)
            #     frappe.db.set_value("Overtime Request", ot_id, "to_time", att_data.out_time)
            #     frappe.db.set_value("Overtime Request", ot_id, "biometric_checkin", att_data.in_time)
            #     frappe.db.set_value("Overtime Request", ot_id, "biometric_checkinout", att_data.out_time)
            #     frappe.db.set_value("Overtime Request", ot_id, "ot_hours", att_data.overtime_hours)
            #     frappe.db.set_value("Overtime Request", ot_id, "total_worked_hours", att_data.total_working_hours)
            #     frappe.db.set_value("Overtime Request", ot_id, "shift", att_data.shift)

            # if att_data.overtime_hours < 0.5:
            #     frappe.db.set_value("Attendance", self.attendance_marked, "overtime_request", "")
            #     if ot_id:
            #         frappe.delete_doc("Overtime Request", ot_id)

            if ot_id:
                if att_data.overtime_hours < 0.5:
                    frappe.db.set_value("Attendance", self.attendance_marked, "overtime_request", "")
                    frappe.delete_doc("Overtime Request", ot_id)
                else:
                    # Update Overtime Request with restored Attendance values
                    frappe.db.set_value("Overtime Request", ot_id, "from_time", att_data.in_time)
                    frappe.db.set_value("Overtime Request", ot_id, "to_time", att_data.out_time)
                    frappe.db.set_value("Overtime Request", ot_id, "biometric_checkin", att_data.in_time)
                    frappe.db.set_value("Overtime Request", ot_id, "biometric_checkinout", att_data.out_time)
                    frappe.db.set_value("Overtime Request", ot_id, "ot_hours", att_data.overtime_hours)
                    frappe.db.set_value("Overtime Request", ot_id, "total_worked_hours", att_data.total_working_hours)
                    frappe.db.set_value("Overtime Request", ot_id, "shift", att_data.shift)
            
                # if att_data.overtime_hours =='0.000' and att_data.overtime_request:
                #     # frappe.db.set_value("Attendance", self.attendance_marked, "overtime_request", "")
                #     # if ot_id:
                #     frappe.errprint("HI1")
                #     frappe.delete_doc("Overtime Request", att_data.overtime_request)
                #     frappe.errprint("HI2")
                #     frappe.db.set_value("Attendance", self.attendance_marked, "overtime_request", self.extra_time or ' ')    
            # if ot_id:
            #     frappe.db.set_value("Overtime Request", ot_id, "from_time", att_data.in_time)
            #     frappe.db.set_value("Overtime Request", ot_id, "to_time", att_data.out_time)
            #     frappe.db.set_value("Overtime Request", ot_id, "biometric_checkin", att_data.in_time)
            #     frappe.db.set_value("Overtime Request", ot_id, "biometric_checkinout", att_data.out_time)
            #     frappe.db.set_value("Overtime Request", ot_id, "ot_hours", att_data.overtime_hours)
            #     frappe.db.set_value("Overtime Request", ot_id, "total_worked_hours", att_data.total_working_hours)
            #     frappe.db.set_value("Overtime Request", ot_id, "shift", att_data.shift)

            # if att_data.overtime_hours < 0.5:
            #     frappe.db.set_value("Attendance", self.attendance_marked, "overtime_request", "")
            #     if ot_id:
            #         frappe.delete_doc("Overtime Request", ot_id)


    def on_submit(self):
        if frappe.db.exists("Attendance", self.attendance_marked):
            # att_data = frappe.db.get_value(
            #     "Attendance", self.attendance_marked,
            #     ["shift", "in_time", "out_time", "total_overtime_hours"],
            #     as_dict=True
            # )

            # self.attendance_shift = att_data.shift
            # self.first_in_time = att_data.in_time
            # self.last_out_time = att_data.out_time    
            # self.extra_time = att_data.total_overtime_hours

            # self.db_update()  # save to DB

            # Update with corrected values
            frappe.db.set_value("Attendance", self.attendance_marked, "attendance_regularize", self.name)
            if self.corrected_shift:
                frappe.db.set_value("Attendance", self.attendance_marked, "shift", self.corrected_shift)
            if self.corrected_in:
                frappe.db.set_value("Attendance", self.attendance_marked, "in_time", self.corrected_in)
            if self.corrected_out:
                frappe.db.set_value("Attendance", self.attendance_marked, "out_time", self.corrected_out)
            if self.corrected_ot:
                frappe.db.set_value("Attendance", self.attendance_marked, "total_overtime_hours", self.corrected_ot)

            update_att_with_employee(self.attendance_date, self.attendance_date, self.employee)

        # def on_cancel(self):
        # 	if frappe.db.exists("Attendance", self.attendance_marked):
        # 		frappe.db.set_value("Attendance", self.attendance_marked, "attendance_regularize", "")
        # 		update_att_with_employee(self.attendance_date,self.attendance_date,self.employee)
        # 		ot_id = frappe.db.get_value("Attendance", self.attendance_marked, "overtime_request")
        # 		att_data = frappe.db.get_value("Attendance", self.attendance_marked, "*", as_dict=True)

        # 		if ot_id:
        # 			frappe.db.set_value("Overtime Request", ot_id, "from_time", att_data.in_time)
        # 			frappe.db.set_value("Overtime Request", ot_id, "to_time", att_data.out_time)
        # 			frappe.db.set_value("Overtime Request", ot_id, "biometric_checkin", att_data.in_time)
        # 			frappe.db.set_value("Overtime Request", ot_id, "biometric_checkinout", att_data.out_time)
        # 			frappe.db.set_value("Overtime Request", ot_id, "ot_hours", att_data.overtime_hours)
        # 			frappe.db.set_value("Overtime Request", ot_id, "total_worked_hours", att_data.total_working_hours)
        # 			frappe.db.set_value("Overtime Request", ot_id, "shift", att_data.shift)

        # 		if att_data.overtime_hours < 0.5:
        # 			frappe.db.set_value("Attendance", self.attendance_marked, "overtime_request", "")
        # 			if ot_id:
        # 				frappe.delete_doc("Overtime Request", ot_id)


        # 		# if self.attendance_shift:
        # 		#     frappe.db.set_value("Attendance", self.attendance_marked, "shift", self.attendance_shift)
        # 		# if self.first_in_time:
        # 		#     frappe.db.set_value("Attendance", self.attendance_marked, "in_time", self.first_in_time)
        # 		# if self.last_out_time:
        # 		#     frappe.db.set_value("Attendance", self.attendance_marked, "out_time", self.last_out_time)
        # 		# if self.extra_time:
        # 		#     frappe.db.set_value("Attendance", self.attendance_marked, "total_overtime_hours", self.extra_time)
        # def on_submit(self):
        # 	if frappe.db.exists("Attendance", self.attendance_marked):
        # 		frappe.db.set_value("Attendance", self.attendance_marked, "attendance_regularize", self.name)
        # 		if self.corrected_shift:
        # 			frappe.db.set_value("Attendance", self.attendance_marked, "shift", self.corrected_shift)
        # 		if self.corrected_in:
        # 			frappe.db.set_value("Attendance", self.attendance_marked, "in_time", self.corrected_in)
        # 		if self.corrected_out:
        # 			frappe.db.set_value("Attendance", self.attendance_marked, "out_time", self.corrected_out)
        # 		if self.corrected_ot:
        # 			frappe.db.set_value("Attendance", self.attendance_marked, "total_overtime_hours", self.corrected_ot)
        # 		update_att_with_employee(self.attendance_date,self.attendance_date,self.employee)


				


@frappe.whitelist()
def get_assigned_shift_details(emp,att_date):
	datalist = []
	data = {}
	assigned_shift = frappe.get_value("Employee",{'name':emp},['default_shift'])
	if assigned_shift != '':
		shift_in_time = frappe.db.get_value('Shift Type',{'name':assigned_shift},['start_time'])
		shift_out_time = frappe.db.get_value('Shift Type',{'name':assigned_shift},['end_time'])
	else:
		shift_in_time = ''
		shift_out_time = ''
	if frappe.db.exists('Attendance',{'employee':emp,'attendance_date':att_date,'docstatus':("!=",2)}):
		if frappe.db.get_value('Attendance',{'employee':emp,'attendance_date':att_date,'docstatus':("!=",2)},['in_time']):
			first_in_time = frappe.db.get_value('Attendance',{'employee':emp,'attendance_date':att_date,'docstatus':("!=",2)},['in_time'])
		else:
			first_in_time = '' 
		if frappe.db.get_value('Attendance',{'employee':emp,'attendance_date':att_date,'docstatus':("!=",2)},['out_time']):
			last_out_time = frappe.db.get_value('Attendance',{'employee':emp,'attendance_date':att_date,'docstatus':("!=",2)},['out_time'])  
		else:
			last_out_time = ''
		if frappe.db.get_value('Attendance',{'employee':emp,'attendance_date':att_date,'docstatus':("!=",2)},['total_overtime_hours']):
			ot_hrs = frappe.db.get_value('Attendance',{'employee':emp,'attendance_date':att_date,'docstatus':("!=",2)},['total_overtime_hours'])  
		else:
			ot_hrs = '00:00:00'
		if frappe.db.get_value('Attendance',{'employee':emp,'attendance_date':att_date,'docstatus':("!=",2)},['shift']):
			attendance_shift = frappe.db.get_value('Attendance',{'employee':emp,'attendance_date':att_date,'docstatus':("!=",2)},['shift'])   
		else:
			attendance_shift = ''
		attendance_marked = frappe.db.get_value('Attendance',{'employee':emp,'attendance_date':att_date,'docstatus':("!=",2)},['name'])
		data.update({
			'assigned_shift':assigned_shift or '',
			'shift_in_time':shift_in_time or '00:00:00',
			'shift_out_time':shift_out_time or '00:00:00',
			'attendance_shift':attendance_shift or '',
			'first_in_time':first_in_time,
			'last_out_time':last_out_time,
			'attendance_marked':attendance_marked,
			'ot_hrs':ot_hrs
		})
		datalist.append(data.copy())
		return datalist	 
	else:
		frappe.throw(_("Attendance not Marked"))


@frappe.whitelist()
def validate_attendance_regularize_duplication(employee,att_date,docstatus):
	exisiting=frappe.db.exists("Attendance Regularize",{'employee':employee,'attendance_date':att_date,'docstatus':('!=',2)})
	if exisiting:
		return "Already Applied"		


# @frappe.whitelist()
# def set_attendance_regularize_application(att_id):
#     reg = frappe.get_doc("Attendance Regularize", {"attendance_marked": att_id})
#     if reg:
#         if frappe.db.exists("Attendance", reg.attendance_marked):
# 			# frappe.db.set_value("Attendance", reg.attendance_marked, "attendance_regularize", reg.name)
#             if reg.corrected_shift:
#                 frappe.db.set_value("Attendance", reg.attendance_marked, "shift", reg.corrected_shift)

#             if reg.corrected_in:
#                 frappe.db.set_value("Attendance", reg.attendance_marked, "in_time", reg.corrected_in)

#             if reg.corrected_out:
#                 frappe.db.set_value("Attendance", reg.attendance_marked, "out_time", reg.corrected_out)

#             if reg.corrected_ot:
#                 frappe.db.set_value("Attendance", reg.attendance_marked, "total_overtime_hours", reg.corrected_ot)
			
@frappe.whitelist()
def set_attendance_regularize_application(att_id):
	reg = frappe.get_doc("Attendance Regularize", {"attendance_marked": att_id})
	
	if reg and frappe.db.exists("Attendance", reg.attendance_marked):
		frappe.db.set_value("Attendance", reg.attendance_marked, "attendance_regularize", reg.name)

		if reg.corrected_shift:
			frappe.db.set_value("Attendance", reg.attendance_marked, "shift", reg.corrected_shift)

		if reg.corrected_in:
			frappe.db.set_value("Attendance", reg.attendance_marked, "in_time", reg.corrected_in)

		if reg.corrected_out:
			frappe.db.set_value("Attendance", reg.attendance_marked, "out_time", reg.corrected_out)

		if reg.corrected_ot:
			frappe.db.set_value("Attendance", reg.attendance_marked, "total_overtime_hours", reg.corrected_ot)
			
			
						
