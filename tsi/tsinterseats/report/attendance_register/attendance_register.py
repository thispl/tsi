# Copyright (c) 2023, Abdulla P I and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from functools import total_ordering
from itertools import count
import frappe
from frappe import permissions
from frappe.utils import cstr, cint, getdate, get_last_day, get_first_day, add_days
from frappe.utils import cstr, add_days, date_diff, getdate, format_date
from math import floor
from frappe import msgprint, _
from calendar import month, monthrange
from datetime import date, timedelta, datetime,time


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	columns = []
	columns += [
		_("Employee ID") + ":Data/:150",
		_("Employee Name") + ":Data/:200",
		_("Department") + ":Data/:150",
	]
	dates = get_dates(filters)
	for date in dates:
		date = datetime.strptime(date,'%Y-%m-%d')
		day = datetime.date(date).strftime('%d')
		month = datetime.date(date).strftime('%b')
		columns.append(_(day) + ":Data/:70")
	columns.append(_("Total Days") + ":Data/:100")
	columns.append(_("Present Days") + ":Data/:100")
	columns.append(_('BH') +':Data/:100')
	columns.append(_("DH") + ":Data/:100")
	columns.append(_("PH")+ ':Data/:100')
	columns.append(_("FH")+ ':Data/:100')
	columns.append(_("WH")+ ':Data/:100')
	columns.append(_("CL")+ ':Data/:100')
	columns.append(_("EL")+ ':Data/:100')
	columns.append(_("ESI")+ ':Data/:100')
	columns.append(_("SA")+ ':Data/:100')
	columns.append(_("Loss Of Pay")+ ':Data/:100')
	columns.append(_("Total Paid Days")+ ':Data/:100')
	columns.append(_("Remarks")+ ':Data/:100')
	return columns

def get_data(filters):
	data = []
	row = []
	employees = get_employees(filters)
	dates = get_dates(filters)

	emp_names = [e.name for e in employees]
	holiday_lists = tuple({e.holiday_list for e in employees if e.holiday_list})

	attendance_map = {}
	holiday_map = {}
	if emp_names:
		for a in frappe.db.sql(
			"""
			SELECT employee, attendance_date, shift_status
			FROM `tabAttendance`
			WHERE docstatus != 2
			  AND attendance_date BETWEEN %(start_date)s AND %(end_date)s
			  AND employee IN %(emp_names)s
			ORDER BY docstatus DESC, modified DESC
			""",
			{"start_date": filters.start_date, "end_date": filters.end_date, "emp_names": tuple(emp_names)},
			as_dict=True,
		):
			attendance_map.setdefault((a.employee, getdate(a.attendance_date)), a.shift_status)

	if holiday_lists:
		for h in frappe.db.sql(
			"""
			SELECT parent, holiday_date, weekly_off, others
			FROM `tabHoliday`
			WHERE parent IN %(holiday_lists)s
			  AND holiday_date BETWEEN %(start_date)s AND %(end_date)s
			""",
			{"holiday_lists": holiday_lists, "start_date": filters.start_date, "end_date": filters.end_date},
			as_dict=True,
		):
			holiday_map.setdefault((h.parent, getdate(h.holiday_date)), h)

	tdcnt =0 
	tpds = 0
	twh=0
	tbh=0
	tdh=0
	tph=0
	tfh=0
	tcl=0
	tel=0
	tesi=0
	tlop=0
	ttpd=0
	tsat=0
	for e in employees:
		row=[]
		row += [e.name,e.employee_name,e.department]
		cnt = 0
		pd=0
		wh=0
		bh=0
		dh=0
		ph=0
		fh=0
		cl=0
		el=0
		esi=0
		sa=0
		lop=0
		tpd=0

		for date in dates:
			date_obj = getdate(date)
			if (e.name, date_obj) in attendance_map:
				att = attendance_map[(e.name, date_obj)]
				if att:
					row.append(att)
					if att =="P":
						pd += 1
						# cell.font = Font(bold=True,size=14)
					elif att == "P/N":
						pd +=1
						sa +=1
					elif att == "P/AB":
						pd +=0.5
					elif att == "DH/P":
						pd +=1
					elif att == "DH/PN":
						pd +=1
					elif att == "DH/PP":
						pd +=0.5
					elif att == "CL":
						cl +=1
					elif att == "PP/CL":
						cl +=0.5
						pd +=0.5
					elif att == "EL":
						el +=1
					elif att == "P/EL":
						el +=0.5
						pd +=0.5
					elif att == "ESI":
						esi +=1
					elif att == "LOP":
						lop +=1

				else:
					row.append('-')
			else:
				hh = check_holiday(date_obj,e,holiday_map)
				row.append(hh)
				if hh == "WH":
					wh+=1
				elif hh == "BH":
					bh +=1
				elif hh == "DH":
					dh +=1
				elif hh == "PH":
					ph +=1
				elif hh == "FH":
					fh +=1
			cnt += 1
		row.append(cnt)
		row.append(pd)
		row.append(bh)
		row.append(dh)
		row.append(ph)
		row.append(fh)
		row.append(wh)
		row.append(cl)
		row.append(el)
		row.append(esi)
		tsa = sa*60
		row.append(tsa)
		row.append(lop)
		tpd=pd+bh+dh+ph+fh+wh+cl+el
		row.append(tpd)
		row.append("")
		data.append(row)
		tdcnt +=cnt
		tpds +=pd
		tbh +=bh
		tdh +=dh
		tph +=ph
		tfh +=fh
		twh +=wh
		tcl +=cl
		tel +=el
		tesi +=esi
		tsat +=tsa
		tlop +=lop
		ttpd +=tpd

	row1 = ['','','']
	dates = get_dates(filters)
	for date in dates:
		row1.extend([''])

	row1.append(tdcnt)
	row1.append(tpds)
	row1.append(tbh)
	row1.append(tdh)
	row1.append(tph)
	row1.append(tfh)
	row1.append(twh)
	row1.append(tcl)
	row1.append(tel)
	row1.append(tesi)
	row1.append(tsat)
	row1.append(tlop)
	row1.append(ttpd)
	row1.append('')
	data.append(row1)
	return data

def get_dates(filters):
	no_of_days = date_diff(add_days(filters['end_date'], 1), filters['start_date'])
	dates = [add_days(filters['start_date'], i) for i in range(0, no_of_days)]
	return dates

def check_holiday(date_obj,e,holiday_map):
	holiday = holiday_map.get((e.holiday_list, date_obj))
	doj = e.date_of_joining
	status = ''
	if holiday :
		if doj < holiday.holiday_date:
			if holiday.weekly_off == 1:
				status = "WH"     
			else:
				if holiday.others == "DH":
					status = "DH"
				elif holiday.others == "BH":
					status = "BH"
				elif holiday.others == "PH":
					status = "PH"
				elif holiday.others == "FH":
					status = "FH"
		else:
			status = '*'
	return status

def get_employees(filters):
	conditions = ''
	if filters.employee:
		conditions += "and name = '%s' " % (filters.employee)
	if filters.department:
		conditions += "and department = '%s' "%(filters.department)
	if filters.employee_catagory:
		conditions += "and employee_catagory = '%s' " %(filters.employee_catagory)
	employees = frappe.db.sql("""select * from `tabEmployee` where status = 'Active' %s order by name ASC""" % (conditions), as_dict=True)
	return employees