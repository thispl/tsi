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
def update_att(doc,method):
    # attendance will be updated every time when checkin is updated
    print("HI")
    if doc.attendance != '' and doc.log_type == "IN":
        print("HI")
        if frappe.db.exists("Attendance",{'name':doc.attendance}):
            att = frappe.get_doc("Attendance",{'name':doc.attendance})
            att.in_time = doc.time
            att.save(ignore_permissions=True)
            frappe.db.commit()
    elif doc.attendance != '' and doc.log_type == "OUT":
        print("HI")
        if frappe.db.exists("Attendance",{'name':doc.attendance}):
            att = frappe.get_doc("Attendance",{'name':doc.attendance})
            att.out_time = doc.time
            att.save(ignore_permissions=True)
            frappe.db.commit()
    if frappe.db.exists("Attendance",{'name':doc.attendance}):
        att = frappe.get_doc('Attendance',{'name':doc.attendance})
        if att.shift and att.in_time and att.out_time :
            if att.on_duty_application != "":
                if att.in_time and att.out_time:
                    in_time = att.in_time
                    out_time = att.out_time
            else:
                if att.session_from_time and att.session_to_time: 
                    in_time = att.session_from_time
                    out_time = att.session_to_time
            att_wh = time_diff_in_hours(out_time,in_time)
            ly = frappe.get_value("Late Entry",{'employee':att.employee,'permission_date':att.attendance_date,'docstatus':('!=','2')},['late']) or 0
            et = frappe.get_value("Early Out",{'employee':att.employee,'permission_date':att.attendance_date,'docstatus':('!=','2')},['out']) or 0
            tot = ly + et
            tot_lyet = tot/60
            wh = float(att_wh) + float(tot_lyet)
            decimal_hours = wh
            hours, remainder = divmod(decimal_hours, 1)
            minutes, seconds = divmod(remainder * 3600, 60)
            time_str = f"{int(hours)} hours and {int(minutes)} minutes and {int(seconds)} seconds"
            time_in_standard_format = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            frappe.db.set_value('Attendance', att.name, 'total_working_hours', time_in_standard_format)
            frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
            if wh < 4:
                frappe.db.set_value('Attendance',att.name,'status','Absent')
            elif wh >= 4 and wh < 8:
                frappe.db.set_value('Attendance',att.name,'status','Half Day')
            elif wh >= 8:
                frappe.db.set_value('Attendance',att.name,'status','Present')  
            shift_st = frappe.get_value("Shift Type",{'name':att.shift},['start_time'])
            shift_et = frappe.get_value("Shift Type",{'name':att.shift},['end_time'])
            if att.shift in ["I","II","G"]:
                shift_tot = time_diff_in_hours(shift_et,shift_st)
            elif att.shift == 'III':
                shift_tot = 8.0
            elif att.shift == 'N':
                shift_tot = 8.5
            ot_hours = time(0,0,0)
            shift_hours = frappe.get_value("Shift Type",{'name':att.shift},['total_working_hours'])
            hours, minutes, seconds = map(int, time_in_standard_format.split(':'))
            time_in_standard_format_timedelta = timedelta(hours=hours, minutes=minutes, seconds=seconds)
            hh = check_holiday(att.attendance_date,att.employee)
            if not hh:
                if wh > shift_tot and time_in_standard_format_timedelta > shift_hours:
                    print("HI")
                    extra_hours_float = wh -  shift_tot 
                    extra_hours = time_in_standard_format_timedelta - shift_hours
                    time_diff = datetime.strptime(str(extra_hours), '%H:%M:%S').time()
                    frappe.db.set_value('Attendance',att.name,'extra_hours',extra_hours_float)
                    frappe.db.set_value('Attendance',att.name,'total_extra_hours',time_diff)
                    if time_diff.hour >= 1 :
                        if time_diff.minute <= 29:
                            ot_hours = time(time_diff.hour,0,0)
                        else:
                            ot_hours = time(time_diff.hour,30,0)
                    elif time_diff.hour == 0 :
                        if time_diff.minute <= 29:
                            ot_hours = time(0,0,0)
                        else:
                            ot_hours = time(time_diff.hour,30,0)
                    ftr = [3600,60,1]
                    hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                    ot_hr = round(hr/3600,1)
                    frappe.db.set_value('Attendance',att.name,'total_overtime_hours',ot_hours)
                    frappe.db.set_value('Attendance',att.name,'overtime_hours',ot_hr)
                else:
                    frappe.db.set_value('Attendance',att.name,'extra_hours',"0.0")
                    frappe.db.set_value('Attendance',att.name,'total_extra_hours',"00:00:00")
                    frappe.db.set_value('Attendance',att.name,'total_overtime_hours',"00:00:00")
                    frappe.db.set_value('Attendance',att.name,'overtime_hours',"0.0")
            else:
                print("HII")
                extra_hours_float = wh  
                extra_hours = time_in_standard_format_timedelta 
                time_diff = datetime.strptime(str(extra_hours), '%H:%M:%S').time()
                print(att.name)
                print(extra_hours)
                frappe.db.set_value('Attendance',att.name,'extra_hours',extra_hours_float)
                frappe.db.set_value('Attendance',att.name,'total_extra_hours',time_diff)
                if time_diff.hour >= 1 :
                    if time_diff.minute <= 29:
                        ot_hours = time(time_diff.hour,0,0)
                    else:
                        ot_hours = time(time_diff.hour,30,0)
                elif time_diff.hour == 0 :
                    if time_diff.minute <= 29:
                        ot_hours = time(0,0,0)
                    else:
                        ot_hours = time(time_diff.hour,30,0)
                ftr = [3600,60,1]
                hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                ot_hr = round(hr/3600,1)
                frappe.db.set_value('Attendance',att.name,'total_overtime_hours',ot_hours)
                frappe.db.set_value('Attendance',att.name,'overtime_hours',ot_hr)
        else:
            frappe.db.set_value('Attendance', att.name,'total_working_hours',"00:00:00")
            frappe.db.set_value('Attendance', att.name,'working_hours',"0.0")
            frappe.db.set_value('Attendance',att.name,'extra_hours',"0.0")
            frappe.db.set_value('Attendance',att.name,'total_extra_hours',"00:00:00")
            frappe.db.set_value('Attendance',att.name,'total_overtime_hours',"00:00:00")
            frappe.db.set_value('Attendance',att.name,'overtime_hours',"0.0")


def check_holiday(date, emp):
    # method returns the holiday with it's short code, used to check that day is holiday or not
    holiday_list = frappe.db.get_value('Employee', {'name': emp}, 'holiday_list')
    holiday = frappe.db.sql("""select `tabHoliday`.holiday_date, `tabHoliday`.weekly_off ,`tabHoliday`.others
                             from `tabHoliday List` 
                             left join `tabHoliday` on `tabHoliday`.parent = `tabHoliday List`.name 
                             where `tabHoliday List`.name = %s and holiday_date = %s""", 
                             (holiday_list, date), as_dict=True)
    doj = frappe.db.get_value("Employee", {'name': emp}, "date_of_joining")
    status = ''

    if holiday:
        
        if doj < holiday[0].holiday_date:
            if holiday[0].weekly_off == 1:
                status = "WW"
            else:
                status = holiday[0].others
        else:
            status = 'Not Joined'
        
    return status