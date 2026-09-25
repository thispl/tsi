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
def cron_job1():
	job = frappe.db.exists('Scheduled Job Type', 'update_relieving_date')
	if not job:
		sjt = frappe.new_doc("Scheduled Job Type")  
		sjt.update({
			"method" : 'tsi.employee_custom.update_relieving_date',
			"frequency" : 'Cron',
			"cron_format" : '30 00 * * *'
		})
		sjt.save(ignore_permissions=True)

# @frappe.whitelist()
# def update_mis_status_on_submit(doc, method):
#     # Get the employee's name from the Full and Final Statement record
#     employee = doc.employee

#     # Update the MIS status of the employee to "Left"
#     employee_doc = frappe.get_doc('Employee', employee)
#     employee_doc.status = 'Left'
#     employee_doc.save()


@frappe.whitelist()
def validate_leave_dates(doc, method):
    try:
        previous_leave_app = frappe.get_all(
            'Leave Application',
            filters={
                'employee': doc.employee,
                'from_date': ['<=', doc.from_date],
                'to_date': ['>=', doc.from_date],
                'workflow_state': "Approved",
                'leave_type': ['in', ['Earned Leave', 'Compensatory Off']]
            },
            fields=['name', 'from_date', 'to_date'],
            order_by='to_date DESC',
            limit=1
        )

        if previous_leave_app:
            last_leave_app = previous_leave_app[0]
            if last_leave_app.to_date >= doc.from_date:
                frappe.throw(_("Cannot apply Casual Leave before or on the same day as the previous Earned Leave or Compensatory Off"))

        next_leave_app = frappe.get_all(
            'Leave Application',
            filters={
                'employee': doc.employee,
                'from_date': ['<=', doc.to_date],
                'to_date': ['>=', doc.to_date],
                'workflow_state': "Approved",
                'leave_type': 'Casual Leave'
            },
            fields=['name', 'from_date', 'to_date'],
            order_by='from_date ASC',
            limit=1
        )

        if next_leave_app:
            next_leave_app = next_leave_app[0]
            if next_leave_app.from_date <= doc.to_date:
                frappe.throw(_("Cannot apply Casual Leave after or on the same day as the next Casual Leave"))

    except Exception as e:
        frappe.log_error(f"Error in validate_leave_dates: {str(e)}")
        raise

# @frappe.whitelist()
# def validate_leave_application(employee, from_date, to_date):
#     try:
#         leave_type_list = ['Casual Leave', 'Compensatory Off']
        
#         existing_leave_applications = frappe.get_all(
#             'Leave Application',
#             filters={
#                 'employee': employee,
#                 'leave_type': ('in', leave_type_list),
#                 'from_date': ('<=', to_date),
#                 'to_date': ('>=', from_date)
#             },
#         )
        
#         if existing_leave_applications:
#             frappe.throw("An overlapping leave application already exists with Casual Leave or Compensatory Off type.")

#     except Exception as e:
#         frappe.log_error(f"Error in validate_leave_application: {str(e)}")
#         raise


# @frappe.whitelist()
# def check_earn_leave(frm_date):
#     date = add_days(frm_date,-15)
#     if not today() <= date:
#         frappe.throw("Earned leave must be applied before 15 days of the leave date")

# @frappe.whitelist()
# def check_earn_lve(to_date):
#     date = add_days(to_date,2)
#     if today() > date:
#         frappe.throw("you have exceed the two days of grace period")

def validate_earn_leave(doc, method):
    if doc.leave_type == 'Earned Leave':
        today = frappe.utils.nowdate()
        from_date = doc.from_date

        user_roles = frappe.get_roles(frappe.session.user)
        hr_roles = ['HR User', 'HR Manager']

        if any(role in user_roles for role in hr_roles):
            min_apply_days = 2  # Minimum days for HR Managers and HR Users
        else:
            min_apply_days = 15  # Default minimum days for other roles

        min_apply_date = frappe.utils.add_days(today, min_apply_days)

        if frappe.utils.date_diff(from_date, today) < 0:
            frappe.msgprint(_('Cannot apply for past dates.'))
            frappe.throw(_('Cannot apply for past dates.'))

        elif frappe.utils.date_diff(from_date, min_apply_date) < 0:
            frappe.msgprint(_('Earned Leaves must be applied at least {} days in advance.').format(min_apply_days))
            frappe.throw(_('Earned Leaves must be applied at least {} days in advance.').format(min_apply_days))

