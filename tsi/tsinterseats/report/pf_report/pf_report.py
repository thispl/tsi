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
	row = []
	salary_slips = frappe.db.sql("""select * from `tabSalary Slip` where start_date between '%s' and '%s' and docstatus!=2"""%(filters.start_date, filters.end_date), as_dict=True)
	i = 1
	for ss in salary_slips:
		emp_id = ss.employee
		emp_name = ss.employee_name
		dep= ss.department
		ac = ss.bank_account_no
		sal = ss.gross_pay
		pf = frappe.get_value('Salary Detail',{'salary_component':"PF",'parent':ss.name},["amount"] or 0)
		row = [i,emp_id or "-",emp_name or "-",dep or "-",ac or "-",sal or 0,pf or 0]
		data.append(row)
		i+=1
	return data
