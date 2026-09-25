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
from frappe.utils import time_diff
from dateutil.relativedelta import relativedelta
from datetime import datetime
from frappe.utils import get_first_day, get_last_day, format_datetime,get_url_to_form,today
from frappe.utils.data import ceil, get_time, get_year_start
import json
import datetime
from frappe.utils import (getdate, cint, add_months, date_diff, add_days,
    nowdate, get_datetime_str, cstr, get_datetime, now_datetime, format_datetime)
from datetime import datetime
from calendar import monthrange
from frappe import _, msgprint
from frappe.utils import flt
from frappe.utils import cstr, cint, getdate,get_first_day, get_last_day, today, time_diff_in_hours
import requests
from datetime import date, timedelta,time
from frappe.utils import get_url_to_form
import math
import dateutil.relativedelta
from datetime import timedelta, datetime
from frappe.utils import cstr, add_days, date_diff,format_datetime
from hrms.hr.utils import get_holidays_for_employee
import re



import frappe
@frappe.whitelist()
def validate_overtime_reason_before_submit(doc, method):
    if doc.workflow_state == "L1 Pending" and not doc.reason:
        frappe.throw("Please enter a Job/Work before sending to Level 1 Approver.")
    if doc.reason and doc.workflow_state == "L1 Pending":
        doc.workflow_state = "L1 Pending"
