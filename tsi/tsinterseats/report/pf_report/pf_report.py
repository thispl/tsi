# Copyright (c) 2023, Abdulla P I and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from datetime import datetime
from calendar import monthrange
from frappe import _, msgprint
from frappe.utils import flt

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
    columns = [
        _("S.No") + ":Data/:60",
        _("Employee") + ":Data:150",
        _("Employee Name") + ":Data:150",
        _("Department") + ":Data:150",
		_("Bank Account Number") + ":Data:180",
		_("Gross Pay") + ":Data:120",
		_("PF") + ":Data:150",
    ]
    return columns

def get_data(filters):
	data = []
	salary_slips = frappe.db.sql("""SELECT ss.employee, ss.employee_name, ss.department, ss.bank_account_no,
			ss.gross_pay, IFNULL(SUM(sd.amount), 0) AS pf
		FROM `tabSalary Slip` ss
		LEFT JOIN `tabSalary Detail` sd
			ON sd.parent = ss.name
			AND sd.parenttype = 'Salary Slip'
			AND sd.salary_component = 'PF'
		WHERE ss.start_date BETWEEN %(start_date)s AND %(end_date)s
			AND ss.docstatus != 2
		GROUP BY ss.name
		ORDER BY ss.name""",
		{"start_date": filters.start_date, "end_date": filters.end_date},
		as_dict=True)
	i = 1
	for ss in salary_slips:
		emp_id = ss.employee
		emp_name = ss.employee_name
		dep = ss.department
		ac = ss.bank_account_no
		sal = ss.gross_pay
		pf = ss.pf
		row = [i, emp_id or "-", emp_name or "-", dep or "-", ac or "-", sal or 0, pf or 0]
		data.append(row)
		i += 1
	return data
