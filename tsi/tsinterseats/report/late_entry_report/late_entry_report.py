# Copyright (c) 2013, teampro and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from six import string_types
import frappe
import json
import datetime
from datetime import datetime
from frappe.utils import (getdate, cint, add_months, date_diff, add_days,
	nowdate, get_datetime_str, cstr, get_datetime, now_datetime, format_datetime,format_date)
from calendar import monthrange
from frappe import _, msgprint
from frappe.utils import flt
from frappe.utils import cstr, cint, getdate
from itertools import count
# import pandas as pd
import datetime as dt
from datetime import datetime, timedelta


def execute(filters=None):
	data = []
	columns = get_columns()
	attendance = get_attendance(filters)
	for att in attendance:
		data.append(att)
	return columns, data

def get_columns():
	columns = [
		_("Attendance Date") + ":Data:150",
		_("Employee") + ":Data:120",
		_("Employee Name") + ":Data:150",
		_("Shift") + ":Data:100",
		_("Shift Time") + ":Data:120",
		_("In Time") + ":Data:170",
		_("Late Time") + ":Data:170",
	]
	return columns

def get_attendance(filters):
	data = []
	if filters.employee:
		attendance = frappe.db.sql("""select attendance_date, employee, employee_name, shift, in_time from `tabAttendance` where attendance_date between %(from_date)s and %(to_date)s and employee = %(employee)s and shift != '' and in_time is not null order by attendance_date,employee ASC""",{"from_date":filters.from_date,"to_date":filters.to_date,"employee":filters.employee},as_dict = True)
	else:
		attendance = frappe.db.sql("""select attendance_date, employee, employee_name, shift, in_time from `tabAttendance` where attendance_date between %(from_date)s and %(to_date)s and shift != '' and in_time is not null order by attendance_date,employee ASC""",{"from_date":filters.from_date,"to_date":filters.to_date},as_dict = True)
	shift_map = {d.name: d.start_time for d in frappe.get_all("Shift Type", fields=["name", "start_time"])}
	for att in attendance:
		if att.shift and att.in_time:
			shift_time = shift_map.get(att.shift)
			if not shift_time:
				continue
			get_time = datetime.strptime(str(shift_time),'%H:%M:%S').strftime('%H:%M:%S')
			shift_start_time = dt.datetime.strptime(str(get_time),"%H:%M:%S")
			start_time = dt.datetime.combine(att.attendance_date,shift_start_time.time())
			st_time = start_time.strftime('%H:%M:%S')
			at_time = att.in_time.strftime('%H:%M:%S')
			if att.in_time > start_time:
				late_time = att.in_time - start_time
				row = [
				format_date(att.attendance_date),
				att.employee,
				att.employee_name,
				att.shift,
				st_time,
				at_time,
				late_time]
				data.append(row)

	return data