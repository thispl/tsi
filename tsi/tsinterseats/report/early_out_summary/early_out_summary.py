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
    attendance = get_early(filters)
    for att in attendance:
        data.append(att)
    return columns, data

def get_columns():
    columns = [
        _("Employee") + ":Data:120",
        _("Employee Name") + ":Data:150",
        _("Department") + ":Data:170",
        _("Designation") + ":Data:170",
        _("Early Out Count") + ":Data:170",
        _("Early Out Time") + ":Data:170",

    ]
    return columns

def get_early(filters):
    data = []
    params = {"from_date": filters.from_date, "to_date": filters.to_date}
    if filters.employee and not filters.department:
        cond = "AND employee = %(employee)s AND docstatus = 1"
        params["employee"] = filters.employee
    elif not filters.employee and filters.department:
        cond = "AND department = %(department)s AND workflow_state = 'Approved'"
        params["department"] = filters.department
    elif filters.employee and filters.department:
        cond = "AND employee = %(employee)s AND department = %(department)s AND workflow_state = 'Approved'"
        params["employee"] = filters.employee
        params["department"] = filters.department
    else:
        cond = "AND workflow_state = 'Approved'"

    early_out = frappe.db.sql(
        """SELECT MIN(permission_date) as permission_date, employee
        FROM `tabEarly Out`
        WHERE permission_date BETWEEN %(from_date)s AND %(to_date)s {cond}
        GROUP BY employee
        ORDER BY permission_date""".format(cond=cond),
        params, as_dict=True)

    stats = {}
    for r in frappe.db.sql(
        """SELECT employee, COUNT(*) as cnt, SUM(`out`) as tot
        FROM `tabEarly Out`
        WHERE permission_date BETWEEN %(from_date)s AND %(to_date)s
            AND workflow_state = 'Approved'
            AND employee IN %(emps)s
        GROUP BY employee""",
        {"from_date": filters.from_date, "to_date": filters.to_date,
         "emps": tuple(ea.employee for ea in early_out) or ("",)},
        as_dict=True):
        stats[r.employee] = r

    emp_map = {e.name: e for e in frappe.get_all("Employee",
        filters={"name": ("in", [ea.employee for ea in early_out])},
        fields=["name", "employee_name", "designation", "department"])} if early_out else {}

    for ea in early_out:
        s = stats.get(ea.employee)
        emp = emp_map.get(ea.employee, frappe._dict())
        count = s.cnt if s else 0
        tot = s.tot if s and s.tot else 0
        row = [ea.employee, emp.get("employee_name"), emp.get("department"), emp.get("designation"), count, tot]
        data.append(row)

    return data

