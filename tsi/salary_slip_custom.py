import frappe
from frappe.model.document import Document
from frappe.utils import time_diff
from datetime import datetime
from datetime import timedelta
import pdfkit
from frappe.utils import getdate
from datetime import date
from frappe.utils.data import get_datetime
from tsi.mark_attendance import att_shift_status_with_employee
from frappe import throw,_
from frappe.utils import (
    add_days,
    add_months,
    cint,
    date_diff,
    flt,
    get_first_day,
    get_last_day,
    get_link_to_form,
    getdate,
    rounded,
    today,
)

@frappe.whitelist()
def update_shift_days(employee, from_date, to_date):
    # method returns the count of night shift in salary slip when employees from plastic injection department 
    att = frappe.db.sql("""
        SELECT name 
        FROM `tabAttendance` 
        WHERE employee = %s 
            AND attendance_date BETWEEN %s AND %s 
            AND shift_status = 'P/N'
    """, (employee, from_date, to_date), as_dict=True)

    count = len(att)
    return count