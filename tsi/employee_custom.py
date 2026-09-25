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

@frappe.whitelist()
def inactive_employee(doc,method):
    # throw error when relieving date is set for active employees
    if doc.status=="Active":
        if doc.relieving_date:
            throw(_("Please remove the relieving date for the Active Employee."))




@frappe.whitelist()
def update_relieving_date():
    # updates the status as left and relieving date in employee MIS
    rf=frappe.db.get_all("Resignation Form",{"docstatus":1},['*'])
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    formatted_date = yesterday.strftime("%Y-%m-%d")
    for i in rf:
        if str(i.relieving_date) == formatted_date:
            value=frappe.get_all("Employee",["status","employee_name"])
            for j in value:
                if i.employee_name==j.employee_name:
                    frappe.db.set_value("Employee","name","status","Left")
                    frappe.db.set_value("Employee","name","relieving_date",i.relieving_date)

