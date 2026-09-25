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
def get_casual_leaves(doc,method):
    if doc.leave_type == "Casual Leave":
        # method to restrict the casual leave applications only 3 per month
        if isinstance(doc.from_date, str):
            doc.from_date = datetime.strptime(doc.from_date, "%Y-%m-%d").date()
        if doc.from_date.day < 26:
            month_start = (doc.from_date - relativedelta(months=1)).replace(day=26)
            month_end = doc.from_date.replace(day=25)
        else:
            month_start = doc.from_date.replace(day=26)
            month_end = (doc.from_date + relativedelta(months=1)).replace(day=25)
        # month_start=get_first_day(doc.from_date)
        # month_end=get_last_day(doc.to_date)
        cl_applications=frappe.get_all(
            "Leave Application",
            filters={
                'employee':doc.employee,
                'from_date':('between',[month_start,month_end]),
                'to_date':('between',[month_start,month_end]),
                'leave_type':'Casual Leave',
                'name':('!=',doc.name),
                'workflow_state':('!=','Cancelled')
            },
            fields=['total_leave_days'])
        total_cl=sum([i['total_leave_days'] for i in cl_applications])
        total_cl+=doc.total_leave_days
        if total_cl >3:
            frappe.throw("3 Casual Leaves only allowed per month.")
       
        
@frappe.whitelist()
def cl_el_restriction(doc,method):
    # method to restrict the EL and CL application before or after sunday
    if doc.leave_type=='Earned Leave' or doc.leave_type=='Casual Leave':
            sdate = getdate(doc.from_date)
            edate = getdate(doc.to_date)
            before_check = sdate.weekday()
            after_check = edate.weekday()
            if before_check==0:
                frappe.errprint('before')
                prev_day = frappe.utils.add_days(sdate, -2)
                frappe.errprint(prev_day)
                if frappe.db.exists('Leave Application', {'employee': doc.employee,'to_date':prev_day,'leave_type': doc.leave_type,'docstatus': ('!=', 2)}):
                    frappe.throw("Already another Leave Application found on Saturday.")
            elif after_check==5:
                frappe.errprint('After')
                next_day = frappe.utils.add_days(edate, 2)
                frappe.errprint(next_day)
                if frappe.db.exists('Leave Application', {'employee': doc.employee,'from_date':next_day,'leave_type': doc.leave_type,'docstatus': ('!=', 2)}):
                    frappe.throw("Already another Leave Application found on Monday.")


@frappe.whitelist()
def el_restriction(doc, method):
    # Get the start and end of the year for the leave application
    start_date=getdate(doc.from_date)
    year_start = date(start_date.year, 1, 1)
    year_end = date(start_date.year, 12, 31)

    # Query to check the number of Earned Leave applications for the employee in the current year
    leave_count = frappe.db.sql("""
        SELECT COUNT(*) AS count
        FROM `tabLeave Application`
        WHERE docstatus != 2
        AND employee = %s
        AND leave_type = 'Earned Leave'
        AND (
            (from_date BETWEEN %s AND %s) 
            OR (to_date BETWEEN %s AND %s) 
            OR (from_date <= %s AND to_date >= %s)
        )
    """, (doc.employee, year_start, year_end, year_start, year_end, year_start, year_end), as_dict=True)

    # Get the leave count
    leave_count = leave_count[0].get('count', 0)

    # Restrict if more than 3 Earned Leave applications exist
    if leave_count > 3:
        frappe.throw("Only 3 earned leave applications are allowed per year.")


@frappe.whitelist()
def validate_leave_application(employee, from_date, to_date):
    try:
        leave_type_list = ['Casual Leave', 'Compensatory Off']
        
        existing_leave_applications = frappe.get_all(
            'Leave Application',
            filters={
                'employee': employee,
                'leave_type': ('in', leave_type_list),
                'from_date': ('<=', to_date),
                'to_date': ('>=', from_date)
            },
        )
        
        if existing_leave_applications:
            frappe.throw("An overlapping leave application already exists with Casual Leave or Compensatory Off type.")

    except Exception as e:
        frappe.log_error(f"Error in validate_leave_application: {str(e)}")
        raise


@frappe.whitelist()
def check_earn_lve(to_date):
    date = add_days(to_date,2)
    if today() > date:
        frappe.throw("you have exceed the two days of grace period")

@frappe.whitelist()
def check_earn_leave(frm_date):
    date = add_days(frm_date,-15)
    if not today() <= date:
        frappe.throw("Earned leave must be applied before 15 days of the leave date")

import frappe
from frappe import _
@frappe.whitelist()
def leave_days_count(doc):
    # method used to return the total no of leaves days in salary slip
    leave = frappe.db.sql("""
        SELECT sum(total_leave_days) as leave_days
        FROM `tabLeave Application`
        WHERE employee = %s 
            AND from_date <= %s 
            AND to_date >= %s
            AND leave_type NOT IN ('Leave Without Pay', 'ESI Leave')
            AND status = 'Approved'
    """, (doc.employee, doc.end_date, doc.start_date), as_dict=True)
    
    return leave[0].leave_days or 0

