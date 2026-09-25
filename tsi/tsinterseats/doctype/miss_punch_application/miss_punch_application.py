# Copyright (c) 2023, Abdulla P I and contributors
# For license information, please see license.txt


import frappe
from frappe.model.document import Document
import frappe
from frappe.utils import add_days, getdate
import frappe
from frappe.utils import date_diff, getdate,get_datetime

status_map = {
	"Present": "P",
	"Absent": "A",
	"Half Day": "HD",
	"On Leave":"On Leave",
	"Work From Home": "WFH",
	"Holiday": "HH",
	"Weekly Off": "WW",
	"Leave Without Pay": "LOP",
	"Casual Leave": "CL",
	"Earned Leave": "EL",
	"ESI Leave": "ESI",
	"Compensatory Off": "C-OFF",
}

class MissPunchApplication(Document):

	def on_submit(self):
		# actual in and out will be reflected to the attendance
		att = frappe.db.exists('Attendance',{'attendance_date':self.date,'employee':self.employee,'docstatus':('!=',2)})
		if att:
			frappe.errprint("Hello")
			attendance = frappe.get_doc("Attendance",{'attendance_date':self.date,'employee':self.employee,'docstatus':('!=',2)})
	
			# attendance.in_time = self.in_punch
			# attendance.out_time = self.out_punch
			# attendance.shift = self.shift
			# attendance.status ="Present"
			# attendance.miss_punch_marked = self.name
			# Sample datetime strings
			in_p = str(self.in_punch)
			out_p = str(self.out_punch)
			frappe.db.set_value("Attendance",attendance.name,"in_time",self.in_punch)
			frappe.db.set_value("Attendance",attendance.name,"out_time",self.out_punch)
			frappe.db.set_value("Attendance",attendance.name,"shift",self.shift)
			frappe.db.set_value("Attendance",attendance.name,"status","Present")
			frappe.db.set_value("Attendance",attendance.name,"miss_punch_marked",self.name)
			
			# Convert datetime strings to Python datetime objects
			datetime1 = get_datetime(in_p)
			datetime2 = get_datetime(out_p)

			# Calculate time difference
			time_difference = datetime2 - datetime1

			hours, remainder = divmod(time_difference.total_seconds(), 3600)
			minutes, seconds = divmod(remainder, 60)

			# Format the time difference as "HH:MM:SS"
			formatted_time_difference = "{:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds))

			time_str = formatted_time_difference  # Replace with your actual time string

			# Split the time string into hours, minutes, and seconds
			hours, minutes, seconds = map(int, time_str.split(':'))

			# Convert the time to a float
			time_in_float = hours + minutes/60 + seconds/3600

			attendance.total_working_hours = formatted_time_difference
			attendance.working_hours = time_in_float
			status = status_map.get(attendance.status, "")
			leave = status_map.get(attendance.leave_type, "")
			hh = check_holiday(attendance.attendance_date,attendance.employee)
			if hh:
				if status == "P" and attendance.shift == "N":
					if hh == "WW" or "PH" or "FH" or "BH":
						ss = "PN/" + hh
					if hh == "DH":
						ss = "PN/" + hh
				if status == "P" and not attendance.shift == "N":
					if hh == "WW" or "PH" or "FH" or "BH":
						ss = "P/" + hh
					if hh == "DH":
						ss = "P/" + hh
			else:
				if status == "P" and attendance.shift == "N":
					ss = "P/N"
				if status == "P" and not attendance.shift == "N":
					ss = "P"
			if status == "A":
				hh = check_holiday(attendance.attendance_date,attendance.employee)
				if hh:
					ss = hh
				else:
					ss = "AB"
			if status == "HD" and leave != '':
				ss = "PP/" + leave
			if status == "HD" and leave == '':
				hh = check_holiday(attendance.attendance_date,attendance.employee)
				if hh:
					if hh == "WW" or "PH" or "FH" or "BH":
						ss = "HD/" + hh
					if hh == "DH":
						ss = "HD/" + hh
				else:
					ss = "HD/-" 
			if status == "On Leave" and leave != '':
				ss = leave
			if status == "On Leave" and leave == '':
				ss = "On Leave"
			attendance.shift_status = ss
			# attendance.save(ignore_permissions=True)

			frappe.db.commit()
	def on_cancel(self):
		if frappe.db.exists("Attendance",{'attendance_date':self.date,'employee':self.employee,'miss_punch_marked':self.name}):
			att=frappe.get_doc("Attendance",{'attendance_date':self.date,'employee':self.employee,'miss_punch_marked':self.name})
			frappe.db.set_value("Attendance",att.name,"miss_punch_marked",'')
def check_holiday(date, emp):
	holiday_list = frappe.db.get_value('Employee', {'name': emp}, 'holiday_list')
	holiday = frappe.db.sql("""select `tabHoliday`.holiday_date, `tabHoliday`.weekly_off ,`tabHoliday`.others
							from `tabHoliday List` 
							left join `tabHoliday` on `tabHoliday`.parent = `tabHoliday List`.name 
							where `tabHoliday List`.name = %s and holiday_date = %s""", 
							(holiday_list, date), as_dict=True)
	doj = frappe.db.get_value("Employee", {'name': emp}, "date_of_joining")
	status = ''

	if holiday:
		if doj < holiday[0].holiday_date:
			if holiday[0].weekly_off == 1:
				status = "WW"
			else:
				status = holiday[0].others
		else:
			status = 'Not Joined'
		
	return status

			