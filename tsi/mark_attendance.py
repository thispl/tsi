from __future__ import print_function
from pickle import TRUE
from time import strptime
from traceback import print_tb
import frappe
from frappe.utils.data import ceil, get_time, get_year_start
# import pandas as pd
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
from datetime import datetime, timedelta
from frappe.utils import get_url_to_form
import math
import dateutil.relativedelta
import datetime as dt
from datetime import datetime, timedelta

status_map = {
    "Present": "P",
    "Absent": "A",
    "Half Day": "HD",
    "On Leave":"On Leave",
    "Work From Home": "WFH",
    "Holiday": "HH",
    "Weekly Off": "WW",
    "Leave Without Pay": "LOP",
    "Casual Leave": "CL",
    "Earned Leave": "EL",
    "Sick Leave": "SL",
    "ESI Leave": "ESI",
    "Compensatory Off": "C-OFF",
}

@frappe.whitelist()
def mark_att_multidate():
    from_date = '2025-01-01'
    to_date = '2025-01-03'
    checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where date(time) between '%s' and '%s' order by time ASC """%(from_date,to_date),as_dict=True)
    for c in checkins:
        employee = frappe.db.exists('Employee',{'status':'Active','date_of_joining':['<=',from_date],'name':c.employee})
        if employee:
            att = mark_attendance_from_checkin(c.employee,c.time,c.log_type)
            if att:
                frappe.db.set_value("Employee Checkin",c.name, "skip_auto_attendance", "1")
    mark_absent(from_date,to_date)
    mark_wh_ot(from_date,to_date)  
    ot_without_break(from_date,to_date) 
    mark_late_early(from_date,to_date) 
    att_shift_status(from_date,to_date)
    mark_att_present(from_date,to_date)
    # mark_cc(from_date,to_date) 
    return "OK"
@frappe.whitelist()
def mark_canteen_coupons():
    from_date = add_days(today(),-1)  
    to_date = today()
    dates = get_dates(from_date,to_date)
    for date in dates:
        from_date = add_days(date,0)
        to_date = date
        mark_cc(from_date,to_date)
    return "ok" 

@frappe.whitelist()
def mark_att_process():
    from_date = add_days(today(),-1)  
    to_date = today() 
    # from_date='2025-01-01'
    # to_date='2025-01-02'
    dates = get_dates(from_date,to_date)
    for date in dates:
        from_date = add_days(date,0)
        to_date = date
        mark_att(from_date,to_date)
    return "ok" 

def get_dates(from_date,to_date):
    no_of_days = date_diff(add_days(to_date, 1), from_date)
    dates = [add_days(from_date, i) for i in range(0, no_of_days)]
    return dates

@frappe.whitelist()
def mark_att(from_date,to_date):
    checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where date(time) between '%s' and '%s' order by time ASC """%(from_date,to_date),as_dict=True)
    for c in checkins:
        print(c.name)
        employee = frappe.db.exists('Employee',{'status':'Active','date_of_joining':['<=',from_date]})
        if employee:
            att = mark_attendance_from_checkin(c.employee,c.time,c.log_type)
            if att:
                frappe.db.set_value("Employee Checkin",c.name, "skip_auto_attendance", "1")
    mark_absent(from_date,to_date)
    mark_wh_ot(from_date,to_date)
    ot_without_break(from_date,to_date)  
    mark_late_early(from_date,to_date)
    att_shift_status(from_date,to_date)
    mark_att_present(from_date,to_date)
    create_npd_allowance_att(from_date,to_date)
    add_ot_from_od(from_date,to_date)
    update_ot_hrs(from_date,to_date)
    # mark_cc(from_date,to_date) 
    update_leave_attendance_status(from_date, to_date)
 

