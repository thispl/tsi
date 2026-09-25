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
def monthly_in_out(start_date,end_date,category):
    # jinja method used in report dashboard to print the monthly in and out report
    data=""
    dates = get_dates(start_date,end_date)
    dates1 = get_date(start_date,end_date)
    if category:
        employees = frappe.get_all("Employee",{'employee_catagory':category,'status':'Active'},['*'])
    else:
        employees = frappe.get_all("Employee",{'status':'Active'},['*'])
    for e in employees:
        data +="""
        <style>
            .print-format {
                padding: 0px;
            }
            @media screen {
                .print-format {
                    padding: 0in;
                }
            }
        </style>
        <div class="container" style="page-break-inside:avoid"><p style="font-size:11px"><b>&nbsp; &nbsp;&nbsp;Employee Code/Name  </b>%s   <b>%s</b></p>"""%(e.name,e.employee_name)
        data +='<div class="row"><div class="col-xs-6"><table width=50% border =1>'
        data += "<tr style='font-size:6px;'><td style='font-size:6px;'><b><center>Day</center></b></td><td style='font-size:6px;'><b><center>Shift</center></b></td><td style='font-size:6px;'><b><center>Status</center></b></td><td style='font-size:6px;'><b><center>Time In</center></b></td><td style='font-size:6px;'><b><center>Time Out</center></b></td><td style='font-size:6px;'><b><center>Total Hours</center></b></td><td style='font-size:6px;'><b><center>Late</center></b></td><td style='font-size:6px;'><b><center>Early</center</b></td><td style='font-size:6px;'><b><center>OT</center</b></td></tr>"
        total_ot = timedelta(0,0,0)
        for date in dates:
            dt = datetime.strptime(date,'%Y-%m-%d')
            d = dt.strftime('%d')
            shift = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'shift') or ''
            status = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'shift_status') or ''
            in_time = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'in_time')
            if in_time is not None:
                    formatted_time = in_time.strftime('%H:%M')
            else:
                formatted_time = ''
            out_time = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'out_time')
            if out_time is not None:
                    formatted_out_time = out_time.strftime('%H:%M')
            else:
                formatted_out_time = ''
            working_hours = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'total_working_hours') or ''
            late = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'late_entry')
            if late==1:
                late_entry=frappe.db.get_value("Late Entry",{"employee":e.name,"permission_date":date},'late')
            else:
                late_entry=' '
            early = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'early_exit')
            if early==1:
                early_exit=frappe.db.get_value("Early Out",{"employee":e.name,"permission_date":date},'out')
            else:
                early_exit=' '
            overtime_hours = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'overtime_hours') or ''

            data += "<tr style='font-size:6px;'><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"%(d,shift,status,formatted_time,formatted_out_time,working_hours or '',late_entry,early_exit,overtime_hours or '')
        data += '</table></div>'
        data += '<div class="col-xs-6"><table  border= 1 width=50%>'
        data += "<tr style='font-size:6px;'><td style='font-size:6px;'><b><center>Day</center></b></td><td style='font-size:6px;'><b><center>Shift</center></b></td><td style='font-size:6px;'><b><center>Status</center></b></td><td style='font-size:6px;'><b><center>Time In</center></b></td><td style='font-size:6px;'><b><center>Time Out</center></b></td><td style='font-size:6px;'><b><center>Total Hours</center></b></td><td style='font-size:6px;'><b><center>Late</center></b></td><td style='font-size:6px;'><b><center>Early</center</b></td><td style='font-size:6px;'><b><center>OT</center</b></td></tr>"

        # data += "<tr style='font-size:9px;2'><td><b><center>Day</center></b></td><td><b><center>Shift</center></b></td><td><b><center>Status</center></b></td><td><b><center>Time In</center></b></td><td><b><center>Time Out</center></b></td><td><b><center>Total Hours</center></b></td><td><b><center>Late</center></b></td><td><b><center>Early</center</b></td><td><b><center>OT</center</b></td></tr>"
        total_ot = timedelta(0,0,0)
        for date in dates1:
            dt = datetime.strptime(date,'%Y-%m-%d')
            d = dt.strftime('%d')
            shift = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'shift') or ''
            status = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'shift_status') or ''
            in_time = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'in_time')
            if in_time is not None:
                    formatted_time = in_time.strftime('%H:%M')
            else:
                formatted_time = ''
            out_time = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'out_time')
            if out_time is not None:
                    formatted_out_time = out_time.strftime('%H:%M')
            else:
                formatted_out_time = ''
            working_hours = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'total_working_hours') or ''
            late = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'late_entry')
            if late==1:
                late_entry=frappe.db.get_value("Late Entry",{"employee":e.name,"permission_date":date},'late')
            else:
          
                late_entry=' '
                early = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'early_exit')
            if early==1:
                early_exit=frappe.db.get_value("Early Out",{"employee":e.name,"permission_date":date},'out')
            else:
                early_exit=' '
            overtime_hours = frappe.db.get_value('Attendance' ,{'employee':e.name,"attendance_date":date,'docstatus':('!=','2')},'overtime_hours') or ''

            data += "<tr style='font-size:6px;'><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"%(d,shift,status,formatted_time,formatted_out_time,working_hours or '',late_entry,early_exit,overtime_hours or '')

        data += '</table></div></div></div>'
    frappe.log_error(title='days',message=data)
    return data


def get_dates(start_date,end_date):
    # method used to get the dates between the start and end date
    no_of_days = date_diff(add_days(end_date, 1), start_date)
    if no_of_days==31:
        dates = [add_days(start_date,i) for i in range(0,16)]
    else:
        dates = [add_days(start_date,i) for i in range(0,15)]
    return dates

def get_date(start_date,end_date):
    no_of_days = date_diff(add_days(end_date, 1), start_date)
    if no_of_days==31:
        dates = [add_days(start_date,i) for i in range(16,no_of_days)]
    else:
        dates = [add_days(start_date,i) for i in range(15,no_of_days)]
    return dates