def validate_casual_leave(doc, method):
    if doc.leave_type == 'Casual Leave':
        today = frappe.utils.nowdate()
        from_date = doc.from_date

        user_roles = frappe.get_roles(frappe.session.user)
        hr_roles = ['HR User', 'HR Manager']

        if any(role in user_roles for role in hr_roles):
            min_apply_days = 2  # Minimum days for HR Managers and HR Users
        else:
            min_apply_days = 3  # Default minimum days for other roles

        min_apply_date = frappe.utils.add_days(today, min_apply_days)

        if frappe.utils.date_diff(from_date, today) < 0:
            frappe.msgprint(_('Cannot apply for past dates.'))
            frappe.throw(_('Cannot apply for past dates.'))

        elif frappe.utils.date_diff(from_date, min_apply_date) < 0:
            frappe.msgprint(_('Casual Leaves must be applied at least {} days in advance.').format(min_apply_days))
            frappe.throw(_('Casual Leaves must be applied at least {} days in advance.').format(min_apply_days))


def validate_combined_leave(doc, method):
    from_date = doc.from_date
    to_date = doc.to_date
    leave_type = doc.leave_type

    if leave_type == 'Casual Leave':
        if doc.get('custom_field_earned_leave') or doc.get('custom_field_complementary_off'):
            frappe.msgprint(_('Casual Leave cannot be combined with Earned Leave or Complementary Off.'))
            frappe.throw(_('Casual Leave cannot be combined with Earned Leave or Complementary Off.'))

        if doc.get('custom_field_from_time') or doc.get('custom_field_to_time'):
            frappe.msgprint(_('Casual Leave cannot have specific from_time and to_time.'))
            frappe.throw(_('Casual Leave cannot have specific from_time and to_time.'))

        if from_date != to_date:
            frappe.msgprint(_('Casual Leave should have the same from_date and to_date.'))
            frappe.throw(_('Casual Leave should have the same from_date and to_date.'))
        check_leave_overlap(doc)

def check_leave_overlap(doc):
    try:
        leave_applications = frappe.get_all(
            'Leave Application',
            filters={
                'employee': doc.employee,
                'docstatus': 1,
                'from_date': ['<=', doc.to_date],
                'to_date': ['>=', doc.from_date],
                'name': ['!=', doc.name]
            }
        )

        if leave_applications:
            frappe.throw(_('Leave application overlaps with existing leave(s).'))

    except Exception as e:
        frappe.log_error(f"Error in check_leave_overlap: {str(e)}")
        raise



# @frappe.whitelist()
# def update_relieving_date():
#     # updates the status as left and relieving date in employee MIS
#     rf=frappe.db.get_all("Resignation Form",{"docstatus":1},['*'])
#     today = datetime.now()
#     yesterday = today - timedelta(days=1)
#     formatted_date = yesterday.strftime("%Y-%m-%d")
#     for i in rf:
#         if str(i.relieving_date) == formatted_date:
#             value=frappe.get_all("Employee",["status","employee_name"])
#             for j in value:
#                 if i.employee_name==j.employee_name:
#                     frappe.db.set_value("Employee","name","status","Left")
#                     frappe.db.set_value("Employee","name","relieving_date",i.relieving_date)



@frappe.whitelist()
def update_att_checkin():
    checkin = frappe.db.sql("""update `tabEmployee Checkin` set attendance = '' """, as_dict=1)
    print(checkin)
    checkin = frappe.db.sql("""delete from `tabAttendance` """, as_dict=1)
    print(checkin)



def get_companies():
    va = frappe.get_all("Salary Component", filters={"monthly_salary_": 1}, fields=["name"])
    return [item['name'] for item in va]

# @frappe.whitelist()
# def salary_details(doc):
#     # method to get the salary details from the applicant for print format (called in jinja)
#     data = '<table class="table table-bordered" style="width:80%;margin-left:16mm;">' 
#     ware = frappe.get_doc("Job Applicant", doc.name)
#     border_color = "black" 
#     data += '<tr>'
#     data += '<td style="text-align:center; border: 1px solid {0};"><b>S.NO</b></td>'.format(border_color)  
#     data += '<td style="text-align:center; border: 1px solid {0};"><b>PARTICULARS</b></td>'.format(border_color)  
#     data += '<td style="text-align:center; border: 1px solid {0};"><b>AMOUNT (PER MONTHS) RS.</b></td>'.format(border_color)  
#     data += '<tr>'
#     a = 1

#     for item in ware.salary_details:
#         data += '<tr>'
#         data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, a)  
#         data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, item.particulars or '')  
#         data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, item.amount_per_month_rs or 0)  
#         data += '</tr>'
#         a += 1

#     data += '<tr>'
#     data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, a)  
#     data += '<td style="text-align:center; border: 1px solid {0};"><b>Total A</b></td>'.format(border_color)  
#     data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, doc.total or 0)  
#     data += '</tr>'
#     a += 1

#     for item in ware.yearly_salary_details:
#         data += '<tr>'
#         data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, a)  
#         data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, item.particulars or '')  
#         data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, item.amount_per_month_rs or 0)  
#         data += '</tr>'
#         a += 1