@frappe.whitelist()
def mark_att_testing():
    from_date = '2026-08-06'
    to_date = '2026-08-07'
    checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where date(time) between '%s' and '%s' order by time ASC """%(from_date,to_date),as_dict=True)
    for c in checkins:
        employee = frappe.db.exists('Employee',{'status':'Active','date_of_joining':['<=',from_date]})
        if employee:
            att = mark_attendance_from_checkin(c.employee,c.time,c.log_type)
            if att:
                frappe.db.set_value("Employee Checkin",c.name, "skip_auto_attendance", "1")
    mark_absent(from_date,to_date)
    mark_wh_ot(from_date,to_date)
    ot_without_break(from_date,to_date)  
    mark_late_early(from_date,to_date)
    att_shift_status(from_date,to_date)
    mark_att_present(from_date,to_date)
    create_npd_allowance_att(from_date,to_date)
    add_ot_from_od(from_date,to_date)
    update_ot_hrs(from_date,to_date)

@frappe.whitelist()
def mark_attendance_from_checkin(employee,time,log_type):
    att_date = time.date()
    att_time = time.time()
    shift = ''
    if log_type == 'IN':   
        att = frappe.db.exists('Attendance',{"employee":employee,'attendance_date':att_date,'docstatus':['!=','2']})   
        checkins = frappe.db.sql(""" select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'IN' and date(time) = '%s' order by time ASC"""%(employee,att_date),as_dict=True)
        if checkins:
            if not att:
                att = frappe.new_doc("Attendance")
                att.employee = employee
                att.attendance_date = att_date
                att.shift = get_checkin_shift(checkins[0].time,employee)
                att.status = 'Absent'
                if len(checkins) > 0:
                    att.in_time = checkins[0].time
                else:
                    att.in_time = checkins[0].time
                att.total_working_hours = "00:00:00"
                att.working_hours = "0.0"
                att.extra_hours = "0.0"
                att.total_extra_hours = "00:00:00"
                att.total_overtime_hours = "00:00:00"
                att.early_exit_hours = "00:00:00"
                att.late_entry_hours = "00:00:00"
                att.overtime_hours = "0.0"
                
                att.save(ignore_permissions=True)
                frappe.db.commit()
                for c in checkins:
                    frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                    frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                return att  
            else:
                att = frappe.get_doc("Attendance",att)
                if att.docstatus != 2:
                    att.employee = employee
                    att.attendance_date = att_date
                    att.status = 'Absent'
                    att.shift = get_checkin_shift(checkins[0].time,employee)
                    if len(checkins) > 0:
                        att.in_time = checkins[0].time
                    else:
                        att.in_time = checkins[0].time
                    if att.attendance_regularize and att.attendance_regularize is not None:
                        if frappe.db.exists("Attendance Regularize",{'name':att.attendance_regularize,'in_time':1}):
                            reg_in=frappe.db.get_value("Attendance Regularize",{'name':att.attendance_regularize,'in_time':1},['corrected_in'])
                            att.in_time =reg_in
                    if att.attendance_regularize and att.attendance_regularize is not None:
                            if frappe.db.exists("Attendance Regularize",{'name':att.attendance_regularize,'shift':1}):
                                reg_in=frappe.db.get_value("Attendance Regularize",{'name':att.attendance_regularize,'shift':1},['corrected_shift'])
                                att.shift =reg_in        
                    att.total_working_hours = "00:00:00"
                    att.working_hours = "0.0"
                    att.extra_hours = "0.0"
                    att.total_extra_hours = "00:00:00"
                    att.total_overtime_hours = "00:00:00"
                    att.overtime_hours = "0.0"
                    att.early_exit_hours = "00:00:00"
                    att.late_entry_hours = "00:00:00"
                    att.save(ignore_permissions=True)
                    frappe.db.commit()
                    for c in checkins:
                        frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                        frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                    
                    return att 
    if log_type == 'OUT':
        # set 10 AM as maximum out for previous day
        max_out = datetime.strptime('10:00','%H:%M').time()
        # take log  type IN before 10 AM in todayin
        todayin = frappe.db.sql("""SELECT * FROM `tabEmployee Checkin` WHERE employee = %s AND log_type = 'IN' AND DATE(time) = %s AND TIME(time) < %s AND TIME(time) < %s AND device_id != 'Canteen' ORDER BY time ASC """, (employee, att_date, max_out,att_time), as_dict=True)
        if att_time < max_out:
            
            # frappe.errprint(att_time)
            if todayin:
                # frappe.errprint("Test")
                # frappe.errprint(todayin)
                # if out is after the todayin update current day attendance
                yesterday=att_date
            else:
                # frappe.errprint("Test1")
                # if out is before the todayin update previous day attendance
                yesterday = add_days(att_date,-1)                
            checkins = frappe.db.sql("select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'OUT' and date(time) = '%s' and time(time) < '%s'order by time ASC "%(employee,att_date,max_out),as_dict=True)
            att = frappe.db.exists("Attendance",{'employee':employee,'attendance_date':yesterday})
            if att:
                att = frappe.get_doc("Attendance",att)
                if att.docstatus != 2:
                    if not att.shift:
                        if len(checkins) > 0:
                            att.shift = get_actual_shift(get_time(checkins[-1].time),employee)
                            att.out_time = checkins[-1].time
                            for c in checkins:
                                frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                                frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                        else:
                            att.shift = get_actual_shift(get_time(checkins[-1].time),employee)
                            att.out_time = checkins[-1].time
                            frappe.db.set_value('Employee Checkin',checkins[-1].name,'skip_auto_attendance','1')
                            frappe.db.set_value("Employee Checkin",checkins[-1].name, "attendance", att.name)
                    else:
                        if len(checkins) > 0:
                            att.out_time = checkins[-1].time
                            for c in checkins:
                                frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                                frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                        else:
                            att.out_time = checkins[-1].time
                            frappe.db.set_value('Employee Checkin',checkins[-1].name,'skip_auto_attendance','1')
                            frappe.db.set_value("Employee Checkin",checkins[-1].name, "attendance", att.name)
                    
                    if att.attendance_regularize and att.attendance_regularize is not None:
                        if frappe.db.exists("Attendance Regularize",{'name':att.attendance_regularize,'out_time':1}):
                            reg_in=frappe.db.get_value("Attendance Regularize",{'name':att.attendance_regularize,'out_time':1},['corrected_out'])
                            att.out_time =reg_in
                    if att.attendance_regularize and att.attendance_regularize is not None:
                        if frappe.db.exists("Attendance Regularize",{'name':att.attendance_regularize,'shift':1}):
                            reg_in=frappe.db.get_value("Attendance Regularize",{'name':att.attendance_regularize,'shift':1},['corrected_shift'])
                            att.shift =reg_in    
                    att.save(ignore_permissions=True)
                    frappe.db.commit()
                    return att
                    
            else:
                att = frappe.new_doc("Attendance")
                att.employee = employee
                att.attendance_date = yesterday
                att.status = 'Absent'
                att.total_working_hours = "00:00:00"
                att.working_hours = "0.0"
                att.extra_hours = "0.0"
                att.total_extra_hours = "00:00:00"
                att.total_overtime_hours = "00:00:00"
                att.early_exit_hours = "00:00:00"
                att.late_entry_hours = "00:00:00"
                att.overtime_hours = "0.0"
                if len(checkins) > 0:
                    att.out_time = checkins[-1].time
                    att.shift = get_actual_shift(get_time(checkins[-1].time),employee)
                    for c in checkins:
                        frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                        frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                else:
                    att.out_time = checkins[-1].time
                    att.shift = get_actual_shift(get_time(checkins[-1].time),employee)
                    frappe.db.set_value('Employee Checkin',checkins[-1].name,'skip_auto_attendance','1')
                    frappe.db.set_value("Employee Checkin",checkins[-1].name, "attendance", att.name)
                att.save(ignore_permissions=True)
                frappe.db.commit()
                return att	
        else:
            # out time after 10 AM automatically taken as current day out
            checkins = frappe.db.sql("select * from `tabEmployee Checkin` where employee ='%s' and log_type = 'OUT' and date(time) = '%s' order by time ASC"%(employee,att_date),as_dict=True)
            att = frappe.db.exists("Attendance",{'employee':employee,'attendance_date':att_date})
            if att:
                att = frappe.get_doc("Attendance",att)
                if att.docstatus != 2:
                    if att.shift=='':
                        if len(checkins) > 0:
                            att.shift = get_actual_shift(get_time(checkins[-1].time),employee)
                            att.out_time = checkins[-1].time
                            for c in checkins:
                                frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                                frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                        else:
                            att.shift = get_actual_shift(get_time(checkins[-1].time),employee)
                            att.out_time = checkins[-1].time
                            frappe.db.set_value('Employee Checkin',checkins[-1].name,'skip_auto_attendance','1')
                            frappe.db.set_value("Employee Checkin",checkins[-1].name, "attendance", att.name)
                    else:
                        if len(checkins) > 0:
                            att.out_time = checkins[-1].time
                            for c in checkins:
                                frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                                frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                        else:
                            att.out_time = checkins[-1].time
                            frappe.db.set_value('Employee Checkin',checkins[-1].name,'skip_auto_attendance','1')
                            frappe.db.set_value("Employee Checkin",checkins[-1].name, "attendance", att.name)
                    if att.attendance_regularize and att.attendance_regularize is not None:
                        if frappe.db.exists("Attendance Regularize",{'name':att.attendance_regularize,'out_time':1}):
                            reg_in=frappe.db.get_value("Attendance Regularize",{'name':att.attendance_regularize,'out_time':1},['corrected_out'])
                            att.out_time =reg_in
                    if att.attendance_regularize and att.attendance_regularize is not None:
                        if frappe.db.exists("Attendance Regularize",{'name':att.attendance_regularize,'shift':1}):
                            reg_in=frappe.db.get_value("Attendance Regularize",{'name':att.attendance_regularize,'shift':1},['corrected_shift'])
                            att.shift =reg_in 
                    att.save(ignore_permissions=True)
                    frappe.db.commit()
                    return att
                    
                else:
                    if att.shift=='':
                        if len(checkins) > 0:
                            att.shift = get_actual_shift(get_time(checkins[-1].time),employee)
                            att.out_time = checkins[-1].time
                            for c in checkins:
                                frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                                frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                                
                        else:
                            att.shift = get_actual_shift(get_time(checkins[-1].time),employee)
                            att.out_time = checkins[-1].time
                            frappe.db.set_value('Employee Checkin',checkins[-1].name,'skip_auto_attendance','1')
                            frappe.db.set_value("Employee Checkin",checkins[-1].name, "attendance", att.name)
                    else:
                        if len(checkins) > 0:
                            att.out_time = checkins[-1].time
                            for c in checkins:
                                frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                                frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                        else:
                            att.out_time = checkins[-1].time
                            frappe.db.set_value('Employee Checkin',checkins[-1].name,'skip_auto_attendance','1')
                            frappe.db.set_value("Employee Checkin",checkins[-1].name, "attendance", att.name)
                    
                    if att.attendance_regularize and att.attendance_regularize is not None:
                        if frappe.db.exists("Attendance Regularize",{'name':att.attendance_regularize,'out_time':1}):
                            reg_in=frappe.db.get_value("Attendance Regularize",{'name':att.attendance_regularize,'out_time':1},['corrected_out'])
                            att.out_time =reg_in
                    if att.attendance_regularize and att.attendance_regularize is not None:
                        if frappe.db.exists("Attendance Regularize",{'name':att.attendance_regularize,'shift':1}):
                            reg_in=frappe.db.get_value("Attendance Regularize",{'name':att.attendance_regularize,'shift':1},['corrected_shift'])
                            att.shift =reg_in 
                    att.save(ignore_permissions=True)
                    frappe.db.commit()
                    return att

            else:
                att = frappe.new_doc("Attendance")
                att.employee = employee
                att.attendance_date = att_date
                att.shift = shift
                att.status = 'Absent'
                if len(checkins) > 0:
                    att.shift = get_actual_shift(get_time(checkins[-1].time),employee)
                    att.out_time = checkins[-1].time
                    for c in checkins:
                        frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                        frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                else:
                    att.shift = get_actual_shift(get_time(checkins[-1].time))
                    att.out_time = checkins[-1].time
                    frappe.db.set_value('Employee Checkin',checkins[-1].name,'skip_auto_attendance','1')
                    frappe.db.set_value("Employee Checkin",checkins[-1].name, "attendance", att.name)
                att.save(ignore_permissions=True)
                frappe.db.commit()
                return att  
@frappe.whitelist()
def get_actual_shift(get_shift_time,employee):
    # method to get the shift based on their in and out time
    from datetime import datetime
    from datetime import date, timedelta,time
    shift1 = frappe.db.get_value('Shift Type',{'name':'I'},['checkout_start_time','checkout_end_time'])
    shift2 = frappe.db.get_value('Shift Type',{'name':'II'},['checkout_start_time','checkout_end_time'])
    shift3 = frappe.db.get_value('Shift Type',{'name':'III'},['checkout_start_time','checkout_end_time'])
    shiftg = frappe.db.get_value('Shift Type',{'name':'G'},['checkout_start_time','checkout_end_time'])
    shiftn = frappe.db.get_value('Shift Type',{'name':'N'},['checkout_start_time','checkout_end_time'])
    shiftlg = frappe.db.get_value('Shift Type',{'name':'Lady Guard'},['checkout_start_time','checkout_end_time'])
    shifthk = frappe.db.get_value('Shift Type',{'name':'HK'},['checkout_start_time','checkout_end_time'])
    shiftso = frappe.db.get_value('Shift Type',{'name':'SO'},['checkout_start_time','checkout_end_time'])
    shiftseq = frappe.db.get_value('Shift Type',{'name':'SEQ'},['checkout_start_time','checkout_end_time'])
    shiftseqn = frappe.db.get_value('Shift Type',{'name':'SS-N'},['checkout_start_time','checkout_end_time'])
    shiftgar = frappe.db.get_value('Shift Type',{'name':'Gardner'},['checkout_start_time','checkout_end_time'])
    att_time_seconds = get_shift_time.hour * 3600 + get_shift_time.minute * 60 + get_shift_time.second
    shift = ''
    department = frappe.get_value("Employee",{'name':employee},["department"])
    designation = frappe.get_value("Employee",{'name':employee},["designation"])
    gender = frappe.get_value("Employee",{'name':employee},["gender"])
    if department == "HK":
        if shifthk[0].total_seconds() < att_time_seconds < shifthk[1].total_seconds():
            shift = "HK"
    elif department == "GARDENER":
        if shiftgar[0].total_seconds() < att_time_seconds < shiftgar[1].total_seconds():
            shift = "Gardner"
    elif department == "Security":
        if gender == "Female":
            if shiftlg[0].total_seconds() < att_time_seconds < shiftlg[1].total_seconds():
                shift = "Lady Guard"
        else:
            if designation=="Security Officer":
                if shiftso[0].total_seconds() < att_time_seconds < shiftso[1].total_seconds():
                    shift = 'SO'
            else:
                if shiftseqn[0].total_seconds() < att_time_seconds < shiftseqn[1].total_seconds():
                    shift = 'SS-N'
                if shiftseq[0].total_seconds() < att_time_seconds < shiftseq[1].total_seconds():
                    shift = 'SEQ'
    else:
        if shift1[0].total_seconds() < att_time_seconds < shift1[1].total_seconds():
            shift = 'I'
        if shift2[0].total_seconds() < att_time_seconds < shift2[1].total_seconds():
            shift = 'II'
        if shift3[0].total_seconds() < att_time_seconds < shift3[1].total_seconds():
            shift ='III'
        if shiftg[0].total_seconds() < att_time_seconds < shiftg[1].total_seconds():
            shift ='G'
        if shiftn[0].total_seconds() < att_time_seconds < shiftn[1].total_seconds():
            shift = 'N'
    return shift

def time_diff_in_timedelta(in_time, out_time):
    datetime_format = "%H:%M:%S"
    if out_time and in_time :
        return out_time - in_time

@frappe.whitelist()
def mark_absent(from_date,to_date):
        # for non holiday when attendance is not created from mark_attendance_from_checkin method, then it will be marked as absent 
        dates = get_dates(from_date,to_date)
        for date in dates:
            employee = frappe.db.get_all('Employee',{'status':'Active','date_of_joining':['<=',from_date]})
            for emp in employee:
                hh = check_holiday(date,emp.name)
                if not hh:
                    if not frappe.db.exists('Attendance',{'attendance_date':date,'employee':emp.name,'docstatus':('!=','2')}):
                        att = frappe.new_doc("Attendance")
                        att.employee = emp.name
                        att.status = 'Absent'
                        att.attendance_date = date
                        att.total_working_hours = "00:00:00"
                        att.late_entry_hours = "00:00:00"
                        att.early_exit_hours = "00:00:00"
                        att.working_hours = "0.0"
                        att.extra_hours = "0.0"
                        att.total_extra_hours = "00:00:00"
                        att.total_overtime_hours = "00:00:00"
                        att.overtime_hours = "0.0"
                        att.save(ignore_permissions=True)
                        frappe.db.commit()

def mark_wh_ot(from_date,to_date):
    # method to mark the attendance status
    attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'docstatus':('!=','2')},['name','shift','in_time','out_time','employee','on_duty_application','employee_name','department','designation','attendance_date','session_from_time','session_to_time','attendance_regularize'])
    od_wh=0.0
    for att in attendance:
        if (att.in_time or (att.session_from_time and att.on_duty_application)) and (att.out_time or (att.session_to_time and att.on_duty_application)) and att.shift:
            in_time = att.in_time
            out_time = att.out_time
            if att.on_duty_application is not None:
                if att.session_from_time and att.session_to_time:
                    od=frappe.get_doc("On Duty Application",att.on_duty_application)
                    if not out_time:
                        total_seconds_to = int(att.session_to_time.total_seconds())
                        hours_to, remainder = divmod(total_seconds_to, 3600)
                        minutes_to, seconds_to = divmod(remainder, 60)
                        session_to_time_as_time = datetime.time(datetime(1, 1, 1, hours_to, minutes_to, seconds_to))
                        session_to_time_as_datetime = datetime.combine(att.attendance_date, session_to_time_as_time)
                        out_time = session_to_time_as_datetime
                    else:
                        session_to_time_as_time = (datetime.min + att.session_to_time).time()
                        if out_time.time() > session_to_time_as_time:
                            out_time = att.out_time
                        else:
                            out_time = datetime.combine(out_time.date(), session_to_time_as_time)
                    # frappe.errprint("OUT PRINT")
                    # frappe.errprint(out_time)
                    if not in_time:
                        total_seconds_from = int(att.session_from_time.total_seconds())
                        hours_from, remainder = divmod(total_seconds_from, 3600)
                        minutes_from, seconds_from = divmod(remainder, 60)
                        session_from_time_as_time = datetime.time(datetime(1, 1, 1, hours_from, minutes_from, seconds_from))
                        session_from_time_as_datetime = datetime.combine(att.attendance_date, session_from_time_as_time)
                        in_time = session_from_time_as_datetime
                    else:
                        # compare actual in time and session from time, least one is taken for calculation
                        session_from_time_as_time = (datetime.min + att.session_from_time).time()
                        if in_time.time() < session_from_time_as_time:
                            in_time = att.in_time
                        else:
                            in_time = datetime.combine(in_time.date(), session_from_time_as_time)
             # if miss punch application is there, then timing from the application is taken for calculation          
            if att.miss_punch_marked is not None:
                misspunch=frappe.get_doc("Miss Punch Application",att.miss_punch_marked)
                if misspunch:
                    in_time = misspunch.in_punch
                    out_time = misspunch.out_punch
                else:
                    if att.in_time and att.out_time:
                        in_time = att.in_time
                        out_time = att.out_time
            else:
                if att.in_time and att.out_time:
                    in_time = in_time
                    out_time = out_time
            if isinstance(in_time, str):
                in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
            if isinstance(out_time, str):
                out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
            
            att_wh = time_diff_in_hours(out_time,in_time)
            ly = frappe.get_value("Late Entry",{'employee':att.employee,'permission_date':att.attendance_date,'docstatus':1},['late']) or 0
            et = frappe.get_value("Early Out",{'employee':att.employee,'permission_date':att.attendance_date,'docstatus':1},['out']) or 0
            tot = ly + et
            tot_lyet = tot/60
            wh = float(att_wh) + float(tot_lyet)
            if wh > 0 :
                
                if wh < 24.0:
                    time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                    frappe.db.set_value('Attendance', att.name, 'total_working_hours', str(time_in_standard_format))
                    frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
                else:
                    wh = 24.0
                    frappe.db.set_value('Attendance', att.name, 'total_working_hours',"23:59:59")
                    frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
                if wh + od_wh < 4:
                    # when working hour less than 4 check for leave application and on duty application to mark the half day or present based on working hours
                    if att.leave_application!='':
                        h_day=frappe.db.get_value("Leave Application",{'name':att.leave_application, 'docstatus':1,'workflow_state': "Approved"},['half_day'])
                        if h_day:
                            if h_day==1:	
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','On Leave')
                        else:
                            frappe.db.set_value('Attendance',att.name,'status','Absent')
                    else:
                        frappe.db.set_value('Attendance',att.name,'status','Absent')
                elif wh + od_wh >= 4 and wh + od_wh < 8:
                    if frappe.db.exists("Leave Application",{'employee':att.employee,'half_day_date':att.attendance_date,'docstatus':1, 'workflow_state': "Approved"}):
 
                        if att.leave_application is None:
                            leave_application=frappe.db.get_value("Leave Application",{'employee':att.employee,'half_day_date':att.attendance_date,'docstatus':1, 'workflow_state': "Approved"},['name'])
                            lapp_type=frappe.db.get_value("Leave Application",{'employee':att.employee,'half_day_date':att.attendance_date,'docstatus':1, 'workflow_state': "Approved"},['leave_type'])
                            frappe.db.set_value('Attendance',att.name,'leave_application',leave_application)
                            frappe.db.set_value('Attendance',att.name,'leave_type',lapp_type)
                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                    else:
                        frappe.db.set_value('Attendance',att.name,'status','Half Day')
                elif wh + od_wh >= 8:
                    frappe.db.set_value('Attendance',att.name,'status','Present')  
                
                    
                
                shift_st = frappe.get_value("Shift Type",{'name':att.shift},['start_time'])
                shift_et = frappe.get_value("Shift Type",{'name':att.shift},['end_time'])
                shift_tot = time_diff_in_hours(shift_et,shift_st)
                time_in_standard_format_timedelta = time_diff_in_timedelta(shift_et,out_time)
                ot_hours = time(0,0,0)
                hh = check_holiday(att.attendance_date,att.employee)
                if not hh or hh=='NPD':
                    if wh > shift_tot:
                        rounded_number1 = 0
                        rounded_number2 = 0
                        ot_hr1 = 0
                        ot_hr2 = 0
                        extra_hours1 = "00:00:00"
                        extra_hours2 = "00:00:00"
                        ot_hours1 = "00:00:00"
                        ot_hours2 = "00:00:00"
                        if datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) > in_time :
                            extra_hours1 = datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) - in_time
                            duration = datetime.strptime(str(extra_hours1), "%H:%M:%S")
                            total_seconds = (duration.hour * 3600 + duration.minute * 60 + duration.second)/3600
                            rounded_number1 = round(total_seconds, 3)
                            time_diff = datetime.strptime(str(extra_hours1), '%H:%M:%S').time()
                            ot_hours1 = time_diff

                        # shift end ot
                        shift_end_time = datetime.strptime(str(shift_et),'%H:%M:%S').time()
                        if att.shift in [ "I","II","Lady Guard","SEQ","SO","G","HK","Gardner"] :
                            shift_date = att.attendance_date
                        else:
                            shift_date = add_days(att.attendance_date,+1)  
                        
                        ot_date_str = datetime.strptime(str(shift_date),'%Y-%m-%d').date()
                        shift_end_datetime = datetime.combine(ot_date_str,shift_end_time)
                        if shift_end_datetime < out_time :
                            extra_hours2 = out_time - shift_end_datetime
                            days = 1
                        else:
                            extra_hours2 = timedelta(0)
                            days = 0
                        if days == 1 :
                            duration = datetime.strptime(str(extra_hours2), "%H:%M:%S")
                            # total_seconds = (duration.hour * 3600 + duration.minute * 60 + duration.second)/3600
                            total_seconds = extra_hours2.total_seconds() / 3600
                            rounded_number2 = round(total_seconds, 3)
                            time_diff = datetime.strptime(str(extra_hours2), '%H:%M:%S').time()
                            ot_hours2 = time_diff
                            
                        else:
                            rounded_number2 = 0
                            ot_hr2 = 0
                            extra_hours2 = "00:00:00"
                            ot_hours2 = "00:00:00"
                        if ot_hours1 and ot_hours2:
                            time_delta1 = datetime.strptime(str(extra_hours1), '%H:%M:%S')
                            time_delta2 = datetime.strptime(str(extra_hours2), '%H:%M:%S')
                            delta1 = timedelta(hours=time_delta1.hour, minutes=time_delta1.minute, seconds=time_delta1.second)
                            delta2 = timedelta(hours=time_delta2.hour, minutes=time_delta2.minute, seconds=time_delta2.second)

                            time_diff = delta1 + delta2
                            if datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) > in_time:
                                extra_hours11 = datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) - in_time
                                duration1 = datetime.strptime(str(extra_hours11), "%H:%M:%S")
                                total_seconds1 = (duration1.hour * 3600 + duration1.minute * 60 + duration1.second)/3600
                                rounded_number11 = round(total_seconds1, 3)
                                time_diff1 = datetime.strptime(str(extra_hours11), '%H:%M:%S').time()
                            else:
                                time_diff1 = time(0, 0, 0)
                            att_out_time = out_time.time()

                            
                            shift_break_time = frappe.get_doc("Shift Type", {'name': att.shift})
                            if shift_break_time.break_time:
                                for s in shift_break_time.break_time:
                                    break_time = datetime.strptime(str(s.breaktime_to),'%H:%M:%S').time()
                                    ot_date_str = datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date()
                                    shift_break_time_to = datetime.combine(ot_date_str,break_time)
                                    if out_time> shift_break_time_to:
                                        if datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) >= shift_break_time_to:
                                            if time_diff1.minute > 30: 
                                                time_diff = time_diff - timedelta(minutes=30)
                                            else:
                                                if time_diff1.hour > 0:
                                                    time_diff = time_diff - timedelta(minutes=30)
                                                else:
                                                    time_diff = time_diff - timedelta(minutes=time_diff1.minute)
    
                                        else:
                                            
                                            if datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_et),'%H:%M:%S').time()) < shift_break_time_to:
                                                time_diff = time_diff - timedelta(minutes=30)
                            if time_diff >= timedelta(hours=1)  :
                                if (time_diff.seconds//60)%60 <=29:
                                    
                                    ot_hours = timedelta(hours=(time_diff.seconds // 3600),minutes=0,seconds=0)
                                else:
                                    ot_hours = timedelta(hours=(time_diff.seconds // 3600),minutes=30,seconds=0)
                            elif time_diff < timedelta(hours=1) :
                                if (time_diff.seconds//60)%60 <= 29:
                                    ot_hours = "00:00:00"
                                else:
                                    ot_hours = "00:30:00"
                            ftr = [3600,60,1]
                            hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                            ot_hr = round(hr/3600,1)
                        frappe.db.set_value('Attendance',att.name,'extra_hours',rounded_number1 + rounded_number2)
                        frappe.db.set_value('Attendance',att.name,'total_extra_hours',time_adding_frm_datetime(extra_hours1,extra_hours2))
                        
                    else:
                        frappe.db.set_value('Attendance',att.name,'extra_hours',"0.0")
                        frappe.db.set_value('Attendance',att.name,'total_extra_hours',"00:00:00")
                        
                else:
                    if datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) > in_time:
                        extra_hours11 = datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) - in_time
                        duration1 = datetime.strptime(str(extra_hours11), "%H:%M:%S")
                        total_seconds1 = (duration1.hour * 3600 + duration1.minute * 60 + duration1.second)/3600
                        rounded_number11 = round(total_seconds1, 3)
                        time_diff1 = datetime.strptime(str(extra_hours11), '%H:%M:%S').time()
                    else:
                        time_diff1 = time(0, 0, 0)
                    att_out_time = out_time.time()

                    time_diff = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
                    shift_break_time = frappe.get_doc("Shift Type", {'name': att.shift})
                    if shift_break_time.break_time:
                        for s in shift_break_time.break_time:
                            break_time = datetime.strptime(str(s.breaktime_to),'%H:%M:%S').time()
                            ot_date_str = datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date()
                            shift_break_time_to = datetime.combine(ot_date_str,break_time)
                            if out_time> shift_break_time_to:
                                if datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) >= shift_break_time_to:
                                    if time_diff1.minute > 30: 
                                        time_diff_datetime = datetime.combine(datetime.min, time_diff) - timedelta(minutes=30)
                                    
                                        time_diff = time_diff_datetime.time()
                                    else:
                                        if time_diff1.hour > 0:
                                            time_diff_datetime = datetime.combine(datetime.min, time_diff) - timedelta(minutes=30)
                                            time_diff = time_diff_datetime.time()
                                        else:
                                            time_diff_datetime = datetime.combine(datetime.min, time_diff) - timedelta(minutes=time_diff1.minute)
                                        
                                            time_diff = time_diff_datetime.time()
                                else:
                                    time_diff_datetime = datetime.combine(datetime.min, time_diff) - timedelta(minutes=30)
                                
                                    time_diff = time_diff_datetime.time()
                    
                    
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
                    frappe.db.set_value('Attendance',att.name,'extra_hours',wh)
                    frappe.db.set_value('Attendance',att.name,'total_extra_hours',str(time_in_standard_format))
            else:
                frappe.db.set_value('Attendance',att.name,'total_working_hours',"00:00:00")
                frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
                frappe.db.set_value('Attendance',att.name,'extra_hours',"0.0")
                frappe.db.set_value('Attendance',att.name,'total_extra_hours',"00:00:00")
                
        else:
            frappe.db.set_value('Attendance',att.name,'total_working_hours',"00:00:00")
            frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
            frappe.db.set_value('Attendance',att.name,'extra_hours',"0.0")
            frappe.db.set_value('Attendance',att.name,'total_extra_hours',"00:00:00")
            
      

    for att in attendance:
        if att.shift and att.in_time and att.out_time and att.overtime_hours:
            ot_applicable = frappe.get_value("Employee",{'name':att.employee},['ot_applicable'])
            if ot_applicable == 1 :
                if att.on_duty_application != "":
                    if att.in_time and att.out_time:
                        in_time = att.in_time
                        out_time = att.out_time
                else:
                    if att.session_from_time and att.session_to_time: 
                        in_time = att.session_from_time
                        out_time = att.session_to_time
                if isinstance(in_time, str):
                    in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
                if isinstance(out_time, str):
                    out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')

                if frappe.db.exists('Overtime Request',{'ot_date':att.attendance_date,'employee':att.employee,'docstatus':('!=','2')}):
                    ot = frappe.get_doc("Overtime Request",{'ot_date':att.attendance_date,'employee':att.employee,'docstatus':('!=','2')})
                    # ot.employee = att.employee
                    # ot.employee_name = att.employee_name
                    # ot.department = frappe.get_value("Employee",{'name':att.employee},['department'])
                    # ot.designation = frappe.get_value("Employee",{'name':att.employee},['designation'])
                    ot.ot_date = att.attendance_date
                    ot.shift = att.shift
                    ot.from_time = in_time.time()
                    ot.to_time = out_time.time()
                    ot.biometric_checkin = in_time
                    ot.biometric_checkinout = out_time
                    ot.total_worked_hours = att.total_working_hours
                    ot.ot_applicable = 1
                    ot.ot_hours = att.overtime_hours
                    ot.attendance = att.name
                    ot.save(ignore_permissions=True)
                    frappe.db.commit()
                else:
                    ot = frappe.new_doc("Overtime Request")
                    ot.employee = att.employee
                    ot.employee_name = att.employee_name
                    ot.department = frappe.get_value("Employee",{'name':att.employee},['department'])
                    ot.designation = frappe.get_value("Employee",{'name':att.employee},['designation'])
                    ot.ot_date = att.attendance_date
                    ot.payroll_date = att.attendance_date
                    ot.shift = att.shift
                    # ot.reason= 'Automatically Created'
                    ot.from_time = in_time.time()
                    ot.to_time = out_time.time()
                    ot.biometric_checkin = in_time
                    ot.biometric_checkinout = out_time
                    ot.total_worked_hours = att.total_working_hours
                    ot.ot_applicable = 1
                    ot.ot_hours = att.overtime_hours
                    ot.attendance = att.name
                    ot.insert(ignore_permissions=True)
                    frappe.db.commit()
                frappe.db.set_value('Attendance',att.name,'overtime_request',ot.name)

        if att.attendance_regularize and att.attendance_regularize is not None:
            if frappe.db.exists("Attendance Regularize",{'name':att.attendance_regularize,'over_time':1}):
                ot=frappe.db.get_value("Attendance Regularize",{'name':att.attendance_regularize,'over_time':1},['corrected_ot'])
                ot_hours = ot.total_seconds() / 3600 if ot else 0
                frappe.db.set_value('Attendance',{'name':att.name},'total_overtime_hours',ot)
                frappe.db.set_value('Attendance',{'name':att.name},'overtime_hours',ot_hours)
                
        
def time_adding(ot_hours1, ot_hours2):
    if isinstance(ot_hours1, time):
        ot_hours1 = ot_hours1.strftime("%H:%M:%S")
    if isinstance(ot_hours2, time):
        ot_hours2 = ot_hours2.strftime("%H:%M:%S")
    hours1, minutes1, *seconds1 = map(int, ot_hours1.split(":"))
    hours2, minutes2, *seconds2 = map(int, ot_hours2.split(":"))
    seconds1 = seconds1[0] if seconds1 else 0
    seconds2 = seconds2[0] if seconds2 else 0
    td1 = timedelta(hours=hours1, minutes=minutes1, seconds=seconds1)
    td2 = timedelta(hours=hours2, minutes=minutes2, seconds=seconds2)
    total_overtime = td1 + td2
    total_seconds = int(total_overtime.total_seconds())
    total_hours = total_seconds // 3600
    total_minutes = (total_seconds % 3600) // 60
    total_overtime_hours = f"{total_hours:02d}:{total_minutes:02d}"
    return total_overtime_hours

def time_adding_frm_datetime(extra_hours1,extra_hours2):
    if isinstance(extra_hours1, (int, float)) and isinstance(extra_hours2, (int, float)):
        total_extra_hours = extra_hours1 + extra_hours2
        return total_extra_hours
    elif isinstance(extra_hours1, timedelta) and isinstance(extra_hours2, timedelta):
        total_extra_timedelta = extra_hours1 + extra_hours2
        total_extra_hours_in_hours = total_extra_timedelta.total_seconds() / 3600
        return total_extra_hours_in_hours
    elif hasattr(extra_hours1, 'total_seconds') and hasattr(extra_hours2, 'total_seconds'):
        total_extra_timedelta = extra_hours1 + extra_hours2
        total_extra_hours_in_hours = total_extra_timedelta.total_seconds() / 3600
        return total_extra_hours_in_hours
    
def mark_cc(from_date, to_date):
    # method to create the canteen coupons based on the in_time and out_time of the employees
    attendance = frappe.db.get_all('Attendance', {
        'attendance_date': ('between', (from_date, to_date)),
        'docstatus': ('!=', '2')
    }, ['name', 'shift', 'in_time', 'out_time', 'employee', 'on_duty_application', 'employee_name', 'department', 'designation', 'attendance_date', 'status'])

    for att in attendance:
        if att.in_time and att.out_time:
            in_time1 = att.in_time
            out_time1 = att.out_time
            if in_time1.date() != out_time1.date():
                if att.attendance_date == in_time1.date():
                    if frappe.db.exists('Canteen Coupons', {'employee': att.employee, 'date': att.attendance_date}):
                        cc = frappe.get_doc('Canteen Coupons', {'employee': att.employee, 'date': att.attendance_date})
                        for i in cc.items:
                            if i.item == "Dinner" or i.item =="Tea / Coffee-3":
                                i.status=1
                                cc.save(ignore_permissions=True)
                                frappe.db.commit()
                    out_time1 = datetime.combine(att.attendance_date, datetime.min.time()) + timedelta(days=1)

            cc_exists = frappe.db.exists('Canteen Coupons', {'employee': att.employee, 'date': att.attendance_date})
            # check if canteen coupon not exists,then create new coupons with food items based on the employee in_time and out_time
            if not cc_exists:
                cc = frappe.new_doc('Canteen Coupons')
                cc.employee = att.employee
                cc.employee_name = att.employee_name
                cc.department = att.department
                cc.designation = att.designation
                cc.date = att.attendance_date
                cc.attendance = att.name
                items_to_add = []
                fm = frappe.db.sql("""select * from `tabFood Menu` order by serial_no """, as_dict=True)
                for f in fm:
                    items_to_add.append({
                        'item': f.name,
                        'status': 0
                    })

                cc.set('items', items_to_add)
            else:
                # create new canteen coupon document
                cc = frappe.get_doc('Canteen Coupons', {'employee': att.employee, 'date': att.attendance_date})
            time_in = att.in_time
            time_out = att.out_time
            if time_in and time_out:
                in_time = time_in.strftime('%H:%M:%S')
                out_time = time_out.strftime('%H:%M:%S')
                time_in = datetime.strptime(in_time, '%H:%M:%S').time()
                time_out = datetime.strptime(out_time, '%H:%M:%S').time()
                for item in cc.get('items'):
                    food_menu = frappe.get_doc('Food Menu', item.get('item'))
                    from_time = str(food_menu.from_time)
                    to_time = str(food_menu.to_time)
                    st = datetime.strptime(from_time, '%H:%M:%S').time()
                    et= datetime.strptime(to_time, '%H:%M:%S').time()
                    if att.shift=='II': 
                        if item.item in ('Lunch','Tea / Coffee-2','Dinner'):
                            if time_in <= st <= time_out or time_in <= et <= time_out:
                                    item.status = 1
                        else:
                            item.status = 0 
                    elif att.shift=='I': 
                        if item.item in ('Lunch','Tea / Coffee-1','Break Fast'):
                            if time_in <= st <= time_out or time_in <= et <= time_out:
                                item.status = 1
                        else:
                            item.status = 0 
                    elif att.shift=='SS-N': 
                        if item.item in ('Tea / Coffee-5','Dinner'):
                            if time_in <= st <= time_out or time_in <= et <= time_out or (st < time_out):
                                item.status = 1
                        elif item.item == 'Break Fast Mid night':
                            if time_out > st:
                                item.status = 1
                        elif item.item=='Tea / Coffee-4':
                            if time_out < st:
                                item.status = 1
                        else:
                            item.status = 0 
                    elif att.shift in ['SEQ','Lady Guard','SO']: 
                        if item.item in ('Lunch','Tea / Coffee-1','Break Fast','Tea / Coffee-2'):
                            if time_in <= st <= time_out or time_in <= et <= time_out:
                                item.status = 1
                        else:
                            item.status = 0 
                    elif att.shift in ['G','Gardner','HK']: 
                        if item.item in ('Lunch','Tea / Coffee-1','Break Fast','Tea / Coffee-2','Dinner','Snacks-1'):
                            if time_in <= st <= time_out or time_in <= et <= time_out:
                                item.status = 1
                        else:
                            item.status = 0
                    elif att.shift == 'N': 
                        if item.item in ('Tea / Coffee-4','Break Fast Mid night','Break Fast','Tea / Coffee-5','Dinner','Snacks-2'):
                            if att.shift=='N':
                                if time_in <= st <= time_out or (st < time_out):
                                    item.status = 1
                                elif time_in <= st and st > time_out:
                                    item.status = 1
                            else:

                                if time_in <= st <= time_out or time_in <= et <= time_out:
                                    item.status = 1
                        else:
                            item.status = 0
                    else:
                        if time_in <= st <= time_out or time_in <= et <= time_out:
                            item.status = 1

            cc.save(ignore_permissions=True)
            frappe.db.commit()
def att_shift_status(from_date,to_date):
    # method to mark the shift status in attendance based on the status and existing applications
    attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'docstatus':('!=','2')},['*'])  
    for att in attendance:
        ss=''
        status = status_map.get(att.status, "")
        leave = status_map.get(att.leave_type, "")
        hh = check_holiday(att.attendance_date,att.employee)
        if hh:
            if status == "P" and not att.on_duty_application != "":
                ss = "OD-" + hh
            if status == "On Leave" and leave == '':
                ss = "hh"
            if status == "On Leave" and leave != '' and att.leave_application is not None:
                ss = leave
            else:
                if status == "P" and att.shift == "N":
                    ss = "PN/" + hh
                if status == "P" and att.shift == "III":
                    ss = "PIII/" + hh
                if status == "P" and not att.shift == "N" and not att.shift == "III":
                    ss = "P/" + hh
        else:
            if status == "P" and att.shift == "N":
                ss = "P/N"
            if status == "P" and att.shift == "III":
                ss = "PN/III"
            if status == "P" and not att.shift == "N" and not att.shift == "III":
                ss = "P"
            if status == "On Leave" and leave != '':
                ss = leave
        if status == "A":
            hh = check_holiday(att.attendance_date,att.employee)
            if hh:
                ss = hh
            else:
                ss = "AB"
        if status == "HD" and leave != '':
            if att.working_hours == 0:
                ss = leave + "/LOP"
            else:
                ss = "PP/" + leave
        if status == "HD" and leave == '':
            
            hh = check_holiday(att.attendance_date,att.employee)
            if hh:
                ss = "HD/" + hh
            else:
                ss = "P/AB" 
                        
        
        if att.on_duty_application:
            session = frappe.get_value("On Duty Application",{'name':att.on_duty_application,'docstatus':('!=',2)},['session'])
            if session == "Full day":
                ss = "P(OD)"

            if session == "First Half":
                ss = "OD/P"
                
            if session == "Second Half":
                ss = "P/OD"
            if session == "Flexible":
                ss = "P-OD"
        
        frappe.db.set_value('Attendance',att.name,'shift_status',str(ss))
        frappe.db.commit()

def mark_att_present(from_date, to_date):
    # when attendance is present and in draft, this method submit the attendance
    attendance_docstatus_0 = frappe.db.get_all('Attendance', {
        'attendance_date': ('between', (from_date, to_date)),'docstatus': 0}, ['*'])
    
    for att in attendance_docstatus_0:
        if att.get('status') == 'Present':
            frappe.db.set_value('Attendance', att.get('name'), 'docstatus', 1)

def check_holiday(date, emp):
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
                if holiday[0].others == "DH":
                    status = "NPD"
                else:
                    status = holiday[0].others
        else:
            status = 'Not Joined'
    return status

@frappe.whitelist()
def get_urc_to_ec(from_date,to_date,employee):
    # method to push the unregistered checkins to the employee checkin with employee
    pin = frappe.get_value('Employee',{'name':employee},['biometric_pin'])
    urc = frappe.db.sql("""select * from `tabUnregistered Employee Checkin` where date(biometric_time) between '%s' and '%s' and biometric_pin = '%s' """%(from_date,to_date,pin),as_dict=True)
    for uc in urc:
        pin = uc.biometric_pin
        time = uc.biometric_time
        dev = uc.location_device_id
        typ = uc.log_type
        nam = uc.name
        if time != "":
            if not frappe.db.exists('Employee Checkin',{'biometric_pin':pin,"time":time}):
                ec = frappe.new_doc('Employee Checkin')
                ec.biometric_pin = pin
                ec.employee = frappe.db.get_value('Employee',{'biometric_pin':pin},['name'])
                ec.time = time
                ec.device_id = dev
                ec.log_type = typ
                ec.save(ignore_permissions=True)
                frappe.db.commit()
                attendance = frappe.db.sql(""" delete from `tabUnregistered Employee Checkin` where name = '%s' """%(nam))      
    return "ok"

@frappe.whitelist()
def get_urc_to_ec_without_employee(from_date,to_date):
    # method to push the unregistered checkins to the employee checkin without employee
    urc = frappe.db.sql("""select * from `tabUnregistered Employee Checkin` where date(biometric_time) between '%s' and '%s' """%(from_date,to_date),as_dict=True)
    for uc in urc:
        pin = uc.biometric_pin
        time = uc.biometric_time
        dev = uc.location_device_id
        typ = uc.log_type
        nam = uc.name
        if time != "":
            if frappe.db.exists('Employee',{'biometric_pin':pin}):
                if not frappe.db.exists('Employee Checkin',{'biometric_pin':pin,"time":time}):
                    ec = frappe.new_doc('Employee Checkin')
                    ec.biometric_pin = pin
                    ec.employee = frappe.db.get_value('Employee',{'biometric_pin':pin},['name'])
                    ec.time = time
                    ec.device_id = dev
                    ec.log_type = typ
                    ec.save(ignore_permissions=True)
                    frappe.db.commit()
                    attendance = frappe.db.sql(""" delete from `tabUnregistered Employee Checkin` where name = '%s' """%(nam))      
    return "ok"

@frappe.whitelist()
def update_att_without_employee(from_date,to_date):
    checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where skip_auto_attendance = 0 and date(time) between '%s' and '%s' order by time  """%(from_date,to_date),as_dict=True)
    for c in checkins:
        employee = frappe.db.exists('Employee',{'status':'Active','date_of_joining':['<=',from_date],'name':c.employee})
        if employee:
            mark_attendance_from_checkin(c.employee,c.time,c.log_type)
    mark_absent(from_date,to_date)
    mark_wh_ot(from_date,to_date)
    ot_without_break(from_date,to_date)  
    mark_late_early(from_date,to_date)
    att_shift_status(from_date,to_date)
    create_npd_allowance_att(from_date,to_date)
    mark_cc(from_date,to_date) 
    add_ot_from_od(from_date,to_date)
    update_ot_hrs(from_date,to_date)
    update_leave_attendance_status(from_date, to_date)
    return "ok"

