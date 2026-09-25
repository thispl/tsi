# Copyright (c) 2024, Abdulla P I and contributors
# For license information, please see license.txt

import frappe
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
    attendance = get_late(filters)
    for att in attendance:
        data.append(att)
    return columns, data

def get_columns():
    columns = [
        _("Employee") + ":Data:120",
        _("Employee Name") + ":Data:150",
        _("Department") + ":Data:170",
        _("Designation") + ":Data:170",
        _("Late Count") + ":Data:170",
        _("Late Time") + ":Data:170",

    ]
    return columns

def get_late(filters):
    data = []
    late_entry = []    
    if filters.employee and not filters.department:
        query = """SELECT MIN(permission_date) as permission_date, employee 
                    FROM `tabLate Entry` 
                    WHERE permission_date BETWEEN '%s' AND '%s' 
                    AND employee = '%s' 
                    AND docstatus = 1 
                    GROUP BY employee 
                    ORDER BY permission_date""" % (filters.from_date, filters.to_date, filters.employee)

    elif not filters.employee and filters.department:
        query = """SELECT MIN(permission_date) as permission_date, employee 
                    FROM `tabLate Entry` 
                    WHERE permission_date BETWEEN '%s' AND '%s' 
                    AND department = '%s' 
                    AND workflow_state = 'Approved' 
                    GROUP BY employee 
                    ORDER BY permission_date""" % (filters.from_date, filters.to_date, filters.department)

    elif filters.employee and filters.department:
        query = """SELECT MIN(permission_date) as permission_date, employee 
                    FROM `tabLate Entry` 
                    WHERE permission_date BETWEEN '%s' AND '%s' 
                    AND employee = '%s' 
                    AND department = '%s' 
                    AND workflow_state = 'Approved' 
                    GROUP BY employee 
                    ORDER BY permission_date""" % (filters.from_date, filters.to_date, filters.employee, filters.department)

    else:
        query = """SELECT MIN(permission_date) as permission_date, employee 
                    FROM `tabLate Entry` 
                    WHERE permission_date BETWEEN '%s' AND '%s' 
                    AND workflow_state = 'Approved' 
                    GROUP BY employee 
                    ORDER BY permission_date""" % (filters.from_date, filters.to_date)


    late_entry = frappe.db.sql(query, as_dict=True)
    frappe.errprint(late_entry)
    for la in late_entry:
        tot = 0
        count = frappe.db.count("Late Entry", {
            'employee': la.employee,
            'permission_date': ['Between', (filters.from_date, filters.to_date)],
            'workflow_state': 'Approved'
        })
        emp_name = frappe.db.get_value("Employee", {'name': la.employee}, ['employee_name'])
        desig = frappe.db.get_value("Employee", {'name': la.employee}, ['designation'])
        dep = frappe.db.get_value("Employee", {'name': la.employee}, ['department'])
        ltime = frappe.db.get_all("Late Entry", {
            'employee': la.employee,
            'permission_date': ['Between', (filters.from_date, filters.to_date)],
            'workflow_state': 'Approved'
        }, ['*'])
        for l in ltime:
            tot += int(l.late)  
        row = [la.employee, emp_name, dep, desig, count, tot]    
        data.append(row)
    
    return data