#     data += '<tr>'
#     data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, a)  
#     data += '<td style="text-align:center; border: 1px solid {0};"><b>Total B</b></td>'.format(border_color)  
#     data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, doc.total_b or 0)  
#     data += '</tr>'
#     a += 1

#     data += '<tr>'
#     data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, a)  
#     data += '<td style="text-align:center; border: 1px solid {0};"><b>Total A-B</b></td>'.format(border_color)  
#     data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, doc.total_a_b or 0)  
#     data += '</tr>'
#     data += '</table>'
#     return data


# @frappe.whitelist()
# def update_att(doc,method):
#     # attendance will be updated every time when checkin is updated
#     print("HI")
#     if doc.attendance != '' and doc.log_type == "IN":
#         print("HI")
#         if frappe.db.exists("Attendance",{'name':doc.attendance}):
#             att = frappe.get_doc("Attendance",{'name':doc.attendance})
#             att.in_time = doc.time
#             att.save(ignore_permissions=True)
#             frappe.db.commit()
#     elif doc.attendance != '' and doc.log_type == "OUT":
#         print("HI")
#         if frappe.db.exists("Attendance",{'name':doc.attendance}):
#             att = frappe.get_doc("Attendance",{'name':doc.attendance})
#             att.out_time = doc.time
#             att.save(ignore_permissions=True)
#             frappe.db.commit()
#     if frappe.db.exists("Attendance",{'name':doc.attendance}):
#         att = frappe.get_doc('Attendance',{'name':doc.attendance})
#         if att.shift and att.in_time and att.out_time :
#             if att.on_duty_application != "":
#                 if att.in_time and att.out_time:
#                     in_time = att.in_time
#                     out_time = att.out_time
#             else:
#                 if att.session_from_time and att.session_to_time: 
#                     in_time = att.session_from_time
#                     out_time = att.session_to_time
#             att_wh = time_diff_in_hours(out_time,in_time)
#             ly = frappe.get_value("Late Entry",{'employee':att.employee,'permission_date':att.attendance_date,'docstatus':('!=','2')},['late']) or 0
#             et = frappe.get_value("Early Out",{'employee':att.employee,'permission_date':att.attendance_date,'docstatus':('!=','2')},['out']) or 0
#             tot = ly + et
#             tot_lyet = tot/60
#             wh = float(att_wh) + float(tot_lyet)
#             decimal_hours = wh
#             hours, remainder = divmod(decimal_hours, 1)
#             minutes, seconds = divmod(remainder * 3600, 60)
#             time_str = f"{int(hours)} hours and {int(minutes)} minutes and {int(seconds)} seconds"
#             time_in_standard_format = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
#             frappe.db.set_value('Attendance', att.name, 'total_working_hours', time_in_standard_format)
#             frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
#             if wh < 4:
#                 frappe.db.set_value('Attendance',att.name,'status','Absent')
#             elif wh >= 4 and wh < 8:
#                 frappe.db.set_value('Attendance',att.name,'status','Half Day')
#             elif wh >= 8:
#                 frappe.db.set_value('Attendance',att.name,'status','Present')  
#             shift_st = frappe.get_value("Shift Type",{'name':att.shift},['start_time'])
#             shift_et = frappe.get_value("Shift Type",{'name':att.shift},['end_time'])
#             if att.shift in ["I","II","G"]:
#                 shift_tot = time_diff_in_hours(shift_et,shift_st)
#             elif att.shift == 'III':
#                 shift_tot = 8.0
#             elif att.shift == 'N':
#                 shift_tot = 8.5
#             ot_hours = time(0,0,0)
#             shift_hours = frappe.get_value("Shift Type",{'name':att.shift},['total_working_hours'])
#             hours, minutes, seconds = map(int, time_in_standard_format.split(':'))
#             time_in_standard_format_timedelta = timedelta(hours=hours, minutes=minutes, seconds=seconds)
#             hh = check_holiday(att.attendance_date,att.employee)
#             if not hh:
#                 if wh > shift_tot and time_in_standard_format_timedelta > shift_hours:
#                     print("HI")
#                     extra_hours_float = wh -  shift_tot 
#                     extra_hours = time_in_standard_format_timedelta - shift_hours
#                     time_diff = datetime.strptime(str(extra_hours), '%H:%M:%S').time()
#                     frappe.db.set_value('Attendance',att.name,'extra_hours',extra_hours_float)
#                     frappe.db.set_value('Attendance',att.name,'total_extra_hours',time_diff)
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
#                     frappe.db.set_value('Attendance',att.name,'total_overtime_hours',ot_hours)
#                     frappe.db.set_value('Attendance',att.name,'overtime_hours',ot_hr)
#                 else:
#                     frappe.db.set_value('Attendance',att.name,'extra_hours',"0.0")
#                     frappe.db.set_value('Attendance',att.name,'total_extra_hours',"00:00:00")
#                     frappe.db.set_value('Attendance',att.name,'total_overtime_hours',"00:00:00")
#                     frappe.db.set_value('Attendance',att.name,'overtime_hours',"0.0")
#             else:
#                 print("HII")
#                 extra_hours_float = wh  
#                 extra_hours = time_in_standard_format_timedelta 
#                 time_diff = datetime.strptime(str(extra_hours), '%H:%M:%S').time()
#                 print(att.name)
#                 print(extra_hours)
#                 frappe.db.set_value('Attendance',att.name,'extra_hours',extra_hours_float)
#                 frappe.db.set_value('Attendance',att.name,'total_extra_hours',time_diff)
#                 if time_diff.hour >= 1 :
#                     if time_diff.minute <= 29:
#                         ot_hours = time(time_diff.hour,0,0)
#                     else:
#                         ot_hours = time(time_diff.hour,30,0)
#                 elif time_diff.hour == 0 :
#                     if time_diff.minute <= 29:
#                         ot_hours = time(0,0,0)
#                     else:
#                         ot_hours = time(time_diff.hour,30,0)
#                 ftr = [3600,60,1]
#                 hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
#                 ot_hr = round(hr/3600,1)
#                 frappe.db.set_value('Attendance',att.name,'total_overtime_hours',ot_hours)
#                 frappe.db.set_value('Attendance',att.name,'overtime_hours',ot_hr)
#         else:
#             frappe.db.set_value('Attendance', att.name,'total_working_hours',"00:00:00")
#             frappe.db.set_value('Attendance', att.name,'working_hours',"0.0")
#             frappe.db.set_value('Attendance',att.name,'extra_hours',"0.0")
#             frappe.db.set_value('Attendance',att.name,'total_extra_hours',"00:00:00")
#             frappe.db.set_value('Attendance',att.name,'total_overtime_hours',"00:00:00")
#             frappe.db.set_value('Attendance',att.name,'overtime_hours',"0.0")