@frappe.whitelist()
def update_att_with_employee(from_date,to_date,employee):
    employee=employee
    checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where date(time) between '%s' and '%s' and employee = '%s' order by time  """%(from_date,to_date,employee),as_dict=True)
    for c in checkins:
        employee = frappe.db.exists('Employee',{'status':'Active','date_of_joining':['<=',from_date],'name':c.employee})
        if employee:
            mark_attendance_from_checkin(c.employee,c.time,c.log_type)
    mark_absent_with_employee(from_date,to_date,employee)
    mark_wh_ot_with_employee(from_date,to_date,employee)
    ot_without_break_with_employee(from_date,to_date,employee)  
    mark_late_early_with_employee(employee,from_date,to_date)
    att_shift_status_with_employee(from_date,to_date,employee)
    create_npd_allowance(from_date,to_date,employee)
    mark_cc_with_employee(from_date,to_date,employee) 
    add_ot_from_od_employee(from_date,to_date,employee)
    update_ot_hrs_emp(from_date,to_date,employee)
    update_leave_attendance_status_employee(from_date,to_date,employee)
    return "ok"

@frappe.whitelist()
def mark_absent_with_employee(from_date,to_date,employee):
        # for non holiday when attendance is not created from mark_attendance_from_checkin method, then it will be marked as absent 
        dates = get_dates(from_date,to_date)
        for date in dates:
            employees = frappe.db.get_all('Employee',{'status':'Active','name':employee},['*'])
            for emp in employees:
                hh = check_holiday(date,emp.name)
                if not hh:
                    if not frappe.db.exists('Attendance',{'attendance_date':date,'employee':emp.name,'docstatus':('!=','2')}):
                        att = frappe.new_doc("Attendance")
                        att.employee = emp.name
                        att.status = 'Absent'
                        att.attendance_date = date
                        att.total_working_hours = "00:00:00"
                        att.late_entry_hours = "00:00:00"
                        att.early_exit_hours = "00:00:00"
                        att.working_hours = "0.0"
                        att.extra_hours = "0.0"
                        att.total_extra_hours = "00:00:00"
                        att.total_overtime_hours = "00:00:00"
                        att.overtime_hours = "0.0"
                        att.save(ignore_permissions=True)
                        frappe.db.commit()
        
# def mark_wh_ot_with_employee(from_date,to_date,employee):
#     # method to mark the attendance status
#     attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'docstatus':('!=','2'),'employee':employee},['name','shift','in_time','out_time','employee','on_duty_application','employee_name','department','designation','attendance_date','session_from_time','session_to_time','attendance_regularize'])
#     od_wh=0.0
#     for att in attendance:
#         if (att.in_time or (att.session_from_time and att.on_duty_application)) and (att.out_time or (att.session_to_time and att.on_duty_application)) and att.shift:
#             in_time = att.in_time
#             out_time = att.out_time
#             if att.on_duty_application is not None:
#                 # frappe.errprint("HI OD Test")
#                 if att.session_from_time and att.session_to_time:
#                     od=frappe.get_doc("On Duty Application",att.on_duty_application)
#                     if not out_time:
#                         total_seconds_to = int(att.session_to_time.total_seconds())
#                         hours_to, remainder = divmod(total_seconds_to, 3600)
#                         minutes_to, seconds_to = divmod(remainder, 60)
#                         session_to_time_as_time = datetime.time(datetime(1, 1, 1, hours_to, minutes_to, seconds_to))
#                         session_to_time_as_datetime = datetime.combine(att.attendance_date, session_to_time_as_time)
#                         out_time = session_to_time_as_datetime
#                     else:
#                         session_to_time_as_time = (datetime.min + att.session_to_time).time()
#                         if out_time.time() > session_to_time_as_time:
#                             out_time = att.out_time
#                         else:
#                             out_time = datetime.combine(out_time.date(), session_to_time_as_time)
#                     # frappe.errprint("OUT PRINT")
#                     # frappe.errprint(out_time)
#                     if not in_time:
#                         total_seconds_from = int(att.session_from_time.total_seconds())
#                         hours_from, remainder = divmod(total_seconds_from, 3600)
#                         minutes_from, seconds_from = divmod(remainder, 60)
#                         session_from_time_as_time = datetime.time(datetime(1, 1, 1, hours_from, minutes_from, seconds_from))
#                         session_from_time_as_datetime = datetime.combine(att.attendance_date, session_from_time_as_time)
#                         in_time = session_from_time_as_datetime
#                     else:
#                         # compare actual in time and session from time, least one is taken for calculation
#                         session_from_time_as_time = (datetime.min + att.session_from_time).time()
#                         if in_time.time() < session_from_time_as_time:
#                             in_time = att.in_time
#                         else:
#                             in_time = datetime.combine(in_time.date(), session_from_time_as_time)
#                     total_seconds = int(att.session_to_time.total_seconds()) - int(att.session_from_time.total_seconds())
#                     od_wh = total_seconds / 3600
#              # if miss punch application is there, then timing from the application is taken for calculation          
#             if att.miss_punch_marked is not None:
#                 misspunch=frappe.get_doc("Miss Punch Application",att.miss_punch_marked)
#                 if misspunch:
#                     in_time = misspunch.in_punch
#                     out_time = misspunch.out_punch
#                 else:
#                     if att.in_time and att.out_time:
#                         in_time = att.in_time
#                         out_time = att.out_time
#             else:
#                 if att.in_time and att.out_time:
#                     in_time = in_time
#                     out_time = out_time
#             if isinstance(in_time, str):
#                 in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
#             if isinstance(out_time, str):
#                 out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
            
#             att_wh = time_diff_in_hours(out_time,in_time)
#             ly = frappe.get_value("Late Entry",{'employee':att.employee,'permission_date':att.attendance_date,'docstatus':1},['late']) or 0
#             et = frappe.get_value("Early Out",{'employee':att.employee,'permission_date':att.attendance_date,'docstatus':1},['out']) or 0
#             tot = ly + et
#             tot_lyet = tot/60
#             wh = float(att_wh) + float(tot_lyet)
#             if wh > 0 :
                
#                 if wh < 24.0:
#                     time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
#                     frappe.db.set_value('Attendance', att.name, 'total_working_hours', str(time_in_standard_format))
#                     frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
#                 else:
#                     wh = 24.0
#                     frappe.db.set_value('Attendance', att.name, 'total_working_hours',"23:59:59")
#                     frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
#                 # frappe.errprint("HI ODWH")
#                 # frappe.errprint(od_wh)
#                 # frappe.errprint(wh)
#                 if wh + od_wh < 4:
#                     # when working hour less than 4 check for leave application and on duty application to mark the half day or present based on working hours
#                     if att.leave_application!='':
#                         h_day=frappe.db.get_value("Leave Application",{'name':att.leave_application},['half_day'])
#                         if h_day:
#                             if h_day==1:	
#                                 frappe.db.set_value('Attendance',att.name,'status','Half Day')
#                             else:
#                                 frappe.db.set_value('Attendance',att.name,'status','On Leave')
#                         else:
#                             frappe.db.set_value('Attendance',att.name,'status','Absent')
#                     else:
#                         frappe.db.set_value('Attendance',att.name,'status','Absent')
#                 elif wh + od_wh >= 4 and wh + od_wh < 8:
#                     if frappe.db.exists("Leave Application",{'employee':att.employee,'half_day_date':att.attendance_date,'docstatus':1,'workflow_state': "Approved"}):
 
#                         if att.leave_application is None:
#                             leave_application=frappe.db.get_value("Leave Application",{'employee':att.employee,'half_day_date':att.attendance_date,'docstatus':1, 'workflow_state': "Approved"},['name'])
#                             lapp_type=frappe.db.get_value("Leave Application",{'employee':att.employee,'half_day_date':att.attendance_date,'docstatus':1, 'workflow_state': "Approved"},['leave_type'])
#                             frappe.db.set_value('Attendance',att.name,'leave_application',leave_application)
#                             frappe.db.set_value('Attendance',att.name,'leave_type',lapp_type)
#                             frappe.db.set_value('Attendance',att.name,'status','Half Day')
#                     else:
#                         # frappe.errprint("HI F")
#                         frappe.db.set_value('Attendance',att.name,'status','Half Day')
#                 elif wh + od_wh >= 8:
#                     frappe.db.set_value('Attendance',att.name,'status','Present') 
    
#                 shift_st = frappe.get_value("Shift Type",{'name':att.shift},['start_time'])
#                 shift_et = frappe.get_value("Shift Type",{'name':att.shift},['end_time'])

#                 # # 🔧 convert timedelta → time
#                 # if isinstance(shift_st, timedelta):
#                 # 	shift_st = timedelta_to_time(shift_st)

#                 # if isinstance(shift_et, timedelta):
#                 # 	shift_et = timedelta_to_time(shift_et)

#                 # 				# build datetime
#                 # shift_start_dt = datetime.combine(att.attendance_date, shift_st)

#                 # #night shift handling
#                 # if shift_et <= shift_st:
#                 # 	shift_end_dt = datetime.combine(add_days(att.attendance_date, 1), shift_et)
#                 # else:
#                 # 	shift_end_dt = datetime.combine(att.attendance_date, shift_et)
#                 shift_tot = time_diff_in_hours(shift_et,shift_st)
#                 time_in_standard_format_timedelta = time_diff_in_timedelta(shift_et,out_time)
#                 ot_hours = time(0,0,0)
#                 hh = check_holiday(att.attendance_date,att.employee)
#                 if not hh or hh=='NPD':
#                     if wh > shift_tot:
#                         rounded_number1 = 0
#                         rounded_number2 = 0
#                         ot_hr1 = 0
#                         ot_hr2 = 0
#                         extra_hours1 = "00:00:00"
#                         extra_hours2 = "00:00:00"
#                         ot_hours1 = "00:00:00"
#                         ot_hours2 = "00:00:00"
#                         if datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) > in_time :
#                             extra_hours1 = datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) - in_time
#                             duration = datetime.strptime(str(extra_hours1), "%H:%M:%S")
#                             total_seconds = (duration.hour * 3600 + duration.minute * 60 + duration.second)/3600
#                             rounded_number1 = round(total_seconds, 3)
#                             time_diff = datetime.strptime(str(extra_hours1), '%H:%M:%S').time()
#                             ot_hours1 = time_diff

#                         # shift end ot
#                         shift_end_time = datetime.strptime(str(shift_et),'%H:%M:%S').time()
#                         if att.shift in [ "I","II","III","Lady Guard","SEQ","SO","G","HK","Gardner"] :
#                             shift_date = att.attendance_date
#                         else:
#                             shift_date = add_days(att.attendance_date,+1)  
                        
#                         ot_date_str = datetime.strptime(str(shift_date),'%Y-%m-%d').date()
#                         shift_end_datetime = datetime.combine(ot_date_str,shift_end_time)
#                         if shift_end_datetime < out_time :
#                             extra_hours2 = out_time - shift_end_datetime
#                             days = 1
#                         else:
#                             extra_hours2 = "00:00:00"
#                             days = 0
#                         if days == 1 :
#                             duration = datetime.strptime(str(extra_hours2), "%H:%M:%S")
#                             total_seconds = (duration.hour * 3600 + duration.minute * 60 + duration.second)/3600
#                             rounded_number2 = round(total_seconds, 3)
#                             time_diff = datetime.strptime(str(extra_hours2), '%H:%M:%S').time()
#                             ot_hours2 = time_diff
                            
#                         else:
#                             rounded_number2 = 0
#                             ot_hr2 = 0
#                             extra_hours2 = "00:00:00"
#                             ot_hours2 = "00:00:00"
#                         if ot_hours1 and ot_hours2:
#                             time_delta1 = datetime.strptime(str(extra_hours1), '%H:%M:%S')
#                             time_delta2 = datetime.strptime(str(extra_hours2), '%H:%M:%S')
#                             delta1 = timedelta(hours=time_delta1.hour, minutes=time_delta1.minute, seconds=time_delta1.second)
#                             delta2 = timedelta(hours=time_delta2.hour, minutes=time_delta2.minute, seconds=time_delta2.second)

#                             time_diff = delta1 + delta2
#                             if datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) > in_time:
#                                 extra_hours11 = datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) - in_time
#                                 duration1 = datetime.strptime(str(extra_hours11), "%H:%M:%S")
#                                 total_seconds1 = (duration1.hour * 3600 + duration1.minute * 60 + duration1.second)/3600
#                                 rounded_number11 = round(total_seconds1, 3)
#                                 time_diff1 = datetime.strptime(str(extra_hours11), '%H:%M:%S').time()
#                             else:
#                                 time_diff1 = time(0, 0, 0)
#                             att_out_time = out_time.time()

                            
#                             shift_break_time = frappe.get_doc("Shift Type", {'name': att.shift})
#                             if shift_break_time.break_time:
#                                 for s in shift_break_time.break_time:
#                                     break_time = datetime.strptime(str(s.breaktime_to),'%H:%M:%S').time()
#                                     ot_date_str = datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date()
#                                     shift_break_time_to = datetime.combine(ot_date_str,break_time)
#                                     if out_time> shift_break_time_to:
#                                         if datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) >= shift_break_time_to:
#                                             if time_diff1.minute > 30: 
#                                                 time_diff = time_diff - timedelta(minutes=30)
#                                             else:
#                                                 if time_diff1.hour > 0:
#                                                     time_diff = time_diff - timedelta(minutes=30)
#                                                 else:
#                                                     time_diff = time_diff - timedelta(minutes=time_diff1.minute)
    
#                                         else:
                                            
#                                             if datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_et),'%H:%M:%S').time()) < shift_break_time_to:
#                                                 time_diff = time_diff - timedelta(minutes=30)
#                             if time_diff >= timedelta(hours=1)  :
#                                 if (time_diff.seconds//60)%60 <=29:
                                    
#                                     ot_hours = timedelta(hours=(time_diff.seconds // 3600),minutes=0,seconds=0)
#                                 else:
#                                     ot_hours = timedelta(hours=(time_diff.seconds // 3600),minutes=30,seconds=0)
#                             elif time_diff < timedelta(hours=1) :
#                                 if (time_diff.seconds//60)%60 <= 29:
#                                     ot_hours = "00:00:00"
#                                 else:
#                                     ot_hours = "00:30:00"
#                             ftr = [3600,60,1]
#                             hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
#                             ot_hr = round(hr/3600,1)
#                         frappe.db.set_value('Attendance',att.name,'extra_hours',rounded_number1 + rounded_number2)
#                         frappe.db.set_value('Attendance',att.name,'total_extra_hours',time_adding_frm_datetime(extra_hours1,extra_hours2))
                        
#                     else:
#                         frappe.db.set_value('Attendance',att.name,'extra_hours',"0.0")
#                         frappe.db.set_value('Attendance',att.name,'total_extra_hours',"00:00:00")
                        
#                 else:
#                     if datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) > in_time:
#                         extra_hours11 = datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) - in_time
#                         duration1 = datetime.strptime(str(extra_hours11), "%H:%M:%S")
#                         total_seconds1 = (duration1.hour * 3600 + duration1.minute * 60 + duration1.second)/3600
#                         rounded_number11 = round(total_seconds1, 3)
#                         time_diff1 = datetime.strptime(str(extra_hours11), '%H:%M:%S').time()
#                     else:
#                         time_diff1 = time(0, 0, 0)
#                     att_out_time = out_time.time()

#                     time_diff = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
#                     shift_break_time = frappe.get_doc("Shift Type", {'name': att.shift})
#                     if shift_break_time.break_time:
#                         for s in shift_break_time.break_time:
#                             break_time = datetime.strptime(str(s.breaktime_to),'%H:%M:%S').time()
#                             ot_date_str = datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date()
#                             shift_break_time_to = datetime.combine(ot_date_str,break_time)
#                             if out_time> shift_break_time_to:
#                                 if datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) >= shift_break_time_to:
#                                     if time_diff1.minute > 30: 
#                                         time_diff_datetime = datetime.combine(datetime.min, time_diff) - timedelta(minutes=30)
                                    
#                                         time_diff = time_diff_datetime.time()
#                                     else:
#                                         if time_diff1.hour > 0:
#                                             time_diff_datetime = datetime.combine(datetime.min, time_diff) - timedelta(minutes=30)
#                                             time_diff = time_diff_datetime.time()
#                                         else:
#                                             time_diff_datetime = datetime.combine(datetime.min, time_diff) - timedelta(minutes=time_diff1.minute)
                                        
#                                             time_diff = time_diff_datetime.time()
#                                 else:
#                                     time_diff_datetime = datetime.combine(datetime.min, time_diff) - timedelta(minutes=30)
                                
#                                     time_diff = time_diff_datetime.time()
                    
                    
#                     if time_diff.hour >= 1 :
#                         if time_diff.minute <= 29:
#                             ot_hours = time(time_diff.hour,0,0)
#                         else:
#                             ot_hours = time(time_diff.hour,30,0)
#                     elif time_diff.hour == 0 :
#                         if time_diff.minute <= 29:
#                             ot_hours = time(0,0,0)
#                         else:
#                             ot_hours = time(time_diff.hour,30,0)
#                     ftr = [3600,60,1]
#                     hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
#                     ot_hr = round(hr/3600,1)
#                     frappe.db.set_value('Attendance',att.name,'extra_hours',wh)
#                     frappe.db.set_value('Attendance',att.name,'total_extra_hours',str(time_in_standard_format))
#             else:
#                 frappe.db.set_value('Attendance',att.name,'total_working_hours',"00:00:00")
#                 frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
#                 frappe.db.set_value('Attendance',att.name,'extra_hours',"0.0")
#                 frappe.db.set_value('Attendance',att.name,'total_extra_hours',"00:00:00")
                
#         else:
#             frappe.db.set_value('Attendance',att.name,'total_working_hours',"00:00:00")
#             frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
#             frappe.db.set_value('Attendance',att.name,'extra_hours',"0.0")
#             frappe.db.set_value('Attendance',att.name,'total_extra_hours',"00:00:00")
#         if att.attendance_regularize and att.attendance_regularize is not None:
#             if frappe.db.exists("Attendance Regularize",{'name':att.attendance_regularize,'over_time':1}):
#                 ot=frappe.db.get_value("Attendance Regularize",{'name':att.attendance_regularize,'over_time':1},['corrected_ot'])
#                 ot_hours = ot.total_seconds() / 3600 if ot else 0
#                 frappe.db.set_value('Attendance',{'name':att.name},'total_overtime_hours',ot)
#                 frappe.db.set_value('Attendance',{'name':att.name},'overtime_hours',ot_hours)
            
def mark_wh_ot_with_employee(from_date, to_date, employee):

    attendance = frappe.db.get_all( 'Attendance',{ 'attendance_date': ('between', (from_date, to_date)), 'docstatus': ('!=', '2'), 'employee': employee},
        ['name','shift','in_time','out_time','employee','on_duty_application','employee_name','department','designation','attendance_date','session_from_time','session_to_time','attendance_regularize',  'miss_punch_marked','leave_application'])
    od_wh = 0.0
    for att in attendance:

        if not ((att.in_time or att.session_from_time) and(att.out_time or att.session_to_time) and att.shift):
            frappe.db.set_value('Attendance', att.name, 'total_working_hours', "00:00:00")
            frappe.db.set_value('Attendance', att.name, 'working_hours', "0.0")
            frappe.db.set_value('Attendance', att.name, 'extra_hours', "0.0")
            frappe.db.set_value('Attendance', att.name, 'total_extra_hours', "00:00:00")
            continue

        in_time = att.in_time
        out_time = att.out_time

        if att.on_duty_application is not None:
            if att.session_from_time and att.session_to_time:
                od=frappe.get_doc("On Duty Application",att.on_duty_application)
                if not out_time:
                    total_seconds_to = int(att.session_to_time.total_seconds())
                    hours_to, remainder = divmod(total_seconds_to, 3600)
                    minutes_to, seconds_to = divmod(remainder, 60)
                    session_to_time_as_time = datetime.time(datetime(1, 1, 1, hours_to, minutes_to, seconds_to))
                    session_to_time_as_datetime = datetime.combine(att.attendance_date, session_to_time_as_time)
                    out_time = session_to_time_as_datetime
                else:
                    session_to_time_as_time = (datetime.min + att.session_to_time).time()
                    if out_time.time() > session_to_time_as_time:
                        out_time = att.out_time
                    else:
                        out_time = datetime.combine(out_time.date(), session_to_time_as_time)
                # frappe.errprint("OUT PRINT")
                # frappe.errprint(out_time)
                if not in_time:
                    total_seconds_from = int(att.session_from_time.total_seconds())
                    hours_from, remainder = divmod(total_seconds_from, 3600)
                    minutes_from, seconds_from = divmod(remainder, 60)
                    session_from_time_as_time = datetime.time(datetime(1, 1, 1, hours_from, minutes_from, seconds_from))
                    session_from_time_as_datetime = datetime.combine(att.attendance_date, session_from_time_as_time)
                    in_time = session_from_time_as_datetime
                else:
                    # compare actual in time and session from time, least one is taken for calculation
                    session_from_time_as_time = (datetime.min + att.session_from_time).time()
                    if in_time.time() < session_from_time_as_time:
                        in_time = att.in_time
                    else:
                        in_time = datetime.combine(in_time.date(), session_from_time_as_time)

        if att.miss_punch_marked:
                misspunch = frappe.get_doc("Miss Punch Application", att.miss_punch_marked)
                if misspunch:
                    in_time = misspunch.in_punch
                    out_time = misspunch.out_punch

        if isinstance(in_time, str):
            in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
        if isinstance(out_time, str):
            out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')

        working_td = out_time - in_time
        wh = working_td.total_seconds() / 3600

        if wh <= 0:
            frappe.db.set_value('Attendance', att.name, 'total_working_hours', "00:00:00")
            frappe.db.set_value('Attendance', att.name, 'working_hours', "0.0")
            frappe.db.set_value('Attendance', att.name, 'extra_hours', "0.0")
            frappe.db.set_value('Attendance', att.name, 'total_extra_hours', "00:00:00")
            continue

        if wh < 24:
            frappe.db.set_value('Attendance', att.name, 'total_working_hours', str(working_td))
            frappe.db.set_value('Attendance', att.name, 'working_hours', wh)

            if wh + od_wh < 4:
                frappe.db.set_value('Attendance', att.name, 'status', 'Absent')

            elif wh + od_wh >= 4 and wh + od_wh < 8:
                frappe.db.set_value('Attendance', att.name, 'status', 'Half Day')

            elif wh + od_wh >= 8:
                frappe.db.set_value('Attendance', att.name, 'status', 'Present')
        else:
            frappe.db.set_value('Attendance', att.name, 'total_working_hours', "23:59:59")
            frappe.db.set_value('Attendance', att.name, 'working_hours', 24.0)
            wh = 24.0

        shift_st = frappe.get_value("Shift Type", {'name': att.shift}, 'start_time')
        shift_et = frappe.get_value("Shift Type", {'name': att.shift}, 'end_time')

        if isinstance(shift_st, timedelta):
            total_seconds = int(shift_st.total_seconds())
            shift_st = time(
                total_seconds // 3600,
                (total_seconds % 3600) // 60,
                total_seconds % 60
            )

        if isinstance(shift_et, timedelta):
            total_seconds = int(shift_et.total_seconds())
            shift_et = time(
                total_seconds // 3600,
                (total_seconds % 3600) // 60,
                total_seconds % 60
            )

        shift_start_dt = datetime.combine(att.attendance_date, shift_st)

        # Night shift handling
        if shift_et <= shift_st:
            shift_end_dt = datetime.combine(
                att.attendance_date + timedelta(days=1),
                shift_et
            )
        else:
            shift_end_dt = datetime.combine(
                att.attendance_date,
                shift_et
            )

        shift_tot = (shift_end_dt - shift_start_dt).total_seconds() / 3600

        extra_hours1 = timedelta(0)
        extra_hours2 = timedelta(0)

        # Before shift OT
        if shift_start_dt > in_time:
            extra_hours1 = shift_start_dt - in_time

        # After shift OT
        if out_time > shift_end_dt:
            extra_hours2 = out_time - shift_end_dt

        total_ot_td = extra_hours1 + extra_hours2
        total_ot_hours = total_ot_td.total_seconds() / 3600

        total_seconds = int(total_ot_td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        formatted_ot = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        if wh > shift_tot:
            frappe.db.set_value('Attendance', att.name, 'extra_hours', round(total_ot_hours, 3))
            frappe.db.set_value('Attendance', att.name, 'total_extra_hours', formatted_ot)
        else:
            frappe.db.set_value('Attendance', att.name, 'extra_hours', "0.0")
            frappe.db.set_value('Attendance', att.name, 'total_extra_hours', "00:00:00")

        if att.attendance_regularize:
            if frappe.db.exists("Attendance Regularize", {'name': att.attendance_regularize, 'over_time': 1}):
                ot = frappe.db.get_value("Attendance Regularize",{'name': att.attendance_regularize, 'over_time': 1},'corrected_ot')
                ot_hours = ot.total_seconds() / 3600 if ot else 0
                frappe.db.set_value('Attendance', att.name, 'total_overtime_hours', ot)
                frappe.db.set_value('Attendance', att.name, 'overtime_hours', ot_hours)

def mark_cc_with_employee(from_date, to_date, employee):
    # method to create the canteen coupons based on the in_time and out_time of the employees
    attendance = frappe.db.get_all(
        'Attendance',
        {'attendance_date': ('between', (from_date, to_date)),
         'docstatus': ('!=', '2'),
         'employee': employee},
        ['name', 'shift', 'in_time', 'out_time', 'employee', 'on_duty_application', 'employee_name', 'department',
         'designation', 'attendance_date', 'status', 'session_from_time', 'session_to_time']
    )

    for att in attendance:
        time_in = None
        time_out = None
        odsession=frappe.db.get_value("On Duty Application",{'name':att.on_duty_application,'docstatus':('!=',2)},['session'])
        if att.status not in ["Absent", "On Leave", "Work From Home"]: 
            if att.on_duty_application =='' or odsession != "Full day":
                if att.in_time and att.out_time:
                    in_time1 = att.in_time
                    out_time1 = att.out_time
                
                    if in_time1 and out_time1:
                        time_in = in_time1.time()
                        time_out = out_time1.time()

                    if in_time1.date() != out_time1.date():
                        if att.attendance_date == in_time1.date():
                            if frappe.db.exists('Canteen Coupons', {'employee': att.employee, 'date': att.attendance_date}):
                                cc = frappe.get_doc('Canteen Coupons', {'employee': att.employee, 'date': att.attendance_date})
                                for i in cc.items:
                                    if i.item == "Dinner" or i.item =="Tea / Coffee-3":
                                        i.status=1
                                        cc.save(ignore_permissions=True)
                                        frappe.db.commit()
                    # check already coupon exists for that date
                    if not frappe.db.exists('Canteen Coupons', {'employee': att.employee, 'date': att.attendance_date}):
                        cc = frappe.new_doc('Canteen Coupons')
                        cc.employee = att.employee
                        cc.employee_name = att.employee_name
                        cc.department = att.department
                        cc.designation = att.designation
                        cc.date = att.attendance_date
                        cc.attendance = att.name
                        items_to_add = []
                        fm = frappe.db.sql("""select * from `tabFood Menu` order by serial_no """, as_dict=True)
                        for f in fm:
                            items_to_add.append({
                                'item': f.name,
                                'status': 0
                            })
                        cc.set('items', items_to_add)

                        if time_in and time_out:
                            in_time = time_in.strftime('%H:%M:%S')
                            out_time = time_out.strftime('%H:%M:%S')
                            time_in = datetime.strptime(in_time, '%H:%M:%S').time()
                            time_out = datetime.strptime(out_time, '%H:%M:%S').time()
                            for item in cc.get('items'):
                                food_menu = frappe.get_doc('Food Menu', item.get('item'))
                                from_time = str(food_menu.from_time)
                                to_time = str(food_menu.to_time)
                                st = datetime.strptime(from_time, '%H:%M:%S').time()
                                et= datetime.strptime(to_time, '%H:%M:%S').time()
                                if att.shift=='II': 
                                    if item.item in ('Lunch','Tea / Coffee-2','Dinner'):
                                        if time_in <= st <= time_out or time_in <= et <= time_out:
                                                item.status = 1
                                    else:
                                        item.status = 0 
                                elif att.shift=='I': 
                                    if item.item in ('Lunch','Tea / Coffee-1','Break Fast'):
                                        if time_in <= st <= time_out or time_in <= et <= time_out:
                                            item.status = 1
                                    else:
                                        item.status = 0 
                                elif att.shift=='SS-N': 
                                    if item.item in ('Tea / Coffee-5','Dinner'):
                                        if time_in <= st <= time_out or time_in <= et <= time_out or (st < time_out):
                                            item.status = 1
                                    elif item.item == 'Break Fast Mid night':
                                        if time_out > st:
                                            item.status = 1
                                    elif item.item=='Tea / Coffee-4':
                                        if time_out < st:
                                            item.status = 1
                                    else:
                                        item.status = 0 
                                elif att.shift in ['SEQ','Lady Guard','SO']: 
                                    if item.item in ('Lunch','Tea / Coffee-1','Break Fast','Tea / Coffee-2'):
                                        if time_in <= st <= time_out or time_in <= et <= time_out:
                                            item.status = 1
                                    else:
                                        item.status = 0 
                                elif att.shift in ['G','Gardner','HK']: 
                                    if item.item in ('Lunch','Tea / Coffee-1','Break Fast','Tea / Coffee-2','Dinner','Snacks-1'):
                                        if time_in <= st <= time_out or time_in <= et <= time_out:
                                            item.status = 1
                                    else:
                                        item.status = 0
                                elif att.shift == 'N': 
                                    if item.item in ('Tea / Coffee-4','Break Fast Mid night','Break Fast','Tea / Coffee-5','Dinner','Snacks-2'):
                                        if att.shift=='N':
                                            if time_in <= st <= time_out or (st < time_out):
                                                item.status = 1
                                        else:

                                            if time_in <= st <= time_out or time_in <= et <= time_out:
                                                item.status = 1
                                    else:
                                        item.status = 0
                                else:
                                    if time_in <= st <= time_out or time_in <= et <= time_out:
                                        item.status = 1

                        cc.save(ignore_permissions=True)
                        frappe.db.commit()
                    else:
                        # create new document when canteen coupon is not present
                        cc = frappe.get_doc('Canteen Coupons', {'employee': att.employee, 'date': att.attendance_date})
                        if not cc.get('items'):
                            items_to_add = []
                            fm = frappe.get_all('Food Menu', ["*"])
                            for f in fm:
                                items_to_add.append({
                                    'item': f.name,
                                    'status': 0
                                })
                            cc.extend('items', items_to_add)

                        if time_in and time_out:
                            in_time = time_in.strftime('%H:%M:%S')
                            out_time = time_out.strftime('%H:%M:%S')
                            time_in = datetime.strptime(in_time, '%H:%M:%S').time()
                            time_out = datetime.strptime(out_time, '%H:%M:%S').time()
                            for item in cc.get('items'):
                                food_menu = frappe.get_doc('Food Menu', item.get('item'))
                                from_time = str(food_menu.from_time)
                                to_time = str(food_menu.to_time)
                                st = datetime.strptime(from_time, '%H:%M:%S').time()
                                et= datetime.strptime(to_time, '%H:%M:%S').time()
                                if att.shift=='II': 
                                    if item.item in ('Lunch','Tea / Coffee-2','Dinner'):
                                        if time_in <= st <= time_out or time_in <= et <= time_out:
                                                item.status = 1
                                    else:
                                        item.status = 0 
                                elif att.shift=='I': 
                                    if item.item in ('Lunch','Tea / Coffee-1','Break Fast'):
                                        if time_in <= st <= time_out or time_in <= et <= time_out:
                                            item.status = 1
                                    else:
                                        item.status = 0 
                                elif att.shift=='SS-N': 
                                    if item.item in ('Tea / Coffee-5','Dinner'):
                                        if time_in <= st <= time_out or time_in <= et <= time_out or (st < time_out):
                                            item.status = 1
                                    elif item.item == 'Break Fast Mid night':
                                        if time_out > st:
                                            item.status = 1
                                    elif item.item=='Tea / Coffee-4':
                                        if time_out < st:
                                            item.status = 1
                                    else:
                                        item.status = 0 
                                elif att.shift in ['SEQ','Lady Guard','SO']: 
                                    if item.item in ('Lunch','Tea / Coffee-1','Break Fast','Tea / Coffee-2'):
                                        if time_in <= st <= time_out or time_in <= et <= time_out:
                                            item.status = 1
                                    else:
                                        item.status = 0 
                                elif att.shift in ['G','Gardner','HK']: 
                                    if item.item in ('Lunch','Tea / Coffee-1','Break Fast','Tea / Coffee-2','Dinner','Snacks-1'):
                                        if att.shift=='N':
                                            if time_in <= st <= time_out or (st < time_out):
                                                item.status = 1
                                        else:

                                            if time_in <= st <= time_out or time_in <= et <= time_out:
                                                item.status = 1
                                    else:
                                        item.status = 0
                                elif att.shift == 'N': 
                                    if item.item in ('Tea / Coffee-4','Break Fast Mid night','Break Fast','Tea / Coffee-5','Dinner','Snacks-2'):
                                        if att.shift=='N':
                                            if time_in <= st <= time_out or (st < time_out):
                                                item.status = 1
                                        else:

                                            if time_in <= st <= time_out or time_in <= et <= time_out:
                                                item.status = 1
                                    else:
                                        item.status = 0
                                else:
                                    if time_in <= st <= time_out or time_in <= et <= time_out:
                                        item.status = 1
                        cc.save(ignore_permissions=True)
                        frappe.db.commit()
def att_shift_status_with_employee(from_date,to_date,employee):
    # method to mark the shift status based on the attendance status and applications
    attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'docstatus':('!=','2'),'employee':employee},['*'])  
    for att in attendance:
        status = status_map.get(att.status, "")
        leave = status_map.get(att.leave_type, "")
        hh = check_holiday(att.attendance_date,att.employee)
        if hh:
            if status == "P" and not att.on_duty_application != "":
                ss = "OD-" + hh
            else:
                if status == "P" and att.shift == "N":
                    ss = "PN/" + hh
                if status == "P" and not att.shift == "N":
                    ss = "P/" + hh
        else:
            if status == "P" and att.shift == "N":
                ss = "P/N"
            if status == "P" and att.shift == "III":
                ss = "PN/III"
            if status == "P" and not att.shift == "N" and not att.shift == "III":
                ss = "P"
        if status == "A":
            hh = check_holiday(att.attendance_date,att.employee)
            if hh:
                ss = hh
            else:
                ss = "AB"
        if status == "HD" and leave != '':
            if att.working_hours == 0:
                ss = leave + "/LOP"
            else:
                ss = "PP/" + leave
        if status == "HD" and leave == '':
            hh = check_holiday(att.attendance_date,att.employee)
            if hh:
                ss = "HD/" + hh
            else:
                ss = "P/AB" 
        if status == "On Leave" and leave != '':
            ss = leave
        if status == "On Leave" and leave == '':
            ss = "On Leave"
        if att.on_duty_application:
            hh = check_holiday(att.attendance_date,att.employee)
            session = frappe.get_value("On Duty Application",{'name':att.on_duty_application,'docstatus':('!=',2)},['session'])
            if hh:
                ss=ss = "OD-" + hh
            else:
                if session == "Full day":
                    ss = "P(OD)"
                if session == "First Half":
                    ss = "OD/P"
                if session == "Second Half":		
                    ss = "P/OD"
                if session == "Flexible":
                    ss = "P-OD"
        frappe.db.set_value('Attendance',att.name,'shift_status',str(ss))
        frappe.db.commit()

@frappe.whitelist()
def update_att(doc,method):
    if doc.leave_application != "":
        if doc.status == "On Leave":
            leave = status_map.get(doc.leave_type, "")
            if leave != '':
                ss = leave
            if leave == '':
                ss = "On Leave"
            frappe.db.set_value('Attendance',doc.name,'shift_status',str(ss))
            frappe.db.set_value('Attendance',doc.name,'total_working_hours',"00:00:00")
            frappe.db.set_value('Attendance',doc.name,'working_hours',"0.0")
            frappe.db.set_value('Attendance',doc.name,'extra_hours',"0.0")
            frappe.db.set_value('Attendance',doc.name,'total_extra_hours',"00:00:00")
            frappe.db.set_value('Attendance',doc.name,'total_overtime_hours',"00:00:00")
            frappe.db.set_value('Attendance',doc.name,'overtime_hours',"0.0")
        elif doc.status == "Half Day":
            leave = status_map.get(doc.leave_type, "")
            if leave != '':
                ss = "PP/" + leave
            if leave == '':
                ss = "P/AB" 
            frappe.db.set_value('Attendance',doc.name,'shift_status',str(ss))
            frappe.db.set_value('Attendance',doc.name,'total_working_hours',doc.total_working_hours)
            frappe.db.set_value('Attendance',doc.name,'working_hours',doc.working_hours)
            frappe.db.set_value('Attendance',doc.name,'extra_hours',doc.extra_hours)
            frappe.db.set_value('Attendance',doc.name,'total_extra_hours',doc.total_extra_hours)
            frappe.db.set_value('Attendance',doc.name,'total_overtime_hours',doc.total_overtime_hours)
            frappe.db.set_value('Attendance',doc.name,'overtime_hours',doc.overtime_hours)
    




def mark_late_early_with_employee(employee,from_date,to_date):
    # method to mark late entry and early exit 
    attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'employee':employee},['*'])
    for att in attendance:
        hh = check_holiday(att.attendance_date, att.employee)
        if not hh or hh=='NPD':
            if att.status not in ['On Leave', 'Work From Home']:
                if att.shift and att.in_time:
                    # frappe.errprint("HI LAte")
                    shift_time_start = frappe.get_value("Shift Type", {'name': att.shift}, ["start_time"])
                    shift_start_time = datetime.strptime(str(shift_time_start), '%H:%M:%S').time()
                    start_time = dt.datetime.combine(att.attendance_date, shift_start_time)
                    start_time += dt.timedelta(minutes=1)

                    if att.in_time > start_time:
                        # if in time is greater then actual start time without any leave applications or late entry applications, then attendance will be marked as half day
                        frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
                        frappe.db.set_value('Attendance', att.name, 'late_entry_hours', att.in_time - start_time)
                        if (att.working_hours >=4) and (att.late_entry_application is None and att.leave_application is None and att.on_duty_application is None):
                            frappe.db.set_value('Attendance', att.name, 'status', 'Half Day')
                        elif (att.working_hours >= 7) and (att.late_entry_application is None and att.on_duty_application is None and att.late_entry):
                            frappe.db.set_value("Attendance", att.name, "status", 'Half Day')
                        elif att.late_entry_application is not None and att.working_hours >= 7:
                            frappe.db.set_value("Attendance", att.name, "status", 'Present')
                        
                    else:
                        frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                        frappe.db.set_value('Attendance', att.name, 'late_entry_hours', "00:00:00")

                if att.shift and att.out_time:
                    # frappe.errprint("wh late 2")
                    shift_time_end = frappe.get_value("Shift Type", {'name': att.shift}, ["end_time"])
                    shift_end_time = datetime.strptime(str(shift_time_end), '%H:%M:%S').time()
                    if att.shift in ['N','III','SS-N']:
                        attdate=add_days(att.attendance_date,+1)
                        end_time = dt.datetime.combine(attdate, shift_end_time)
                    else:
                        # frappe.errprint("G shift")
                        end_time = dt.datetime.combine(att.attendance_date, shift_end_time)
                    if att.out_time < end_time:
                        # frappe.errprint("G shift 1")
                        # if out time is less then actual end time without any leave applications or early out applications, then attendance will be marked as half day
                        frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                        frappe.db.set_value('Attendance', att.name, 'early_exit_hours', end_time - att.out_time)
                        if (att.working_hours >=4) and (att.early_exit_application is None and att.leave_application is None and att.on_duty_application is None):
                            frappe.db.set_value("Attendance", att.name, "status", 'Half Day')
                        elif att.early_exit_application is not None and att.working_hours >= 7:
                            frappe.db.set_value("Attendance", att.name, "status", 'Present')
                            
                    else:
                        frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                        frappe.db.set_value('Attendance', att.name, 'early_exit_hours', "00:00:00")
            else:
                frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                frappe.db.set_value('Attendance', att.name, 'late_entry_hours', "00:00:00")
                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                frappe.db.set_value('Attendance', att.name, 'early_exit_hours', "00:00:00")
        else:
            frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
            frappe.db.set_value('Attendance', att.name, 'late_entry_hours', "00:00:00")
            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
            frappe.db.set_value('Attendance', att.name, 'early_exit_hours', "00:00:00")

def mark_late_early(from_date,to_date):
    # method to mark late entry and early exit 
    attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'docstatus':('!=',2)},['*'])
    for att in attendance:
        hh = check_holiday(att.attendance_date, att.employee)
        if not hh or hh=='NPD':
            if att.status not in ['On Leave', 'Work From Home']:
                if att.shift and att.in_time:
                    shift_time_start = frappe.get_value("Shift Type", {'name': att.shift}, ["start_time"])
                    shift_start_time = datetime.strptime(str(shift_time_start), '%H:%M:%S').time()
                    start_time = dt.datetime.combine(att.attendance_date, shift_start_time)
                    start_time += dt.timedelta(minutes=1)
                    if att.in_time > start_time:
                        # if in time is greater then actual start time without any leave applications or late entry applications, then attendance will be marked as half day
                        frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
                        frappe.db.set_value('Attendance', att.name, 'late_entry_hours', att.in_time - start_time)
                        if (att.working_hours >=4) and (att.late_entry_application is None and att.leave_application is None and att.on_duty_application is None):
                            frappe.db.set_value("Attendance", att.name, "status", 'Half Day')
                        elif (att.working_hours >= 7) and (att.late_entry_application is None and att.late_entry):
                            frappe.db.set_value("Attendance", att.name, "status", 'Half Day')
                        elif att.late_entry_application is not None and att.working_hours >= 7:
                            frappe.db.set_value("Attendance", att.name, "status", 'Present')
                    else:
                        frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                        frappe.db.set_value('Attendance', att.name, 'late_entry_hours', "00:00:00")

                if att.shift and att.out_time:
                    shift_time_end = frappe.get_value("Shift Type", {'name': att.shift}, ["end_time"])
                    shift_end_time = datetime.strptime(str(shift_time_end), '%H:%M:%S').time()
                    if att.shift in ['N','III','SS-N']:
                        attdate=add_days(att.attendance_date,+1)
                        end_time = dt.datetime.combine(attdate, shift_end_time)
                    else:
                        end_time = dt.datetime.combine(att.attendance_date, shift_end_time)
                    
                    if att.out_time < end_time:
                        # if out time is less then actual end time without any leave applications or early out applications, then attendance will be marked as half day
                        frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                        frappe.db.set_value('Attendance', att.name, 'early_exit_hours', end_time - att.out_time)
                        if (att.working_hours >=4) and (att.early_exit_application is None and att.leave_application is None and att.on_duty_application is None):
                            frappe.db.set_value("Attendance", att.name, "status", 'Half Day')
                        elif att.early_exit_application is not None and att.working_hours >= 7:
                            frappe.db.set_value("Attendance", att.name, "status", 'Present')
                    else:
                        frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                        frappe.db.set_value('Attendance', att.name, 'early_exit_hours', "00:00:00")
            else:
                frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                frappe.db.set_value('Attendance', att.name, 'late_entry_hours', "00:00:00")
                frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                frappe.db.set_value('Attendance', att.name, 'early_exit_hours', "00:00:00")
        else:
            frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
            frappe.db.set_value('Attendance', att.name, 'late_entry_hours', "00:00:00")
            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
            frappe.db.set_value('Attendance', att.name, 'early_exit_hours', "00:00:00")



@frappe.whitelist()
def mark_wh_ot_on_update(doc,method):
    attendance = frappe.db.get_all('Attendance',{'name':doc.name},['*'])
    od_wh=0.0
    for att in attendance:
        # print(att.name)
        if att.in_time and att.out_time and att.shift:
            if att.on_duty_application != "":
                od=frappe.get_doc("On Duty Application",att.on_duty_application)
                if od.session=='Full Day':
                    in_time = att.session_from_time
                    out_time = att.session_to_time
                else:
                    od_wh = time_diff_in_hours(att.session_to_time,att.session_from_time)
            if att.miss_punch_marked is not None:
                misspunch=frappe.get_doc("Miss Punch Application",att.miss_punch_marked)
                if misspunch:
                    in_time = misspunch.in_punch
                    out_time = misspunch.out_punch
                else:
                    if att.in_time and att.out_time:
                        in_time = att.in_time
                        out_time = att.out_time
            else:
                if att.in_time and att.out_time:
                    in_time = att.in_time
                    out_time = att.out_time
            if isinstance(in_time, str):
                in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
            if isinstance(out_time, str):
                out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
            
            att_wh = time_diff_in_hours(out_time,in_time)
            ly = frappe.get_value("Late Entry",{'employee':att.employee,'permission_date':att.attendance_date,'docstatus':1},['late']) or 0
            et = frappe.get_value("Early Out",{'employee':att.employee,'permission_date':att.attendance_date,'docstatus':1},['out']) or 0
            tot = ly + et
            tot_lyet = tot/60
            wh = float(att_wh) + float(tot_lyet)
            if wh > 0 :
                if wh < 24.0:
                    time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                    frappe.db.set_value('Attendance', att.name, 'total_working_hours', str(time_in_standard_format))
                    frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
                else:
                    wh = 24.0
                    frappe.db.set_value('Attendance', att.name, 'total_working_hours',"23:59:59")
                    frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
                if wh + od_wh < 4:
                    if att.leave_application!='':
                        h_day=frappe.db.get_value("Leave Application",{'name':att.leave_application, 'docstatus':1,'workflow_state': "Approved"},['half_day'])
                        if h_day:
                            if h_day==1:	
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','On Leave')
                    else:
                        frappe.db.set_value('Attendance',att.name,'status','Absent')
                elif wh + od_wh >= 4 and wh + od_wh < 8:
                    if frappe.db.exists("Leave Application",{'employee':att.employee,'from_date':att.attendance_date,'docstatus':1, 'workflow_state': "Approved"}):
 
                        if att.leave_application is None:
                            leave_application=frappe.db.get_value("Leave Application",{'employee':att.employee,'half_day_date':att.attendance_date,'docstatus':1, 'workflow_state': "Approved"},['name'])
                            lapp_type=frappe.db.get_value("Leave Application",{'employee':att.employee,'half_day_date':att.attendance_date,'docstatus':1, 'workflow_state': "Approved"},['leave_type'])
                            frappe.db.set_value('Attendance',att.name,'leave_application',leave_application)
                            frappe.db.set_value('Attendance',att.name,'leave_type',lapp_type)
                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                    else:
                        frappe.db.set_value('Attendance',att.name,'status','Half Day')
                elif wh + od_wh >= 8:
                    frappe.db.set_value('Attendance',att.name,'status','Present')  
                shift_st = frappe.get_value("Shift Type",{'name':att.shift},['start_time'])
                shift_et = frappe.get_value("Shift Type",{'name':att.shift},['end_time'])
                shift_tot = time_diff_in_hours(shift_et,shift_st)
                time_in_standard_format_timedelta = time_diff_in_timedelta(shift_et,out_time)
                ot_hours = time(0,0,0)
                hh = check_holiday(att.attendance_date,att.employee)
                if not hh:
                    if wh > shift_tot:
                        rounded_number1 = 0
                        rounded_number2 = 0
                        ot_hr1 = 0
                        ot_hr2 = 0
                        extra_hours1 = "00:00:00"
                        extra_hours2 = "00:00:00"
                        ot_hours1 = "00:00:00"
                        ot_hours2 = "00:00:00"
                          # shift_start_datetime = datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time())
                        if datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) > in_time :
                            extra_hours1 = datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) - in_time
                            duration = datetime.strptime(str(extra_hours1), "%H:%M:%S")
                            total_seconds = (duration.hour * 3600 + duration.minute * 60 + duration.second)/3600
                            rounded_number1 = round(total_seconds, 3)
                            time_diff = datetime.strptime(str(extra_hours1), '%H:%M:%S').time()
                            ot_hours1 = time_diff
                            
                        # shift end ot
                        shift_end_time = datetime.strptime(str(shift_et),'%H:%M:%S').time()
                        if att.shift in [ "I","II","Lady Guard","SEQ","SO","G","HK","Gardner"] :
                            shift_date = att.attendance_date
                        else:
                            shift_date = add_days(att.attendance_date,+1)  
                        
                        ot_date_str = datetime.strptime(str(shift_date),'%Y-%m-%d').date()
                        shift_end_datetime = datetime.combine(ot_date_str,shift_end_time)
                        if shift_end_datetime < out_time :
                            extra_hours2 = out_time - shift_end_datetime
                            days = 1
                        else:
                            extra_hours2 = "00:00:00"
                            days = 0
                        if days == 1 :
                            duration = datetime.strptime(str(extra_hours2), "%H:%M:%S")
                            total_seconds = (duration.hour * 3600 + duration.minute * 60 + duration.second)/3600
                            rounded_number2 = round(total_seconds, 3)
                            time_diff = datetime.strptime(str(extra_hours2), '%H:%M:%S').time()
                            ot_hours2 = time_diff
                        else:
                            rounded_number2 = 0
                            ot_hr2 = 0
                            extra_hours2 = "00:00:00"
                            ot_hours2 = "00:00:00"	
                        if ot_hours1 and ot_hours2:
                            time_delta1 = datetime.strptime(str(extra_hours1), '%H:%M:%S')
                            time_delta2 = datetime.strptime(str(extra_hours2), '%H:%M:%S')
                            delta1 = timedelta(hours=time_delta1.hour, minutes=time_delta1.minute, seconds=time_delta1.second)
                            delta2 = timedelta(hours=time_delta2.hour, minutes=time_delta2.minute, seconds=time_delta2.second)

                            time_diff = delta1 + delta2
                            if datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) > in_time:
                                extra_hours11 = datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) - in_time
                                duration1 = datetime.strptime(str(extra_hours11), "%H:%M:%S")
                                total_seconds1 = (duration1.hour * 3600 + duration1.minute * 60 + duration1.second)/3600
                                rounded_number11 = round(total_seconds1, 3)
                                time_diff1 = datetime.strptime(str(extra_hours11), '%H:%M:%S').time()
                            else:
                                time_diff1 = time(0, 0, 0)
                            att_out_time = out_time.time()

                            
                            shift_break_time = frappe.get_doc("Shift Type", {'name': att.shift})
                            if shift_break_time.break_time:
                                for s in shift_break_time.break_time:
                                    break_time = datetime.strptime(str(s.breaktime_to),'%H:%M:%S').time()
                                    ot_date_str = datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date()
                                    shift_break_time_to = datetime.combine(ot_date_str,break_time)
                                    if out_time> shift_break_time_to:
                                        if datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) >= shift_break_time_to:
                                            if time_diff1.minute > 30: 
                                                time_diff = time_diff - timedelta(minutes=30)
    
                                            else:
                                                if time_diff1.hour > 0:
                                                    time_diff = time_diff - timedelta(minutes=30)
                                                else:
                                                    time_diff = time_diff - timedelta(minutes=time_diff1.minute)
    
                                        else:
                                            if datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_et),'%H:%M:%S').time()) < shift_break_time_to:
                                                time_diff = time_diff - timedelta(minutes=30)
                            if time_diff >= timedelta(hours=1)  :
                                if (time_diff.seconds//60)%60 <=29:

                                    ot_hours = timedelta(hours=(time_diff.seconds // 3600),minutes=0,seconds=0)
                                else:
                                    ot_hours = timedelta(hours=(time_diff.seconds // 3600),minutes=30,seconds=0)
                            elif time_diff < timedelta(hours=1) :
                                if (time_diff.seconds//60)%60 <=29:
                                    ot_hours = "00:00:00"
                                else:
                                    ot_hours = "00:30:00"
                            ftr = [3600,60,1]
                            hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                            ot_hr = round(hr/3600,1)

                        frappe.db.set_value('Attendance',att.name,'extra_hours',rounded_number1 + rounded_number2)
                        frappe.db.set_value('Attendance',att.name,'total_extra_hours',time_adding_frm_datetime(extra_hours1,extra_hours2))
                   
                    else:
                        frappe.db.set_value('Attendance',att.name,'extra_hours',"0.0")
                        frappe.db.set_value('Attendance',att.name,'total_extra_hours',"00:00:00")
                    
                else:
                    if datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) > in_time:
                        extra_hours11 = datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) - in_time
                        duration1 = datetime.strptime(str(extra_hours11), "%H:%M:%S")
                        total_seconds1 = (duration1.hour * 3600 + duration1.minute * 60 + duration1.second)/3600
                        rounded_number11 = round(total_seconds1, 3)
                        time_diff1 = datetime.strptime(str(extra_hours11), '%H:%M:%S').time()
                    else:
                        time_diff1 = time(0, 0, 0)
                    att_out_time = out_time.time()

                    time_diff = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
                    shift_break_time = frappe.get_doc("Shift Type", {'name': att.shift})
                    if shift_break_time.break_time:
                        for s in shift_break_time.break_time:
                            break_time = datetime.strptime(str(s.breaktime_to),'%H:%M:%S').time()
                            ot_date_str = datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date()
                            shift_break_time_to = datetime.combine(ot_date_str,break_time)
                            if out_time> shift_break_time_to:
                                if datetime.combine(datetime.strptime(str(att.attendance_date),'%Y-%m-%d').date(),datetime.strptime(str(shift_st),'%H:%M:%S').time()) >= shift_break_time_to:
                                    if time_diff1.minute > 30: 
                                        time_diff_datetime = datetime.combine(datetime.min, time_diff) - timedelta(minutes=30)
                                    
                                        time_diff = time_diff_datetime.time()
                                    else:
                                        if time_diff1.hour > 0:
                                            time_diff_datetime = datetime.combine(datetime.min, time_diff) - timedelta(minutes=30)
                                    
                                            time_diff = time_diff_datetime.time()
                                        else:
                                            time_diff_datetime = datetime.combine(datetime.min, time_diff) - timedelta(minutes=time_diff1.minute)
                                        
                                            time_diff = time_diff_datetime.time()
                                else:
                                    time_diff_datetime = datetime.combine(datetime.min, time_diff) - timedelta(minutes=30)
                                
                                    time_diff = time_diff_datetime.time()
                    
                    if time_diff.hour >= 1 :
                        if time_diff.minute <= 29:
                            ot_hours = time(time_diff.hour,0,0)
                        else:
                            ot_hours = time(time_diff.hour,30,0)
                    if time_diff.hour == 0 :
                        if time_diff.minute <= 29:
                            ot_hours = time(0,0,0)
                        else:
                            ot_hours = time(time_diff.hour,30,0)
                    
                    ftr = [3600,60,1]
                    hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                    ot_hr = round(hr/3600,1)
                    ot_hr1=0
                    ot_hr2=0
                    frappe.db.set_value('Attendance',att.name,'extra_hours',wh)
                    frappe.db.set_value('Attendance',att.name,'total_extra_hours',str(time_in_standard_format))
            else:
                frappe.db.set_value('Attendance',att.name,'total_working_hours',"00:00:00")
                frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
                frappe.db.set_value('Attendance',att.name,'extra_hours',"0.0")
                frappe.db.set_value('Attendance',att.name,'total_extra_hours',"00:00:00")
                
        else:
            frappe.db.set_value('Attendance',att.name,'total_working_hours',"00:00:00")
            frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
            frappe.db.set_value('Attendance',att.name,'extra_hours',"0.0")
            frappe.db.set_value('Attendance',att.name,'total_extra_hours',"00:00:00")
    att_shift_status_with_employee(doc.attendance_date,doc.attendance_date,doc.employee)       

from datetime import datetime, timedelta
@frappe.whitelist()
def ot_without_break(from_date,to_date):
    # method to deduct the break time from the OT hours

    attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'docstatus':('!=','2')},['*'],order_by='employee_name ASC')
    i=0
    import traceback
    frappe.log_error('Error in Ot method: {}'.format(traceback.format_exc()))
    for att in attendance:
        if att.shift:
            from datetime import datetime, time, timedelta
            intime = att.in_time
            outtime = att.out_time
            # check for on duty application
            if att.on_duty_application is not None:
                if not outtime:
                    total_seconds_to = int(att.session_to_time.total_seconds())
                    hours_to, remainder = divmod(total_seconds_to, 3600)
                    minutes_to, seconds_to = divmod(remainder, 60)
                    session_to_time_as_time = datetime.time(datetime(1, 1, 1, hours_to, minutes_to, seconds_to))
                    session_to_time_as_datetime = datetime.combine(att.attendance_date, session_to_time_as_time)
                    outtime = session_to_time_as_datetime
                else:
                    # compare actual out time and session end time, greater one is taken for calculation
                    session_to_time_as_time = (datetime.min + att.session_to_time).time()
                    if outtime.time() > session_to_time_as_time:
                        outtime = att.out_time
                    else:
                        outtime = datetime.combine(outtime.date(), session_to_time_as_time)
                if not intime:
                    total_seconds_from = int(att.session_from_time.total_seconds())
                    hours_from, remainder = divmod(total_seconds_from, 3600)
                    minutes_from, seconds_from = divmod(remainder, 60)
                    session_from_time_as_time = datetime.time(datetime(1, 1, 1, hours_from, minutes_from, seconds_from))
                    session_from_time_as_datetime = datetime.combine(att.attendance_date, session_from_time_as_time)
                    intime = session_from_time_as_datetime
                else:
                    # compare actual in time and session from time, least one is taken for calculation
                    session_from_time_as_time = (datetime.min + att.session_from_time).time()
                    if intime.time() < session_from_time_as_time:
                        intime = att.in_time
                    else:
                        intime = datetime.combine(intime.date(), session_from_time_as_time)
            else:
                intime = att.in_time
                outtime = att.out_time
            shift = frappe.get_doc('Shift Type', att.shift)
            # break will be calculated when ot_applicable is checked in the shift and break will be deducted when ot_break_deduction is checked in the shift
            if shift.ot_applicable==1 and shift.ot_break_deduction==1:
                if intime and outtime:
                    # break time are given in time ranges
                    emp_shift=frappe.get_doc("Shift Type",att.shift)
                    time_ranges = []
                    for b in emp_shift.break_time:
                        if b.breaktime_from and b.breaktime_to:
                            start_str = str(b.breaktime_from)
                            end_str = str(b.breaktime_to)
                            time_ranges.append((start_str, end_str))
                    break_deduction=0
                    early_ot=0
                    after_ot=0
                    for start_str, end_str in time_ranges:
                        start_time = datetime.strptime(start_str, '%H:%M:%S').time()
                        end_time = datetime.strptime(end_str, '%H:%M:%S').time()
                        start_datetime = datetime.combine(intime.date(), start_time)
                        if att.late_entry_application:
                            ltime=frappe.db.get_value("Shift Type",{'name':att.shift},['start_time'])
                            total_sec = int(ltime.total_seconds())
                            hours, remainder = divmod(total_sec, 3600)
                            minutes, seconds = divmod(remainder, 60)
                            ltime_as_time = time(hour=hours, minute=minutes, second=seconds)
                            act_start_datetime = datetime.combine(intime.date(), ltime_as_time)
                        end_datetime = datetime.combine(intime.date(), end_time)
                        if outtime > intime:
                            end_datetime += timedelta(days=1)
                        
                        if start_datetime < outtime < datetime.combine(intime.date(), end_time): 
                            after_ot = outtime - start_datetime
                        else:
                            # when late entry application is set shift start time is taken as in time
                            if att.late_entry_application:
                                if (act_start_datetime <= end_datetime <= outtime) or (act_start_datetime <= start_datetime <= outtime):
                                    break_deduction +=1

                                elif start_datetime < act_start_datetime < datetime.combine(intime.date(), end_time): 
                                    early_ot = end_datetime - act_start_datetime
                            else:
                                if (intime <= end_datetime <= outtime) or (intime <= start_datetime <= outtime):
                                    break_deduction +=1
                                # else:
                                elif start_datetime < intime < datetime.combine(intime.date(), end_time): 
                                        early_ot = end_datetime - intime
                    if early_ot:
                        early_ot_hrs=(early_ot.seconds//60)%60
                    else:
                        early_ot_hrs=0
                    n_shift = frappe.db.get_value("Shift Type", {'name': 'N'}, ['end_time'])
                    if att.shift=='N':
                        if isinstance(n_shift, str):
                            end_time_obj = datetime.strptime(n_shift, '%H:%M:%S').time()
                        elif isinstance(n_shift, datetime):
                            end_time_obj = n_shift.time()
                        elif isinstance(n_shift, timedelta):
                            total_seconds = n_shift.total_seconds()
                            end_time_obj = time(hour=int(total_seconds // 3600),
                                                minute=int((total_seconds % 3600) // 60),
                                                second=int(total_seconds % 60))
                        else:
                            raise ValueError("Unsupported 'end_time' format")
                        n_date=add_days(att.attendance_date,1)
                        n_shift_datetime = datetime.combine(n_date, end_time_obj)
                        if outtime>n_shift_datetime:
                            after_ot=outtime-n_shift_datetime
                    if after_ot:
                        after_ot_hrs=(after_ot.seconds//60)%60
                    else:
                        after_ot_hrs=0
                    if att.late_entry_application:
                        total_wh=outtime-act_start_datetime
                    else:
                        total_wh=outtime-intime
                    break_minutes = break_deduction * 30
                    regular_hours = timedelta(hours=8)
                    hh = check_holiday(att.attendance_date, att.employee)
                    # for NPD days the calculation need to be normal as same as non holidays, the time need to be set in working hours instead of overtime hours 
                    if hh and hh!='NPD':
                        overtime = total_wh - (timedelta(minutes=break_minutes) + timedelta(minutes=early_ot_hrs) + timedelta(minutes=after_ot_hrs))
                        
                    else:
                        if total_wh > timedelta(hours=8,minutes=30):
                            overtime = total_wh - (regular_hours + timedelta(minutes=break_minutes) + timedelta(minutes=early_ot_hrs) + timedelta(minutes=after_ot_hrs))
                        else:
                            overtime = timedelta(hours=0,minutes=0,seconds=0)
                        
                    if overtime >= timedelta(hours=1):
                        if (overtime.seconds//60)%60 <=29:
                            ot_hours = timedelta(hours=(overtime.seconds // 3600),minutes=0,seconds=0)
                        else:
                            ot_hours = timedelta(hours=(overtime.seconds // 3600),minutes=30,seconds=0)
                    elif overtime < timedelta(hours=1) :
                        total_minutes = overtime.total_seconds() // 60 
                        if total_minutes <= 29:
                            ot_hours = "00:00:00"
                        else:
                            ot_hours = "00:30:00" 
                        # frappe.errprint("NEGATIVE")
                        # frappe.errprint(ot_hours)
                    if ot_hours !='00:00:00':
                        i+=1
                        ftr = [3600,60,1]
                        hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                        ot_hr = round(hr/3600,1)
                        frappe.db.set_value('Attendance',att.name,'total_overtime_hours',ot_hours)
                        frappe.db.set_value('Attendance',att.name,'overtime_hours',ot_hr)
                    else:
                        frappe.db.set_value('Attendance',att.name,'total_overtime_hours',"00:00:00")
                        frappe.db.set_value('Attendance',att.name,'overtime_hours',"0.0")
            # break time will not deducted , when ot_break_deductionis not checked in shift   
            elif shift.ot_applicable==1 and shift.ot_break_deduction==0:
                shift_end_time = frappe.db.get_value('Shift Type', {'name': att.shift}, ['end_time'])
                if isinstance(shift_end_time, timedelta):
                    shift_end_time = (datetime.min + shift_end_time).time()
                else:
                    shift_end_time = datetime.strptime(shift_end_time, '%H:%M:%S').time()	
                hh = check_holiday(att.attendance_date, att.employee)	
                att_otime = outtime
                if att_otime:
                    att_otime_time = att_otime.time()
                else:
                    att_otime_time = shift_end_time
                time_worked_after_shift_end = timedelta(0)
                if hh:
                    if hh!='NPD':
                        if outtime > intime:
                            out_dt = datetime.combine(datetime.today(), outtime.time())
                            in_dt  = datetime.combine(datetime.today(), intime.time())

                            if outtime.time() < intime.time():
                                out_dt = out_dt + timedelta(days=1)

                            time_worked_after_shift_end = out_dt - in_dt
                    #         time_worked_after_shift_end = datetime.combine(datetime.today(), outtime.time()) - datetime.combine(datetime.today(), intime.time())
                    #     else:
                    #         time_worked_after_shift_end = timedelta(0)
                    # # else:
                    # 	if att_otime_time > shift_end_time:
                    # 		time_worked_after_shift_end = datetime.combine(datetime.today(), att_otime_time) - datetime.combine(datetime.today(), shift_end_time)
                    # 	else:
                    # 		time_worked_after_shift_end = timedelta(0)
                    else:
                        # Day shift
                        if att.shift not in ('N', 'III'):
                            if att_otime_time > shift_end_time:
                                time_worked_after_shift_end = (
                                    datetime.combine(datetime.today(), att_otime_time)
                                    - datetime.combine(datetime.today(), shift_end_time)
                                )
                            else:
                                time_worked_after_shift_end = timedelta(0)

                        # Night shift (III / N)
                        else:
                            shift_end_dt = datetime.combine(
                                add_days(att.attendance_date, 1),
                                shift_end_time
                            )
                            if outtime and outtime > shift_end_dt:
                                time_worked_after_shift_end = outtime - shift_end_dt
                            else:
                                time_worked_after_shift_end = timedelta(0)

                else:
                    if att_otime_time > shift_end_time:
                        time_worked_after_shift_end = datetime.combine(datetime.today(), att_otime_time) - datetime.combine(datetime.today(), shift_end_time)
                    else:
                        time_worked_after_shift_end = timedelta(0)
                total_seconds = time_worked_after_shift_end.total_seconds()
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                seconds = int(total_seconds % 60)
                act_time = f'{hours:02}:{minutes:02}:{seconds:02}'
                rounded_ot_total = total_seconds / 3600
                final_ot = round(rounded_ot_total, 3)
                final_ot_tot=round(final_ot * 2) / 2
                if act_time !='00:00:00':

                    hh = check_holiday(att.attendance_date, att.employee)		
                    if hh and hh=='NPD':
                        frappe.db.set_value('Attendance',att.name,'total_overtime_hours',act_time)
                        frappe.db.set_value('Attendance',att.name,'overtime_hours',final_ot_tot)
                    else:
                        frappe.db.set_value('Attendance',att.name,'total_overtime_hours',act_time)
                        frappe.db.set_value('Attendance',att.name,'overtime_hours',final_ot_tot)
                else:
                    frappe.db.set_value('Attendance',att.name,'total_overtime_hours',"00:00:00")
                    frappe.db.set_value('Attendance',att.name,'overtime_hours',"0.0")
            else:
                frappe.db.set_value('Attendance',att.name,'total_overtime_hours',"00:00:00")
                frappe.db.set_value('Attendance',att.name,'overtime_hours',"0.0")


        if att.attendance_regularize and att.attendance_regularize is not None:
            if frappe.db.exists("Attendance Regularize",{'name':att.attendance_regularize,'over_time':1}):
                ot=frappe.db.get_value("Attendance Regularize",{'name':att.attendance_regularize,'over_time':1},['corrected_ot'])
                ot_hours = ot.total_seconds() / 3600 if ot else 0
                frappe.db.set_value('Attendance',{'name':att.name},'total_overtime_hours',ot)
                frappe.db.set_value('Attendance',{'name':att.name},'overtime_hours',ot_hours) 
    for att in attendance:
        # based on the overtime hours, OT request is created for the employee
        ot=frappe.db.get_value('Attendance',{'name':att.name},['overtime_hours'])
        if att.shift and (att.in_time or att.session_from_time) and (att.out_time or att.session_to_time) and ot:
            ot_applicable = frappe.get_value("Employee",{'name':att.employee},['ot_applicable'])
            if ot_applicable == 1 :
                from datetime import datetime, time
                in_time = att.in_time
                out_time = att.out_time
                if att.on_duty_application is not None:
                    if not out_time:
                        total_seconds_to = int(att.session_to_time.total_seconds())
                        hours_to, remainder = divmod(total_seconds_to, 3600)
                        minutes_to, seconds_to = divmod(remainder, 60)
                        session_to_time_as_time = datetime.time(datetime(1, 1, 1, hours_to, minutes_to, seconds_to))
                        session_to_time_as_datetime = datetime.combine(att.attendance_date, session_to_time_as_time)
                        out_time = session_to_time_as_datetime
                    else:
                        session_to_time_as_time = (datetime.min + att.session_to_time).time()
                        if out_time.time() > session_to_time_as_time:
                            out_time = att.out_time
                        else:
                            out_time = datetime.combine(out_time.date(), session_to_time_as_time)
                    if not in_time:
                        total_seconds_from = int(att.session_from_time.total_seconds())
                        hours_from, remainder = divmod(total_seconds_from, 3600)
                        minutes_from, seconds_from = divmod(remainder, 60)
                        session_from_time_as_time = datetime.time(datetime(1, 1, 1, hours_from, minutes_from, seconds_from))
                        session_from_time_as_datetime = datetime.combine(att.attendance_date, session_from_time_as_time)
                        in_time = session_from_time_as_datetime
                    else:
                        session_from_time_as_time = (datetime.min + att.session_from_time).time()
                        if in_time.time() < session_from_time_as_time:
                            in_time = att.in_time
                        else:
                            in_time = datetime.combine(in_time.date(), session_from_time_as_time)
                else:
                    in_time = att.in_time
                    out_time = att.out_time
                if in_time is not None and isinstance(in_time, str):
                    in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
                if out_time is not None and isinstance(out_time, str):
                    out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')

                if frappe.db.exists('Overtime Request',{'ot_date':att.attendance_date,'employee':att.employee,'ot_from_od':0,'docstatus':('!=','2')}):
                    ot = frappe.get_doc("Overtime Request",{'ot_date':att.attendance_date,'employee':att.employee,'docstatus':('!=','2')})
                    att_ot=frappe.db.get_value("Attendance",{'name':att.name},['overtime_hours'])
                    ot.employee = att.employee
                    ot.employee_name = att.employee_name
                    ot.department = frappe.get_value("Employee",{'name':att.employee},['department'])
                    ot.designation = frappe.get_value("Employee",{'name':att.employee},['designation'])
                    ot.ot_date = att.attendance_date
                    ot.shift = att.shift
                    ot.from_time = in_time.time()
                    ot.to_time = out_time.time()
                    ot.biometric_checkin = in_time
                    ot.biometric_checkinout = out_time
                    ot.total_worked_hours = att.total_working_hours
                    ot.ot_applicable = 1
                    ot.ot_hours = att_ot
                    ot.attendance = att.name
                    ot.save(ignore_permissions=True)
                    frappe.db.commit()
                    frappe.db.set_value('Attendance',att.name,'overtime_request',ot.name)
                if not frappe.db.exists('Overtime Request',{'ot_date':att.attendance_date,'employee':att.employee,'docstatus':('!=','2')}):
                    ot = frappe.new_doc("Overtime Request")
                    att_ot=frappe.db.get_value("Attendance",{'name':att.name},['overtime_hours'])
                    ot.employee = att.employee
                    ot.employee_name = att.employee_name
                    ot.department = frappe.get_value("Employee",{'name':att.employee},['department'])
                    ot.designation = frappe.get_value("Employee",{'name':att.employee},['designation'])
                    ot.ot_date = att.attendance_date
                    ot.payroll_date = att.attendance_date
                    ot.shift = att.shift
                    # ot.reason= 'Automatically Created'
                    ot.from_time = in_time.time()
                    ot.to_time = out_time.time()
                    ot.biometric_checkin = in_time
                    ot.biometric_checkinout = out_time
                    ot.total_worked_hours = att.total_working_hours
                    ot.ot_applicable = 1
                    ot.ot_hours = att_ot
                    ot.attendance = att.name
                    ot.insert(ignore_permissions=True)
                    frappe.db.commit()
                    frappe.db.set_value('Attendance',att.name,'overtime_request',ot.name)


@frappe.whitelist()
def ot_without_break_with_employee(from_date,to_date,employee):
    # method to deduct the break time from the OT hours
    attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'docstatus':('!=','2'),'employee':employee},['*'])
    i=0
    for att in attendance:
        if att.shift:
            # frappe.errprint("HHHELLLO")
            from datetime import datetime, time, timedelta
            intime = att.in_time
            outtime = att.out_time
            # check for on duty application
            if att.on_duty_application is not None:
                if not outtime:
                    total_seconds_to = int(att.session_to_time.total_seconds())
                    hours_to, remainder = divmod(total_seconds_to, 3600)
                    minutes_to, seconds_to = divmod(remainder, 60)
                    session_to_time_as_time = datetime.time(datetime(1, 1, 1, hours_to, minutes_to, seconds_to))
                    session_to_time_as_datetime = datetime.combine(att.attendance_date, session_to_time_as_time)
                    outtime = session_to_time_as_datetime
                else:
                    # compare actual out time and session end time, greater one is taken for calculation
                    session_to_time_as_time = (datetime.min + att.session_to_time).time()
                    if outtime.time() > session_to_time_as_time:
                        outtime = att.out_time
                    else:
                        outtime = datetime.combine(outtime.date(), session_to_time_as_time)
                if not intime:
                    total_seconds_from = int(att.session_from_time.total_seconds())
                    hours_from, remainder = divmod(total_seconds_from, 3600)
                    minutes_from, seconds_from = divmod(remainder, 60)
                    session_from_time_as_time = datetime.time(datetime(1, 1, 1, hours_from, minutes_from, seconds_from))
                    session_from_time_as_datetime = datetime.combine(att.attendance_date, session_from_time_as_time)
                    intime = session_from_time_as_datetime
                else:
                    # compare actual in time and session from time, least one is taken for calculation
                    session_from_time_as_time = (datetime.min + att.session_from_time).time()
                    if intime.time() < session_from_time_as_time:
                        intime = att.in_time
                    else:
                        intime = datetime.combine(intime.date(), session_from_time_as_time)
            else:
                intime = att.in_time
                outtime = att.out_time
            shift = frappe.get_doc('Shift Type', att.shift)
            # break will be calculated when ot_applicable is checked in the shift and break will be deducted when ot_break_deduction is checked in the shift
            if shift.ot_applicable==1 and shift.ot_break_deduction==1:
                # frappe.errprint("test")
                if intime and outtime:
                    # break time are given in time ranges
                    emp_shift=frappe.get_doc("Shift Type",att.shift)
                    time_ranges = []
                    for b in emp_shift.break_time:
                        if b.breaktime_from and b.breaktime_to:
                            start_str = str(b.breaktime_from)
                            end_str = str(b.breaktime_to)
                            time_ranges.append((start_str, end_str))
                    # frappe.errprint(time_ranges)
                    break_deduction=0
                    early_ot=0
                    after_ot=0
                    for start_str, end_str in time_ranges:
                        start_time = datetime.strptime(start_str, '%H:%M:%S').time()
                        end_time = datetime.strptime(end_str, '%H:%M:%S').time()
                        start_datetime = datetime.combine(intime.date(), start_time)
                        if att.late_entry_application:
                            ltime=frappe.db.get_value("Shift Type",{'name':att.shift},['start_time'])
                            total_sec = int(ltime.total_seconds())
                            hours, remainder = divmod(total_sec, 3600)
                            minutes, seconds = divmod(remainder, 60)
                            ltime_as_time = time(hour=hours, minute=minutes, second=seconds)
                            act_start_datetime = datetime.combine(intime.date(), ltime_as_time)
                        end_datetime = datetime.combine(intime.date(), end_time)
                        if outtime > intime:
                            end_datetime += timedelta(days=1)
                        
                        if start_datetime < outtime < datetime.combine(intime.date(), end_time): 
                            after_ot = outtime - start_datetime
                        else:
                            # when late entry application is set shift start time is taken as in time
                            if att.late_entry_application:
                                if (act_start_datetime <= end_datetime <= outtime) or (act_start_datetime <= start_datetime <= outtime):
                                    break_deduction +=1

                                elif start_datetime < act_start_datetime < datetime.combine(intime.date(), end_time): 
                                    early_ot = end_datetime - act_start_datetime
                            else:
                                if (intime <= end_datetime <= outtime) or (intime <= start_datetime <= outtime):
                                    break_deduction +=1
                                # else:
                                elif start_datetime < intime < datetime.combine(intime.date(), end_time): 
                                        early_ot = end_datetime - intime
                    if early_ot:
                        early_ot_hrs=(early_ot.seconds//60)%60
                    else:
                        early_ot_hrs=0
                    n_shift = frappe.db.get_value("Shift Type", {'name': 'N'}, ['end_time'])
                    if att.shift=='N':
                        if isinstance(n_shift, str):
                            end_time_obj = datetime.strptime(n_shift, '%H:%M:%S').time()
                        elif isinstance(n_shift, datetime):
                            end_time_obj = n_shift.time()
                        elif isinstance(n_shift, timedelta):
                            total_seconds = n_shift.total_seconds()
                            end_time_obj = time(hour=int(total_seconds // 3600),
                                                minute=int((total_seconds % 3600) // 60),
                                                second=int(total_seconds % 60))
                        else:
                            raise ValueError("Unsupported 'end_time' format")
                        n_date=add_days(att.attendance_date,1)
                        n_shift_datetime = datetime.combine(n_date, end_time_obj)
                        if outtime>n_shift_datetime:
                            after_ot=outtime-n_shift_datetime
                        
                    if after_ot:
                        after_ot_hrs=(after_ot.seconds//60)%60
                    else:
                        after_ot_hrs=0
                    if att.late_entry_application:
                        total_wh=outtime-act_start_datetime
                    else:
                        total_wh=outtime-intime
                    break_minutes = break_deduction * 30
                    regular_hours = timedelta(hours=8)
                    hh = check_holiday(att.attendance_date, att.employee)
                    # for NPD days the calculation need to be normal as same as non holidays, the time need to be set in working hours instead of overtime hours 
                    if hh and hh!='NPD':
                        overtime = total_wh - (timedelta(minutes=break_minutes) + timedelta(minutes=early_ot_hrs) + timedelta(minutes=after_ot_hrs))
                     
                    else:
                        if total_wh > timedelta(hours=8,minutes=30):
                            overtime = total_wh - (regular_hours + timedelta(minutes=break_minutes) + timedelta(minutes=early_ot_hrs) + timedelta(minutes=after_ot_hrs))
                            
                        else:
                            overtime = timedelta(hours=0,minutes=0,seconds=0)
                        
                    if overtime >= timedelta(hours=1):
                        if (overtime.seconds//60)%60 <=29:
                            ot_hours = timedelta(hours=(overtime.seconds // 3600),minutes=0,seconds=0)
                        else:
                            ot_hours = timedelta(hours=(overtime.seconds // 3600),minutes=30,seconds=0)
                    elif overtime < timedelta(hours=1) :
                        total_minutes = overtime.total_seconds() // 60 
                        if total_minutes <= 29:
                            ot_hours = "00:00:00"
                        else:
                            ot_hours = "00:30:00"  
                    
                    # frappe.errprint("NEGATIVE")
                    # frappe.errprint(ot_hours)
                    
                    if ot_hours !='00:00:00':
                        i+=1
                        ftr = [3600,60,1]
                        hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                        ot_hr = round(hr/3600,1)
                        frappe.db.set_value('Attendance',att.name,'total_overtime_hours',ot_hours)
                        frappe.db.set_value('Attendance',att.name,'overtime_hours',ot_hr)
                    else:
                        frappe.db.set_value('Attendance',att.name,'total_overtime_hours',"00:00:00")
                        frappe.db.set_value('Attendance',att.name,'overtime_hours',"0.0")
            # break time will not deducted , when ot_break_deductionis not checked in shift   
            elif shift.ot_applicable==1 and shift.ot_break_deduction==0:
                shift_end_time = frappe.db.get_value('Shift Type', {'name': att.shift}, ['end_time'])
                if isinstance(shift_end_time, timedelta):
                    shift_end_time = (datetime.min + shift_end_time).time()
                else:
                    shift_end_time = datetime.strptime(shift_end_time, '%H:%M:%S').time()	
                hh = check_holiday(att.attendance_date, att.employee)	
                att_otime = outtime
                att_otime_time = att_otime.time()
                time_worked_after_shift_end = timedelta(0)
                if hh:
                    if hh!='NPD':
                        # frappe.errprint("No NPD")
                        if outtime > intime:
                            out_dt = datetime.combine(datetime.today(), outtime.time())
                            in_dt  = datetime.combine(datetime.today(), intime.time())

                            if outtime.time() < intime.time():
                                out_dt = out_dt + timedelta(days=1)

                            time_worked_after_shift_end = out_dt - in_dt
                            # frappe.errprint(time_worked_after_shift_end)

                            # frappe.errprint(outtime)
                            # frappe.errprint(intime)
                            # frappe.errprint("OT No")
                            # time_worked_after_shift_end = datetime.combine(datetime.today(), outtime.time()) - datetime.combine(datetime.today(), intime.time())
                            # frappe.errprint(time_worked_after_shift_end)
                        else:
                            # frappe.errprint("OT")
                            time_worked_after_shift_end = timedelta(0)
                            
                    # else:
                    # 	if att_otime_time > shift_end_time:
                    # 		time_worked_after_shift_end = datetime.combine(datetime.today(), att_otime_time) - datetime.combine(datetime.today(), shift_end_time)
                    # 	else:
                    # 		time_worked_after_shift_end = timedelta(0)
                    else:
                        
                        # Day shift
                        if att.shift not in ('N', 'III'):
                            if att_otime_time > shift_end_time:
                                time_worked_after_shift_end = (
                                    datetime.combine(datetime.today(), att_otime_time)
                                    - datetime.combine(datetime.today(), shift_end_time)
                                )
                            else:
                                time_worked_after_shift_end = timedelta(0)

                        # Night shift (III / N)
                        else:
                            shift_end_dt = datetime.combine(
                                add_days(att.attendance_date, 1),
                                shift_end_time
                            )
                            if outtime and outtime > shift_end_dt:
                                time_worked_after_shift_end = outtime - shift_end_dt
                            else:
                                time_worked_after_shift_end = timedelta(0)

                else:
                    if att_otime_time > shift_end_time:
                        time_worked_after_shift_end = datetime.combine(datetime.today(), att_otime_time) - datetime.combine(datetime.today(), shift_end_time)
                    else:
                        time_worked_after_shift_end = timedelta(0)
                total_seconds = time_worked_after_shift_end.total_seconds()
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                seconds = int(total_seconds % 60)
                act_time = f'{hours:02}:{minutes:02}:{seconds:02}'
                rounded_ot_total = total_seconds / 3600
                final_ot = round(rounded_ot_total, 3)
                final_ot_tot=round(final_ot * 2) / 2
                if act_time !='00:00:00':
                    hh = check_holiday(att.attendance_date, att.employee)		
                    if hh and hh=='NPD':
                        frappe.db.set_value('Attendance',att.name,'total_overtime_hours',act_time)
                        frappe.db.set_value('Attendance',att.name,'overtime_hours',final_ot_tot)
                    else:
                        frappe.db.set_value('Attendance',att.name,'total_overtime_hours',act_time)
                        frappe.db.set_value('Attendance',att.name,'overtime_hours',final_ot_tot)
                else:
                    frappe.db.set_value('Attendance',att.name,'total_overtime_hours',"00:00:00")
                    frappe.db.set_value('Attendance',att.name,'overtime_hours',"0.0")
            else:
                frappe.db.set_value('Attendance',att.name,'total_overtime_hours',"00:00:00")
                frappe.db.set_value('Attendance',att.name,'overtime_hours',"0.0")
        
        if att.attendance_regularize and att.attendance_regularize is not None:
            if frappe.db.exists("Attendance Regularize",{'name':att.attendance_regularize,'over_time':1}):
                ot=frappe.db.get_value("Attendance Regularize",{'name':att.attendance_regularize,'over_time':1},['corrected_ot'])
                ot_hours = ot.total_seconds() / 3600 if ot else 0
                frappe.db.set_value('Attendance',{'name':att.name},'total_overtime_hours',ot)
                frappe.db.set_value('Attendance',{'name':att.name},'overtime_hours',ot_hours)
    for att in attendance:
        # based on the overtime hours, OT request is created for the employee
        ot=frappe.db.get_value('Attendance',{'name':att.name},['overtime_hours'])
        if att.shift and (att.in_time or att.session_from_time) and (att.out_time or att.session_to_time) and ot:
            ot_applicable = frappe.get_value("Employee",{'name':att.employee},['ot_applicable'])
            if ot_applicable == 1 :
                from datetime import datetime, time
                in_time = att.in_time
                out_time = att.out_time
                if att.on_duty_application is not None:
                    if not out_time:
                        total_seconds_to = int(att.session_to_time.total_seconds())
                        hours_to, remainder = divmod(total_seconds_to, 3600)
                        minutes_to, seconds_to = divmod(remainder, 60)
                        session_to_time_as_time = datetime.time(datetime(1, 1, 1, hours_to, minutes_to, seconds_to))
                        session_to_time_as_datetime = datetime.combine(att.attendance_date, session_to_time_as_time)
                        out_time = session_to_time_as_datetime
                    else:
                        session_to_time_as_time = (datetime.min + att.session_to_time).time()
                        if out_time.time() > session_to_time_as_time:
                            out_time = att.out_time
                        else:
                            out_time = datetime.combine(out_time.date(), session_to_time_as_time)
                    if not in_time:
                        total_seconds_from = int(att.session_from_time.total_seconds())
                        hours_from, remainder = divmod(total_seconds_from, 3600)
                        minutes_from, seconds_from = divmod(remainder, 60)
                        session_from_time_as_time = datetime.time(datetime(1, 1, 1, hours_from, minutes_from, seconds_from))
                        session_from_time_as_datetime = datetime.combine(att.attendance_date, session_from_time_as_time)
                        in_time = session_from_time_as_datetime
                    else:
                        session_from_time_as_time = (datetime.min + att.session_from_time).time()
                        if in_time.time() < session_from_time_as_time:
                            in_time = att.in_time
                        else:
                            in_time = datetime.combine(in_time.date(), session_from_time_as_time)
                else:
                    in_time = att.in_time
                    out_time = att.out_time
                if in_time is not None and isinstance(in_time, str):
                    in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
                if out_time is not None and isinstance(out_time, str):
                    out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')

                if frappe.db.exists('Overtime Request',{'ot_date':att.attendance_date,'employee':att.employee,'ot_from_od':0,'docstatus':('!=','2')}):
                    ot = frappe.get_doc("Overtime Request",{'ot_date':att.attendance_date,'employee':att.employee,'docstatus':('!=','2')})
                    att_ot=frappe.db.get_value("Attendance",{'name':att.name},['overtime_hours'])
                    ot.employee = att.employee
                    ot.employee_name = att.employee_name
                    ot.department = frappe.get_value("Employee",{'name':att.employee},['department'])
                    ot.designation = frappe.get_value("Employee",{'name':att.employee},['designation'])
                    ot.ot_date = att.attendance_date
                    ot.shift = att.shift
                    ot.from_time = in_time.time()
                    ot.to_time = out_time.time()
                    ot.biometric_checkin = in_time
                    ot.biometric_checkinout = out_time
                    ot.total_worked_hours = att.total_working_hours
                    ot.ot_applicable = 1
                    ot.ot_hours = att_ot
                    ot.attendance = att.name
                    ot.save(ignore_permissions=True)
                    frappe.db.commit()
                    frappe.db.set_value('Attendance',att.name,'overtime_request',ot.name)
                if not frappe.db.exists('Overtime Request',{'ot_date':att.attendance_date,'employee':att.employee,'docstatus':('!=','2')}):
                    ot = frappe.new_doc("Overtime Request")
                    att_ot=frappe.db.get_value("Attendance",{'name':att.name},['overtime_hours'])
                    ot.employee = att.employee
                    ot.employee_name = att.employee_name
                    ot.department = frappe.get_value("Employee",{'name':att.employee},['department'])
                    ot.designation = frappe.get_value("Employee",{'name':att.employee},['designation'])
                    ot.ot_date = att.attendance_date
                    ot.payroll_date = att.attendance_date
                    ot.shift = att.shift
                    # ot.reason= 'Automatically Created'
                    ot.from_time = in_time.time()
                    ot.to_time = out_time.time()
                    ot.biometric_checkin = in_time
                    ot.biometric_checkinout = out_time
                    ot.total_worked_hours = att.total_working_hours
                    ot.ot_applicable = 1
                    ot.ot_hours = att_ot
                    ot.attendance = att.name
                    ot.insert(ignore_permissions=True)
                    frappe.db.commit()
                    frappe.db.set_value('Attendance',att.name,'overtime_request',ot.name)


@frappe.whitelist()
def check_holiday(date, emp):
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
                if holiday[0].others == "DH":
                    status = "NPD"
                else:
                    status = holiday[0].others
        else:
            status = 'Not Joined'
    return status

def get_checkin_shift(att_time,employee):
    # method to fetch shift based on the checkin start and end time
    shift=''
    shift1 = frappe.db.get_value('Shift Type',{'name':'I'},['checkin_start_time','checkin_end_time'])
    shift2 = frappe.db.get_value('Shift Type',{'name':'II'},['checkin_start_time','checkin_end_time'])
    shift3 = frappe.db.get_value('Shift Type',{'name':'III'},['checkin_start_time','checkin_end_time'])
    shiftg = frappe.db.get_value('Shift Type',{'name':'G'},['checkin_start_time','checkin_end_time'])
    shiftn = frappe.db.get_value('Shift Type',{'name':'N'},['checkin_start_time','checkin_end_time'])
    shiftlg = frappe.db.get_value('Shift Type',{'name':'Lady Guard'},['checkin_start_time','checkin_end_time'])
    shifthk = frappe.db.get_value('Shift Type',{'name':'HK'},['checkin_start_time','checkin_end_time'])
    shiftso = frappe.db.get_value('Shift Type',{'name':'SO'},['checkin_start_time','checkin_end_time'])
    shiftseq = frappe.db.get_value('Shift Type',{'name':'SEQ'},['checkin_start_time','checkin_end_time'])
    shiftseqn = frappe.db.get_value('Shift Type',{'name':'SS-N'},['checkin_start_time','checkin_end_time'])
    shiftgar = frappe.db.get_value('Shift Type',{'name':'Gardner'},['checkin_start_time','checkin_end_time'])
    att_time_seconds = att_time.hour * 3600 + att_time.minute * 60 + att_time.second
    department = frappe.get_value("Employee",{'name':employee},["department"])
    designation = frappe.get_value("Employee",{'name':employee},["designation"])
    gender = frappe.get_value("Employee",{'name':employee},["gender"])
    if department == "HK":
        if shifthk[0].total_seconds() < att_time_seconds < shifthk[1].total_seconds():
            shift = "HK"
    elif department == "GARDENER":
        if shiftgar[0].total_seconds() < att_time_seconds < shiftgar[1].total_seconds():
            shift = "Gardner"
    elif department == "Security":
        if gender == "Female":
            if shiftlg[0].total_seconds() < att_time_seconds < shiftlg[1].total_seconds():
                shift = "Lady Guard"
        else:
            if designation=="Security Officer":
                if shiftso[0].total_seconds() < att_time_seconds < shiftso[1].total_seconds():
                    shift = 'SO'
            else:
                if shiftseqn[0].total_seconds() < att_time_seconds < shiftseqn[1].total_seconds():
                    shift = 'SS-N'
                if shiftseq[0].total_seconds() < att_time_seconds < shiftseq[1].total_seconds():
                    shift = 'SEQ'
    else:
        if shift1[0].total_seconds() < att_time_seconds < shift1[1].total_seconds():
            shift = 'I'
        if shift2[0].total_seconds() < att_time_seconds < shift2[1].total_seconds():
            shift = 'II'
        if shift3[0].total_seconds() < att_time_seconds < shift3[1].total_seconds():
            shift ='III'
        if shiftg[0].total_seconds() < att_time_seconds < shiftg[1].total_seconds():
            shift ='G'
        if shiftn[0].total_seconds() < att_time_seconds < shiftn[1].total_seconds():
            shift = 'N'  
    return shift


def att_shift_status_employee(from_date,to_date,employee):
    attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'docstatus':('!=','2'),'employee':employee},['*'])  
    ss=''
    for att in attendance:
        status = status_map.get(att.status, "")
        leave = status_map.get(att.leave_type, "")
        hh = check_holiday(att.attendance_date,att.employee)
        if hh:
            if status == "P" and not att.on_duty_application != "":
                ss = "OD-" + hh
            else:
                if status == "P" and att.shift == "N":
                    ss = "PN/" + hh
                if status == "P" and att.shift == "III":
                    ss = "PIII/" + hh
                if status == "P" and not att.shift == "N" and not att.shift == 'III':
                    ss = "P/" + hh
        else:
            if status == "P" and att.shift == "N":
                ss = "P/N"
            if status == "P" and att.shift == "III":
                ss = "PN/III"
            if status == "P" and not att.shift == "N" and not att.shift == 'III':
                ss = "P"
        if status == "A":
            hh = check_holiday(att.attendance_date,att.employee)
            if hh:
                ss = hh
            else:
                ss = "AB"
        if status == "HD" and leave != '':
            
            ss = "PP/" + leave
        if status == "HD" and leave == '':
            hh = check_holiday(att.attendance_date,att.employee)
            if hh:
                ss = "HD/" + hh
            else:
                ss = "P/AB" 
        if status == "On Leave" and leave != '':
            ss = leave
        if status == "On Leave" and leave == '':
            ss = "On Leave"
        if att.on_duty_application:
            hh = check_holiday(att.attendance_date,att.employee)
            session = frappe.get_value("On Duty Application",{'name':att.on_duty_application,'docstatus':('!=',2)},['session'])
            if hh:
                ss=ss = "OD-" + hh
            else:
                if session == "Full day":
                    ss = "P(OD)"
                if session == "First Half":
                    ss = "OD/P"
                if session == "Second Half":		
                    ss = "P/OD"
                if session == "Flexible":
                    ss = "P-OD"
        
    return str(ss)

@frappe.whitelist()
def att_draft_to_submit_with_employee(from_date, to_date, employee):
    draft = frappe.db.get_all('Attendance',
                              filters = {
                                  'docstatus': 0,
                                  'attendance_date' : ['between', [from_date, to_date]],
                                  'employee': employee
                              },
                              fields = ['name'])
    
    for d in draft:
        att_doc = frappe.get_doc("Attendance", d['name'])
        att_doc.submit()

    return 'ok'

@frappe.whitelist()
def att_draft_to_submit_without_employee(from_date, to_date):
    draft = frappe.db.get_all('Attendance',
                              filters = {
                                  'docstatus': 0,
                                  'attendance_date': ['between', [from_date, to_date]]
                              })
    
    for d in draft:
        att_doc = frappe.get_doc("Attendance", d)
        att_doc.submit()

    return 'ok'

@frappe.whitelist()
def create_npd_allowance(from_date,to_date,employee):
    # method to mark the attendance status
    attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'docstatus':('!=','2'),"employee":employee},['*'])
    od_wh=0.0
    for att in attendance:

        hh = check_holiday(att.attendance_date,att.employee)
        if hh and hh=='NPD':
            # conditions when OD application is present
            if (att.in_time or (att.session_from_time and att.on_duty_application)) and (att.out_time or (att.session_to_time and att.on_duty_application)) and (att.shift and att.shift not in ('Gardner','HK','Lady Guard','SS-N','SEQ','SO')):
                in_time = att.in_time
                out_time = att.out_time
                if att.on_duty_application is not None:
                    if att.session_from_time and att.session_to_time:
                        od=frappe.get_doc("On Duty Application",att.on_duty_application)
                        if not out_time:
                            total_seconds_to = int(att.session_to_time.total_seconds())
                            hours_to, remainder = divmod(total_seconds_to, 3600)
                            minutes_to, seconds_to = divmod(remainder, 60)
                            session_to_time_as_time = datetime.time(datetime(1, 1, 1, hours_to, minutes_to, seconds_to))
                            session_to_time_as_datetime = datetime.combine(att.attendance_date, session_to_time_as_time)
                            out_time = session_to_time_as_datetime
                        else:
                            # compare actual out time and session end time, greater one is taken for calculation
                            session_to_time_as_time = (datetime.min + att.session_to_time).time()
                            if out_time.time() > session_to_time_as_time:
                                out_time = att.out_time
                            else:
                                out_time = datetime.combine(out_time.date(), session_to_time_as_time)
                        if not in_time:
                            total_seconds_from = int(att.session_from_time.total_seconds())
                            hours_from, remainder = divmod(total_seconds_from, 3600)
                            minutes_from, seconds_from = divmod(remainder, 60)
                            session_from_time_as_time = datetime.time(datetime(1, 1, 1, hours_from, minutes_from, seconds_from))
                            session_from_time_as_datetime = datetime.combine(att.attendance_date, session_from_time_as_time)
                            in_time = session_from_time_as_datetime
                        else:
                            # compare actual in time and session from time, least one is taken for calculation
                            session_from_time_as_time = (datetime.min + att.session_from_time).time()
                            if in_time.time() < session_from_time_as_time:
                                in_time = att.in_time
                            else:
                                in_time = datetime.combine(in_time.date(), session_from_time_as_time)
                shift_time_start = frappe.get_value("Shift Type", {'name': att.shift}, ["start_time"])
                shift_start_time = datetime.strptime(str(shift_time_start), '%H:%M:%S').time()
                shift_time_end = frappe.get_value("Shift Type", {'name': att.shift}, ["end_time"])
                shift_end_time = datetime.strptime(str(shift_time_end), '%H:%M:%S').time()
                in_time_calc = datetime.combine(in_time.date(), shift_start_time) 
                end_date=in_time.date()
                if att.shift=='III' or att.shift=='N':
                    end_date=add_days(att.attendance_date,1)
                out_time_calc = datetime.combine(end_date, shift_end_time) 
                if in_time<in_time_calc:
                    in_time=in_time_calc
                if out_time>out_time_calc:
                    out_time=out_time_calc
                emp_shift=frappe.get_doc("Shift Type",att.shift)
                time_ranges = []
                for b in emp_shift.break_time:
                    if b.breaktime_from and b.breaktime_to:
                        start_str = str(b.breaktime_from)
                        end_str = str(b.breaktime_to)
                        time_ranges.append((start_str, end_str))
                if isinstance(in_time, str):
                    in_time = datetime.strptime(in_time, "%H:%M:%S")
                if isinstance(out_time, str):
                    out_time = datetime.strptime(out_time, "%H:%M:%S")
                if out_time>in_time:
                    wh_diff=time_diff_in_hours(out_time,in_time)
                else:
                    wh_diff=0
                for range_start, range_end in time_ranges:
                    if att.shift=='N' or att.shift=='III':
                        if (datetime.strptime(range_start, "%H:%M:%S").time() < in_time.time() and datetime.strptime(range_start, "%H:%M:%S").time() < out_time.time() ):
                            range_start_dt = datetime.combine(out_time.date(), datetime.strptime(range_start, "%H:%M:%S").time())
                            range_end_dt = datetime.combine(out_time.date(), datetime.strptime(range_end, "%H:%M:%S").time())
                        else:
                            range_start_dt = datetime.combine(in_time.date(), datetime.strptime(range_start, "%H:%M:%S").time())
                            range_end_dt = datetime.combine(in_time.date(), datetime.strptime(range_end, "%H:%M:%S").time())
                    else:
                        range_start_dt = datetime.combine(in_time.date(), datetime.strptime(range_start, "%H:%M:%S").time())
                        range_end_dt = datetime.combine(in_time.date(), datetime.strptime(range_end, "%H:%M:%S").time())
                    if in_time < range_end_dt and out_time > range_start_dt:
                        overlap_start = max(in_time, range_start_dt)
                        overlap_end = min(out_time, range_end_dt)
                        overlap_duration = time_diff_in_hours(overlap_end, overlap_start)
                        wh_diff -= overlap_duration
                            
                if wh_diff>=0.5:
                    if wh_diff < 1:
                        wh_diff=0.5
                    else:
                        integer_part = int(wh_diff)
                        fractional_part = wh_diff - integer_part
                        if 0 <= fractional_part < 0.50:
                            wh_diff = integer_part
                        elif 0.50 <= fractional_part <= 0.99:
                            wh_diff = integer_part + 0.5
                    wh_hrs=wh_diff
                    wh_diff=wh_diff*62.5
                    if frappe.db.exists("DH Approval",{'dh_date':att.attendance_date,'employee':att.employee,'docstatus':['!=',2]}):
                        dh_name=frappe.db.get_value("DH Approval",{'dh_date':att.attendance_date,'employee':att.employee,'docstatus':['!=',2]},['name'])
                        dh_doc=frappe.get_doc('DH Approval',dh_name)
                        dh_doc.dh_allowance=wh_diff
                        dh_doc.attendance=att.name
                        dh_doc.payroll_date_npd=att.attendance_date
                        dh_doc.shift=att.shift
                        dh_doc.shift_working_hours=wh_hrs
                        dh_doc.overtime_hours=att.total_overtime_hours
                        dh_doc.extra_hours=att.total_extra_hours
                        dh_doc.total_working_hours=att.total_working_hours
                        dh_doc.save(ignore_permissions=True)
                    else:
                        dh_doc=frappe.new_doc('DH Approval')
                        dh_doc.dh_date=att.attendance_date
                        dh_doc.employee=att.employee
                        dh_doc.attendance=att.name
                        dh_doc.payroll_date_npd=att.attendance_date
                        # dh_doc.job__work='Automatically Created'
                        dh_doc.shift_working_hours=wh_hrs
                        dh_doc.overtime_hours=att.total_overtime_hours
                        dh_doc.extra_hours=att.total_extra_hours
                        dh_doc.shift=att.shift
                        dh_doc.total_working_hours=att.total_working_hours
                        dh_doc.dh_allowance=wh_diff
                        dh_doc.insert(ignore_permissions=True)
                        frappe.db.commit()


@frappe.whitelist()
def create_npd_allowance_att(from_date,to_date):
    # method to mark the attendance status
    attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'docstatus':('!=','2')},['*'])
    od_wh=0.0
    for att in attendance:

        hh = check_holiday(att.attendance_date,att.employee)
        if hh and hh=='NPD':
            # conditions when OD application is present
            if (att.in_time or (att.session_from_time and att.on_duty_application)) and (att.out_time or (att.session_to_time and att.on_duty_application)) and (att.shift and att.shift not in ('Gardner','HK','Lady Guard','SS-N','SEQ','SO')):
                in_time = att.in_time
                out_time = att.out_time
                if att.on_duty_application is not None:
                    if att.session_from_time and att.session_to_time:
                        od=frappe.get_doc("On Duty Application",att.on_duty_application)
                        if not out_time:
                            total_seconds_to = int(att.session_to_time.total_seconds())
                            hours_to, remainder = divmod(total_seconds_to, 3600)
                            minutes_to, seconds_to = divmod(remainder, 60)
                            session_to_time_as_time = datetime.time(datetime(1, 1, 1, hours_to, minutes_to, seconds_to))
                            session_to_time_as_datetime = datetime.combine(att.attendance_date, session_to_time_as_time)
                            out_time = session_to_time_as_datetime
                        else:
                            # compare actual out time and session end time, greater one is taken for calculation
                            session_to_time_as_time = (datetime.min + att.session_to_time).time()
                            if out_time.time() > session_to_time_as_time:
                                out_time = att.out_time
                            else:
                                out_time = datetime.combine(out_time.date(), session_to_time_as_time)
                        if not in_time:
                            total_seconds_from = int(att.session_from_time.total_seconds())
                            hours_from, remainder = divmod(total_seconds_from, 3600)
                            minutes_from, seconds_from = divmod(remainder, 60)
                            session_from_time_as_time = datetime.time(datetime(1, 1, 1, hours_from, minutes_from, seconds_from))
                            session_from_time_as_datetime = datetime.combine(att.attendance_date, session_from_time_as_time)
                            in_time = session_from_time_as_datetime
                        else:
                            # compare actual in time and session from time, least one is taken for calculation
                            session_from_time_as_time = (datetime.min + att.session_from_time).time()
                            if in_time.time() < session_from_time_as_time:
                                in_time = att.in_time
                            else:
                                in_time = datetime.combine(in_time.date(), session_from_time_as_time)
                shift_time_start = frappe.get_value("Shift Type", {'name': att.shift}, ["start_time"])
                shift_start_time = datetime.strptime(str(shift_time_start), '%H:%M:%S').time()
                shift_time_end = frappe.get_value("Shift Type", {'name': att.shift}, ["end_time"])
                shift_end_time = datetime.strptime(str(shift_time_end), '%H:%M:%S').time()
                in_time_calc = datetime.combine(in_time.date(), shift_start_time) 
                end_date=in_time.date()
                if att.shift=='III' or att.shift=='N':
                    end_date=add_days(att.attendance_date,1)
                out_time_calc = datetime.combine(end_date, shift_end_time) 
                if in_time<in_time_calc:
                    in_time=in_time_calc
                if out_time>out_time_calc:
                    out_time=out_time_calc
                emp_shift=frappe.get_doc("Shift Type",att.shift)
                time_ranges = []
                for b in emp_shift.break_time:
                    if b.breaktime_from and b.breaktime_to:
                        start_str = str(b.breaktime_from)
                        end_str = str(b.breaktime_to)
                        time_ranges.append((start_str, end_str))
                if isinstance(in_time, str):
                    in_time = datetime.strptime(in_time, "%H:%M:%S")
                if isinstance(out_time, str):
                    out_time = datetime.strptime(out_time, "%H:%M:%S")
                if out_time>in_time:
                    wh_diff=time_diff_in_hours(out_time,in_time)
                else:
                    wh_diff=0
                for range_start, range_end in time_ranges:
                    if att.shift=='N' or att.shift=='III':
                        if (datetime.strptime(range_start, "%H:%M:%S").time() < in_time.time() and datetime.strptime(range_start, "%H:%M:%S").time() < out_time.time() ):
                            range_start_dt = datetime.combine(out_time.date(), datetime.strptime(range_start, "%H:%M:%S").time())
                            range_end_dt = datetime.combine(out_time.date(), datetime.strptime(range_end, "%H:%M:%S").time())
                        else:
                            range_start_dt = datetime.combine(in_time.date(), datetime.strptime(range_start, "%H:%M:%S").time())
                            range_end_dt = datetime.combine(in_time.date(), datetime.strptime(range_end, "%H:%M:%S").time())
                    else:
                        range_start_dt = datetime.combine(in_time.date(), datetime.strptime(range_start, "%H:%M:%S").time())
                        range_end_dt = datetime.combine(in_time.date(), datetime.strptime(range_end, "%H:%M:%S").time())
                    if in_time < range_end_dt and out_time > range_start_dt:
                        overlap_start = max(in_time, range_start_dt)
                        overlap_end = min(out_time, range_end_dt)
                        overlap_duration = time_diff_in_hours(overlap_end, overlap_start)
                        wh_diff -= overlap_duration
                        
                if wh_diff>=0.5:
                    if wh_diff < 1:
                        wh_diff=0.5
                    else:
                        integer_part = int(wh_diff)
                        fractional_part = wh_diff - integer_part
                        if 0 <= fractional_part < 0.50:
                            wh_diff = integer_part
                        elif 0.50 <= fractional_part <= 0.99:
                            wh_diff = integer_part + 0.5
                    wh_hrs=wh_diff
                    wh_diff=wh_diff*62.5
                    if frappe.db.exists("DH Approval",{'dh_date':att.attendance_date,'employee':att.employee,'docstatus':['!=',2]}):
                        dh_name=frappe.db.get_value("DH Approval",{'dh_date':att.attendance_date,'employee':att.employee,'docstatus':['!=',2]},['name'])
                        dh_doc=frappe.get_doc('DH Approval',dh_name)
                        dh_doc.dh_allowance=wh_diff
                        dh_doc.attendance=att.name
                        dh_doc.payroll_date_npd=att.attendance_date
                        dh_doc.shift=att.shift
                        dh_doc.shift_working_hours=wh_hrs
                        dh_doc.overtime_hours=att.total_overtime_hours
                        dh_doc.extra_hours=att.total_extra_hours
                        dh_doc.total_working_hours=att.total_working_hours
                        dh_doc.save(ignore_permissions=True)
                    else:
                        dh_doc=frappe.new_doc('DH Approval')
                        dh_doc.dh_date=att.attendance_date
                        dh_doc.employee=att.employee
                        dh_doc.attendance=att.name
                        # dh_doc.job__work='Automatically Created'
                        dh_doc.shift_working_hours=wh_hrs
                        dh_doc.overtime_hours=att.total_overtime_hours
                        dh_doc.extra_hours=att.total_extra_hours
                        dh_doc.shift=att.shift
                        dh_doc.total_working_hours=att.total_working_hours
                        dh_doc.dh_allowance=wh_diff
                        dh_doc.insert(ignore_permissions=True)
                        frappe.db.commit()




@frappe.whitelist()
def add_ot_from_od(from_date,to_date):
    od_application=frappe.db.get_all("Overtime Request",{"docstatus":['!=',2],'od_date':["!=",''],'od_date':('between',(from_date,to_date)),'ot_from_od':1},['*'])
    if od_application:
        for od in od_application:
            if frappe.db.exists('Attendance',{'attendance_date':od.od_date,'docstatus':('!=','2'),'employee':od.employee}):
                attendance=frappe.db.get_value('Attendance',{'attendance_date':od.od_date,'docstatus':('!=','2'),'employee':od.employee},['name'])
                frappe.db.set_value("Attendance",attendance,'overtime_hours',od.ot_hours)

@frappe.whitelist()
def add_ot_from_od_employee(from_date,to_date,employee):
    od_application=frappe.db.get_all("Overtime Request",{"docstatus":['!=',2],'od_date':["!=",''],'od_date':('between',(from_date,to_date)),'ot_from_od':1,'employee':employee},['*'])
    if od_application:
        for od in od_application:
            if frappe.db.exists('Attendance',{'attendance_date':od.od_date,'docstatus':('!=','2'),'employee':od.employee}):
                attendance=frappe.db.get_value('Attendance',{'attendance_date':od.od_date,'docstatus':('!=','2'),'employee':od.employee},['name'])
                frappe.db.set_value("Attendance",attendance,'overtime_hours',od.ot_hours)

@frappe.whitelist()
def update_ot_hrs(from_date,to_date):
    od_application=frappe.db.get_all("Attendance",{"docstatus":['!=',2],'attendance_date':('between',(from_date,to_date))},['name','in_time','out_time','status'])
    if od_application:
        for od in od_application:
            if od.status=='On Leave':
                if (od.in_time==None and od.out_time==None) or od.in_time==None or od.out_time==None :
                    frappe.db.set_value("Attendance",od.name,'total_overtime_hours','00:00:00')
                    frappe.db.set_value("Attendance",od.name,'total_working_hours','00:00:00')
                    frappe.db.set_value("Attendance",od.name,'total_extra_hours','00:00:00')
                
@frappe.whitelist()
def update_ot_hrs_emp(from_date,to_date,employee):
    od_application=frappe.db.get_all("Attendance",{'employee':employee,"docstatus":['!=',2],'attendance_date':('between',(from_date,to_date))},['name','in_time','out_time','status'])
    if od_application:
        for od in od_application:
            if od.status=='On Leave':
                if (od.in_time==None and od.out_time==None) or od.in_time==None or od.out_time==None :
                    frappe.db.set_value("Attendance",od.name,'total_overtime_hours','00:00:00')
                    frappe.db.set_value("Attendance",od.name,'total_working_hours','00:00:00')
                    frappe.db.set_value("Attendance",od.name,'total_extra_hours','00:00:00')    



@frappe.whitelist()
def update_leave_attendance_status(from_date, to_date):
    attendances = frappe.db.get_all("Attendance",{"attendance_date": ["between", [from_date, to_date]],"docstatus": ['!=',2] ,'leave_application':['!=','']}, ["name", "employee", "attendance_date", "leave_application"])
    for att in attendances:
        if att.leave_application:
            leave_doc=frappe.get_doc('Leave Application',att.leave_application)
            if leave_doc.half_day:
                if leave_doc.half_day_date==att.attendance_date:
                    frappe.db.set_value("Attendance",att.name,"status", "Half Day")
                else:
                    frappe.db.set_value("Attendance",att.name, "status", "On Leave")
            else:
                frappe.db.set_value("Attendance",att.name, "status", "On Leave")



# @frappe.whitelist()
# def update_leave_attendance_status_employee(from_date, to_date, employee):
#     attendances = frappe.db.get_all("Attendance",{"attendance_date": ["between", [from_date, to_date]],"docstatus": ['!=',2], "employee":employee }, ["name", "employee", "attendance_date"])
#     for att in attendances:
#         leave = frappe.db.get_value("Leave Application",{"employee": att.employee,"from_date": ["<=", att.attendance_date],"to_date": [">=", att.attendance_date],"docstatus": 1, 'workflow_state': "Approved"},["name", "half_day"],as_dict=True)
#         if leave:
#             if leave.half_day:
#                 frappe.db.set_value("Attendance",att.name,"status", "Half Day")
#                 frappe.db.set_value("Attendance",att.name,"leave_application",leave.name)
#             else:
#                 frappe.db.set_value("Attendance",att.name, "status", "On Leave")
#                 frappe.db.set_value("Attendance",att.name,"leave_application",leave.name)

@frappe.whitelist()
def update_leave_attendance_status_employee(from_date, to_date, employee):
    attendances = frappe.db.get_all("Attendance",{"attendance_date": ["between", [from_date, to_date]],"docstatus": ["!=", 2],"employee": employee},["name", "employee", "attendance_date"])
    for att in attendances:
        leave = frappe.db.get_value("Leave Application",{"employee": att.employee,"from_date": ["<=", att.attendance_date],"to_date": [">=", att.attendance_date],"docstatus": 1,"workflow_state": "Approved"},["name", "half_day", "half_day_date"],as_dict=True)
        if leave:
            if(leave.half_day and leave.half_day_date and leave.half_day_date == att.attendance_date):
                frappe.db.set_value("Attendance",att.name,{"status": "Half Day","leave_application": leave.name})
            else:
                frappe.db.set_value("Attendance",att.name,{"status": "On Leave","leave_application": leave.name })

# @frappe.whitelist()
# def update_leave_attendance_status(from_date, to_date):
#     attendances = frappe.db.get_all("Attendance",{"attendance_date": ["between", [from_date, to_date]],"docstatus": ['!=',2] }, ["name", "employee", "attendance_date"])
#     for att in attendances:
#         leave = frappe.db.get_value("Leave Application",{"employee": att.employee,"from_date": ["<=", att.attendance_date],"to_date": [">=", att.attendance_date],"docstatus": 1, 'workflow_state': "Approved"},["name", "half_day", "half_day_date"],as_dict=True)
#         if leave:
#             if leave.half_day:
#                 frappe.db.set_value("Attendance",att.name,"status", "Half Day")
#                 frappe.db.set_value("Attendance",att.name,"leave_application",leave.name)
#             else:
#                 frappe.db.set_value("Attendance",att.name, "status", "On Leave")
#                 frappe.db.set_value("Attendance",att.name,"leave_application",leave.name)


@frappe.whitelist()
def update_leave_attendance_status(from_date, to_date):
    attendances = frappe.db.get_all("Attendance",{"attendance_date": ["between", [from_date, to_date]],"docstatus": ["!=", 2]},["name", "employee", "attendance_date"])
    for att in attendances:
        leave = frappe.db.get_value("Leave Application",{"employee": att.employee,"from_date": ["<=", att.attendance_date],"to_date": [">=", att.attendance_date], "docstatus": 1,"workflow_state": "Approved" },["name", "half_day", "half_day_date"], as_dict=True)
        if leave:
            if leave.half_day and leave.half_day_date == att.attendance_date:
                frappe.db.set_value("Attendance",att.name,{"status": "Half Day","leave_application": leave.name })
            else:
                frappe.db.set_value("Attendance",att.name,{"status": "On Leave", "leave_application": leave.name} )
    # frappe.db.commit()

def timedelta_to_time(td):
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return time(hours % 24, minutes, seconds)
