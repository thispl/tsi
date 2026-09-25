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
def validate_compensatory_leave_duration(work_from_date):
    # method to restrict applying comp off request after 30 from actual date
    date_string = work_from_date
    dt = datetime.strptime(date_string,'%Y-%m-%d').date()
    today = datetime.today().date()
    c_off = add_months(today,-1)
    if c_off < today:
         frappe.throw(_("Compensatory leave cannot be applied after 1 month from the work from date"))
    