# def check_holiday(date, emp):
#     # method returns the holiday with it's short code, used to check that day is holiday or not
#     holiday_list = frappe.db.get_value('Employee', {'name': emp}, 'holiday_list')
#     holiday = frappe.db.sql("""select `tabHoliday`.holiday_date, `tabHoliday`.weekly_off ,`tabHoliday`.others
#                              from `tabHoliday List` 
#                              left join `tabHoliday` on `tabHoliday`.parent = `tabHoliday List`.name 
#                              where `tabHoliday List`.name = %s and holiday_date = %s""", 
#                              (holiday_list, date), as_dict=True)
#     doj = frappe.db.get_value("Employee", {'name': emp}, "date_of_joining")
#     status = ''

#     if holiday:
        
#         if doj < holiday[0].holiday_date:
#             if holiday[0].weekly_off == 1:
#                 status = "WW"
#             else:
#                 status = holiday[0].others
#         else:
#             status = 'Not Joined'
        
#     return status




# @frappe.whitelist()
# def monthly_in_out(start_date,end_date,category):
#     # jinja method used in report dashboard to print the monthly in and out report
#     data=""
#     dates = get_dates(start_date,end_date)
#     dates1 = get_date(start_date,end_date)
#     if category:
#         employees = frappe.get_all("Employee",{'employee_catagory':category,'status':'Active'},['*'])
#     else:
#         employees = frappe.get_all("Employee",{'status':'Active'},['*'])
#     for e in employees:
#         data +="""
#         <style>
#             .print-format {
#                 padding: 0px;
#             }
#             @media screen {
#                 .print-format {
#                     padding: 0in;
#                 }
#             }
#         </style>
#         <div class="container" style="page-break-inside:avoid"><p style="font-size:11px"><b>&nbsp; &nbsp;&nbsp;Employee Code/Name  </b>%s   <b>%s</b></p>"""%(e.name,e.employee_name)
#         data +='<div class="row"><div class="col-xs-6"><table width=50% border =1>'
#         data += "<tr style='font-size:6px;'><td style='font-size:6px;'><b><center>Day</center></b></td><td style='font-size:6px;'><b><center>Shift</center></b></td><td style='font-size:6px;'><b><center>Status</center></b></td><td style='font-size:6px;'><b><center>Time In</center></b></td><td style='font-size:6px;'><b><center>Time Out</center></b></td><td style='font-size:6px;'><b><center>Total Hours</center></b></td><td style='font-size:6px;'><b><center>Late</center></b></td><td style='font-size:6px;'><b><center>Early</center</b></td><td style='font-size:6px;'><b><center>OT</center</b></td></tr>"
#         total_ot = timedelta(0,0,0)
#         for date in dates:
#             dt = datetime.strptime(date,'%Y-%m-%d')
#             d = dt.strftime('%d')
#             shift = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'shift') or ''
#             status = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'shift_status') or ''
#             in_time = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'in_time')
#             if in_time is not None:
#                     formatted_time = in_time.strftime('%H:%M')
#             else:
#                 formatted_time = ''
#             out_time = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'out_time')
#             if out_time is not None:
#                     formatted_out_time = out_time.strftime('%H:%M')
#             else:
#                 formatted_out_time = ''
#             working_hours = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'total_working_hours') or ''
#             late = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'late_entry')
#             if late==1:
#                 late_entry=frappe.db.get_value("Late Entry",{"employee":e.name,"permission_date":date},'late')
#             else:
#                 late_entry=' '
#             early = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'early_exit')
#             if early==1:
#                 early_exit=frappe.db.get_value("Early Out",{"employee":e.name,"permission_date":date},'out')
#             else:
#                 early_exit=' '
#             overtime_hours = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'overtime_hours') or ''

#             data += "<tr style='font-size:6px;'><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"%(d,shift,status,formatted_time,formatted_out_time,working_hours or '',late_entry,early_exit,overtime_hours or '')
#         data += '</table></div>'
#         data += '<div class="col-xs-6"><table  border= 1 width=50%>'
#         data += "<tr style='font-size:6px;'><td style='font-size:6px;'><b><center>Day</center></b></td><td style='font-size:6px;'><b><center>Shift</center></b></td><td style='font-size:6px;'><b><center>Status</center></b></td><td style='font-size:6px;'><b><center>Time In</center></b></td><td style='font-size:6px;'><b><center>Time Out</center></b></td><td style='font-size:6px;'><b><center>Total Hours</center></b></td><td style='font-size:6px;'><b><center>Late</center></b></td><td style='font-size:6px;'><b><center>Early</center</b></td><td style='font-size:6px;'><b><center>OT</center</b></td></tr>"

#         # data += "<tr style='font-size:9px;2'><td><b><center>Day</center></b></td><td><b><center>Shift</center></b></td><td><b><center>Status</center></b></td><td><b><center>Time In</center></b></td><td><b><center>Time Out</center></b></td><td><b><center>Total Hours</center></b></td><td><b><center>Late</center></b></td><td><b><center>Early</center</b></td><td><b><center>OT</center</b></td></tr>"
#         total_ot = timedelta(0,0,0)
#         for date in dates1:
#             dt = datetime.strptime(date,'%Y-%m-%d')
#             d = dt.strftime('%d')
#             shift = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'shift') or ''
#             status = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'shift_status') or ''
#             in_time = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'in_time')
#             if in_time is not None:
#                     formatted_time = in_time.strftime('%H:%M')
#             else:
#                 formatted_time = ''
#             out_time = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'out_time')
#             if out_time is not None:
#                     formatted_out_time = out_time.strftime('%H:%M')
#             else:
#                 formatted_out_time = ''
#             working_hours = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'total_working_hours') or ''
#             late = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'late_entry')
#             if late==1:
#                 late_entry=frappe.db.get_value("Late Entry",{"employee":e.name,"permission_date":date},'late')
#             else:
          
#                 late_entry=' '
#                 early = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'early_exit')
#             if early==1:
#                 early_exit=frappe.db.get_value("Early Out",{"employee":e.name,"permission_date":date},'out')
#             else:
#                 early_exit=' '
#             overtime_hours = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'overtime_hours') or ''

#             data += "<tr style='font-size:6px;'><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"%(d,shift,status,formatted_time,formatted_out_time,working_hours or '',late_entry,early_exit,overtime_hours or '')

#         data += '</table></div></div></div>'
#     frappe.log_error(title='days',message=data)
#     return data

# def get_dates(start_date,end_date):
#     # method used to get the dates between the start and end date
#     no_of_days = date_diff(add_days(end_date, 1), start_date)
#     if no_of_days==31:
#         dates = [add_days(start_date,i) for i in range(0,16)]
#     else:
#         dates = [add_days(start_date,i) for i in range(0,15)]
#     return dates

# def get_date(start_date,end_date):
#     no_of_days = date_diff(add_days(end_date, 1), start_date)
#     if no_of_days==31:
#         dates = [add_days(start_date,i) for i in range(16,no_of_days)]
#     else:
#         dates = [add_days(start_date,i) for i in range(15,no_of_days)]
#     return dates

# @frappe.whitelist()
# def inactive_employee(doc,method):
#     # throw error when relieving date is set for active employees
#     if doc.status=="Active":
#         if doc.relieving_date:
#             throw(_("Please remove the relieving date for the Active Employee."))

@frappe.whitelist()
def automate_dh_approval():
    employee_check_ins = get_employee_check_ins()  # Retrieve employee Check-In data
    holidays = get_holidays()  # Retrieve list of holidays
    
    for employee_id, check_ins in employee_check_ins.items():
        for check_in_date in check_ins:  # Iterate over dates directly
            if check_in_date in holidays:
                # Create DH Approval document
                dh_approval = frappe.new_doc('DH Approval')
                dh_approval.employee = employee_id
                dh_approval.dh_date = check_in_date  # Set check-in date
                dh_approval.insert()

def get_holidays():
    # Retrieve list of holidays from the Holiday child table
    holidays = frappe.get_all('Holiday', fields=['holiday_date'])
    return [holiday.holiday_date for holiday in holidays]

def get_employee_check_ins():
    # Retrieve all employee Check-In data
    employee_check_ins = frappe.get_all('Employee Checkin', fields=['employee', 'time'])
    
    # Convert datetime field to datetime object
    check_ins_data = {}
    for entry in employee_check_ins:
        employee_id = entry.employee
        check_in_datetime = entry.time
        check_in_date = check_in_datetime.date()  # Convert datetime to date
        if employee_id not in check_ins_data:
            check_ins_data[employee_id] = []
        check_ins_data[employee_id].append(check_in_date)  # Append date
    return check_ins_data


# @frappe.whitelist()
# def validate_compensatory_leave_duration(work_from_date):
#     # method to restrict applying comp off request after 30 from actual date
#     date_string = work_from_date
#     dt = datetime.strptime(date_string,'%Y-%m-%d').date()
#     today = datetime.today().date()
#     c_off = add_months(today,-1)
#     if c_off < today:
#          frappe.throw(_("Compensatory leave cannot be applied after 1 month from the work from date"))
    


# @frappe.whitelist()
# def update_shift_days(employee, from_date, to_date):
#     # method returns the count of night shift in salary slip when employees from plastic injection department 
#     att = frappe.db.sql("""
#         SELECT name 
#         FROM `tabAttendance` 
#         WHERE employee = %s 
#             AND attendance_date BETWEEN %s AND %s 
#             AND shift_status = 'P/N'
#     """, (employee, from_date, to_date), as_dict=True)

#     count = len(att)
#     return count

@frappe.whitelist()
def attendance_correction():
    checkin = frappe.db.sql("""update `tabLeave Application` set docstatus=0 where name="HR-LAP-2024-00672" """,as_dict = True)


from datetime import datetime, timedelta

@frappe.whitelist()
def ot_without_break():
    # replica of method used for break deduction in mark att code
    from_date = '2024-07-16'
    to_date = '2024-07-31'
    attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'docstatus':('!=','2')},['*'],order_by='employee_name ASC')
    i=0
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
                    ot.shift = att.shift
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
    for att in attendance:
        if att.shift not in ['Lady Guard','SS-N','SQ','SEC']:
            if att.in_time and att.out_time:
                time_ranges = [
                    ('01:00:00', '01:30:00'),
                    ('08:30:00', '09:00:00'),
                    ('13:00:00', '13:30:00'),
                    ('20:30:00', '21:00:00')
                    
                ]
                break_deduction=0
                early_ot=0
                for start_str, end_str in time_ranges:
                    start_time = datetime.strptime(start_str, '%H:%M:%S').time()
                    end_time = datetime.strptime(end_str, '%H:%M:%S').time()
                    start_datetime = datetime.combine(att.in_time.date(), start_time)
                    end_datetime = datetime.combine(att.in_time.date(), end_time)
                    if att.out_time > att.in_time:
                        end_datetime += timedelta(days=1)
                    if start_datetime.time() <= att.out_time.time() <= end_datetime.time():
                        print("hi")
                    else:
                        if (att.in_time <= end_datetime <= att.out_time) or (att.in_time <= start_datetime <= att.out_time):
                            break_deduction +=1

                        elif start_datetime < att.in_time < datetime.combine(att.in_time.date(), end_time): 
                            early_ot = end_datetime - att.in_time
                if early_ot:
                    early_ot_hrs=(early_ot.seconds//60)%60
                else:
                    early_ot_hrs=0
                total_wh=att.out_time-att.in_time
                break_minutes = break_deduction * 30
                regular_hours = timedelta(hours=8)
                hh = check_holiday(att.attendance_date, att.employee)
                if hh and hh!='NPD':
                    overtime = total_wh - (timedelta(minutes=break_minutes) + timedelta(minutes=early_ot_hrs))
                else:
                    overtime = total_wh - (regular_hours + timedelta(minutes=break_minutes) + timedelta(minutes=early_ot_hrs))
                if overtime >= timedelta(hours=1):
                    if (overtime.seconds//60)%60 <=29:
                        ot_hours = timedelta(hours=(overtime.seconds // 3600),minutes=0,seconds=0)
                    else:
                        ot_hours = timedelta(hours=(overtime.seconds // 3600),minutes=30,seconds=0)
                elif overtime < timedelta(hours=1) :
                    if (overtime.seconds//60)%60 <= 29:
                        ot_hours = "00:00:00"
                    else:
                        ot_hours = "00:30:00"   
                if ot_hours !='00:00:00':
                    i+=1
                    print(att.employee_name)
                    print(ot_hours)
                
                    ftr = [3600,60,1]
                    hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
                    ot_hr = round(hr/3600,1)
                    frappe.db.set_value('Attendance',att.name,'total_overtime_hours',ot_hours)
                    frappe.db.set_value('Attendance',att.name,'overtime_hours',ot_hr)
                else:
                    frappe.db.set_value('Attendance',att.name,'total_overtime_hours',"00:00:00")
                    frappe.db.set_value('Attendance',att.name,'overtime_hours',"0.0")
    print(i)
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


                    
# import frappe
# from frappe import _
# @frappe.whitelist()
# def leave_days_count(doc):
#     # method used to return the total no of leaves days in salary slip
#     leave = frappe.db.sql("""
#         SELECT sum(total_leave_days) as leave_days
#         FROM `tabLeave Application`
#         WHERE employee = %s 
#             AND from_date <= %s 
#             AND to_date >= %s
#             AND leave_type NOT IN ('Leave Without Pay', 'ESI Leave')
#             AND status = 'Approved'
#     """, (doc.employee, doc.end_date, doc.start_date), as_dict=True)
    
#     return leave[0].leave_days or 0


# @frappe.whitelist()
# def get_casual_leaves(doc,method):
#     if doc.leave_type == "Casual Leave":
#         # method to restrict the casual leave applications only 3 per month
#         if isinstance(doc.from_date, str):
#             doc.from_date = datetime.strptime(doc.from_date, "%Y-%m-%d").date()
#         if doc.from_date.day < 26:
#             month_start = (doc.from_date - relativedelta(months=1)).replace(day=26)
#             month_end = doc.from_date.replace(day=25)
#         else:
#             month_start = doc.from_date.replace(day=26)
#             month_end = (doc.from_date + relativedelta(months=1)).replace(day=25)
#         # month_start=get_first_day(doc.from_date)
#         # month_end=get_last_day(doc.to_date)
#         cl_applications=frappe.get_all(
#             "Leave Application",
#             filters={
#                 'employee':doc.employee,
#                 'from_date':('between',[month_start,month_end]),
#                 'to_date':('between',[month_start,month_end]),
#                 'leave_type':'Casual Leave',
#                 'name':('!=',doc.name),
#                 'workflow_state':('!=','Cancelled')
#             },
#             fields=['total_leave_days'])
#         total_cl=sum([i['total_leave_days'] for i in cl_applications])
#         total_cl+=doc.total_leave_days
#         if total_cl >3:
#             frappe.throw("3 Casual Leaves only allowed per month.")
        
# @frappe.whitelist()
# def cl_el_restriction(doc,method):
#     # method to restrict the EL and CL application before or after sunday
#     if doc.leave_type=='Earned Leave' or doc.leave_type=='Casual Leave':
#             sdate = getdate(doc.from_date)
#             edate = getdate(doc.to_date)
#             before_check = sdate.weekday()
#             after_check = edate.weekday()
#             if before_check==0:
#                 frappe.errprint('before')
#                 prev_day = frappe.utils.add_days(sdate, -2)
#                 frappe.errprint(prev_day)
#                 if frappe.db.exists('Leave Application', {'employee': doc.employee,'to_date':prev_day,'leave_type': doc.leave_type,'docstatus': ('!=', 2)}):
#                     frappe.throw("Already another Leave Application found on Saturday.")
#             elif after_check==5:
#                 frappe.errprint('After')
#                 next_day = frappe.utils.add_days(edate, 2)
#                 frappe.errprint(next_day)
#                 if frappe.db.exists('Leave Application', {'employee': doc.employee,'from_date':next_day,'leave_type': doc.leave_type,'docstatus': ('!=', 2)}):
#                     frappe.throw("Already another Leave Application found on Monday.")

@frappe.whitelist()
def update_late_entry_time():
    attendance=frappe.get_all("Attendance",{'status':'Absent',"attendance_date":('between',('2024-06-01','2024-06-30'))},['*'])
    i=0
    for att in attendance:
        late_entry_str = att.get('late_entry_hours', '0:00:00')
        early_exit_str = att.get('early_exit_hours', '0:00:00')
        
        late_entry_str = str(late_entry_str)
        early_exit_str = str(early_exit_str)
        try:
            late_entry_formatted = re.sub(r'\.\d+$', '', late_entry_str)
            early_exit_formatted = re.sub(r'\.\d+$', '', early_exit_str)
        except re.error as e:
            late_entry_formatted = late_entry_str
            early_exit_formatted = early_exit_str
        if (late_entry_formatted == early_exit_formatted) and late_entry_formatted!='00:00:00':
            # frappe.db.sql("""update `tabAttendance` set late_entry_hours = '00:00:00' where name = %s""",(att.name))
            # frappe.db.sql("""update `tabAttendance` set early_exit_hours = '00:00:00' where name = %s""",(att.name))
            i += 1

    # Print the count of matching entries
    print(i)

# @frappe.whitelist()
# def el_restriction(doc, method):
#     # Get the start and end of the year for the leave application
#     start_date=getdate(doc.from_date)
#     year_start = date(start_date.year, 1, 1)
#     year_end = date(start_date.year, 12, 31)

#     # Query to check the number of Earned Leave applications for the employee in the current year
#     leave_count = frappe.db.sql("""
#         SELECT COUNT(*) AS count
#         FROM `tabLeave Application`
#         WHERE docstatus != 2
#         AND employee = %s
#         AND leave_type = 'Earned Leave'
#         AND (
#             (from_date BETWEEN %s AND %s) 
#             OR (to_date BETWEEN %s AND %s) 
#             OR (from_date <= %s AND to_date >= %s)
#         )
#     """, (doc.employee, year_start, year_end, year_start, year_end, year_start, year_end), as_dict=True)

#     # Get the leave count
#     leave_count = leave_count[0].get('count', 0)

#     # Restrict if more than 3 Earned Leave applications exist
#     if leave_count > 3:
#         frappe.throw("Only 3 earned leave applications are allowed per year.")

@frappe.whitelist()		
def update_shift_status(doc,method):
        s_status = att_shift_status_with_employee(doc.attendance_date, doc.attendance_date, doc.employee)
        if doc.status == 'On Leave':
            doc.shift_status=s_status
            doc.in_time=''
            doc.out_time=''
            doc.shift=''
            doc.total_working_hours="00:00:00"
            doc.total_extra_hours="00:00:00"
            doc.total_overtime_hours="00:00:00"
            doc.early_exit_hours="00:00:00"
            doc.late_entry_hours="00:00:00"

@frappe.whitelist()
def create_ledger():
    att = frappe.new_doc("Attendance")
    att.employee = 'TSIS/P028'
    att.attendance_date = '2022-11-09'
    att.shift_status = 'EL'
    att.status='On Leave'
    att.leave_application='HR-LAP-2024-00775'
    att.leave_type='Earned Leave'
    att.total_working_hours = "00:00:00"
    att.working_hours = "0.0"
    att.extra_hours = "0.0"
    att.total_extra_hours = "00:00:00"
    att.total_overtime_hours = "00:00:00"
    att.early_exit_hours = "00:00:00"
    att.late_entry_hours = "00:00:00"
    att.overtime_hours = "0.0"
    att.insert()
    att.save(ignore_permissions=True)

# @frappe.whitelist()
# #send a mail alert if any scheduled job failed
# def schedule_log_fail(doc,method):
#     if doc.status=='Failed':
#         message = """
#         The schedule Job type <b>{}</b> is failed. <br>Kindly check the log <b>{}</b>
#         """.format(doc.scheduled_job_type,doc.name)
#         frappe.sendmail(
#                 recipients=["erp@groupteampro.com"],
#                 subject='Scheduled Job type failed (TSI)',
#                 message=message
#             )
        
@frappe.whitelist()
def update_ot():
    att=frappe.db.get_all("Attendance",{'attendance_date':('between',('2025-03-01','2025-03-29')),'docstatus':['!=',2],'overtime_hours':0,'overtime_request':['!=','']},['overtime_request','name'])
    for a in att:
        ot=a.overtime_request

        frappe.db.set_value("Attendance",a.name,'overtime_request','')
        doc=frappe.get_doc("Overtime Request",ot)
        if doc.docstatus==0:
            doc.delete()

# import frappe
# @frappe.whitelist()
# def validate_overtime_reason_before_submit(doc, method):
#     if doc.workflow_state == "L1 Pending" and not doc.reason:
#         frappe.throw("Please enter a Job/Work before sending to Level 1 Approver.")
#     if doc.reason and doc.workflow_state == "L1 Pending":
#         doc.workflow_state = "L1 Pending"

# import frappe        

# @frappe.whitelist()
# def validate_dh_reason_before_submit(doc, method):
#     job_work_value = getattr(doc, "job__work", None)
#     if doc.workflow_state == "L1 Pending" and not job_work_value:
#         frappe.throw("Please enter a Job/Work before sending to Level 1 Approver.")
#     if job_work_value and doc.workflow_state == "L1 Pending":
#         doc.workflow_state = "L1 Pending"
