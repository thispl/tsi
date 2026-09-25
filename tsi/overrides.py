from email import message
import frappe
from frappe import _
import datetime, math
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
from hrms.hr.doctype.leave_application.leave_application import LeaveApplication
from hrms.hr.doctype.attendance.attendance import Attendance
from hrms.hr.utils import get_holidays_for_employee
from tsi.mark_attendance import att_shift_status_with_employee
from datetime import datetime, timedelta
from frappe.utils import cstr, add_days, date_diff,format_datetime,ceil,flt
from frappe.utils import (getdate, cint, add_months, date_diff, add_days,nowdate, get_datetime_str, cstr, get_datetime, now_datetime, format_datetime, format_date,get_time)
from frappe.utils.data import today, add_days, add_years
from dateutil.relativedelta import relativedelta

class CustomSalarySlip(SalarySlip):
    def get_date_details(self):
        # sum of working hours is set as dh hours, when the employee works on NPD
        dh_hrs = frappe.db.sql("""
            SELECT * FROM `tabAttendance`
            WHERE attendance_date BETWEEN %s AND %s 
            AND shift_status LIKE %s
            AND employee = %s AND docstatus != 2
        """, (self.start_date, self.end_date, '%NPD%', self.employee), as_dict=True)
        custom_dh_hours = 0
        for hr in dh_hrs:
            if hr.working_hours>=8:
                custom_dh_hours +=8
            elif hr.working_hours<8:
                custom_dh_hours += hr.working_hours
        
        integer_part = int(custom_dh_hours)
        decimal_part = custom_dh_hours - integer_part
        if 0.1 <= decimal_part <= 0.49:
            custom_dh_hours = integer_part
        elif 0.5 <= decimal_part <= 0.99:
            custom_dh_hours = integer_part + 0.5
        else:
            custom_dh_hours = integer_part
        self.dh_overtime_hours = custom_dh_hours
        npd_amount=frappe.db.get_all("DH Approval",{'payroll_date_npd':('between',(self.start_date,self.end_date)),'employee':self.employee,'docstatus':1,'shift':('not in',['Gardner','HK','Lady Guard','SS-N','SEQ','SO'])},['*'])
        npd_allow=0
        for n in npd_amount:
            npd_allow+=n.dh_allowance
        self.dh_amount=npd_allow
        # holidays = get_holidays_for_employee(self.employee, self.start_date, self.end_date)
        # working_days = date_diff(self.end_date, self.start_date) + 1
        # working_days_list = [
        #     add_days(getdate(self.start_date), days=day) for day in range(0, working_days)
        # ]
        # working_days_list = [i for i in working_days_list if i not in holidays]
        # working_days -= len(holidays)
        relieving_date = frappe.db.get_value("Employee", self.employee, ["relieving_date"])
        date_of_joining = frappe.db.get_value("Employee", self.employee, ["date_of_joining"])
        if date_of_joining < getdate(self.start_date):
            start_date=getdate(self.start_date)
        else:
            start_date=date_of_joining
        if relieving_date:
            no_of_days = date_diff(add_days(relieving_date, 1), start_date)
        else:
            no_of_days = date_diff(add_days(self.end_date, 1), start_date)
        dates = [add_days(start_date, i) for i in range(0, no_of_days)]
        att_count=0
        holidays=0
        # att bonus is set when employee is present for all days
        for date in dates:
            holiday_list = frappe.db.get_value('Employee',{'name':self.employee},'holiday_list')
            holiday = frappe.db.sql("""select `tabHoliday`.holiday_date,`tabHoliday`.weekly_off, `tabHoliday`.others from `tabHoliday List` 
            left join `tabHoliday` on `tabHoliday`.parent = `tabHoliday List`.name where `tabHoliday List`.name = '%s' and holiday_date = '%s' """%(holiday_list,date),as_dict=True)
            doj= frappe.db.get_value("Employee",{'name':self.employee},"date_of_joining")
            status = ''
            if not holiday :
                if frappe.db.exists("Attendance",{'attendance_date':date,'employee':self.employee,'docstatus':('!=','2'),'status':'Present'}):
                    att_count+=1
                if frappe.db.exists("Attendance",{'attendance_date':date,'employee':self.employee,'docstatus':('!=','2'),'status':'Half Day'}):
                    att_count+=0.5
            else:
                holidays+=1
        self.att_bonus=att_count + holidays
        self.holidays=holidays
        nsa=0
        # count of night shift
        attendance=frappe.db.sql("select * from `tabAttendance` where employee=%s and attendance_date between %s and %s and shift in ('N','SS-N','III')",(self.employee,self.start_date,self.end_date),as_dict=True)
        for att in attendance:
            if att.status=='Present':
                nsa+=1
            elif att.status=='Half Day':
                nsa+=0.5
        self.number_of_night_shift_attended=nsa
        # ot hours is updated from the overtime request
        ot_hrs = frappe.db.sql("""
            SELECT SUM(ot_hours) AS ot_total 
            FROM `tabOvertime Request`
            WHERE payroll_date BETWEEN %s AND %s 
            AND employee = %s 
            AND docstatus = 1
            AND workflow_state = 'Approved'
        """, (self.start_date, self.end_date, self.employee), as_dict=True)
        if ot_hrs and len(ot_hrs) > 0:
            self.overtime_hours = ot_hrs[0].ot_total or 0
        else:
            self.overtime_hours = 0

# class CustomAttendance(Attendance):
#     def validate(self):
#         # method to update the shift status
#         s_status = att_shift_status_with_employee(self.attendance_date, self.attendance_date, self.employee)
#         frappe.errprint(s_status)
#         self.shift_status = s_status
#         if self.status == 'On Leave':
#             frappe.errprint('s_status')
#             self.shift_status = s_status
#             self.in_time = ''
#             self.out_time = ''
#             self.shift = ''
#             self.total_working_hours = "00:00:00"
#             self.total_extra_hours = "00:00:00"
#             self.overtime_hours = "00:00:00"
#             self.early_exit_hours = "00:00:00"
#             self.late_entry_hours = "00:00:00"
#         if self.leave_application and self.status == 'Half Day':
#             frappe.errprint("hd1")
#             frappe.errprint(s_status)
#             self.shift_status = s_status
#             frappe.errprint(self.shift_status)
            
#     def after_insert(self):
#         # method to in time and out time empty when leave application is there
#         status_map = {
#             "Present": "P",
#             "Absent": "A",
#             "Half Day": "HD",
#             "On Leave":"On Leave",
#             "Work From Home": "WFH",
#             "Holiday": "HH",
#             "Weekly Off": "WW",
#             "Leave Without Pay": "LOP",
#             "Casual Leave": "CL",
#             "Earned Leave": "EL",
#             "Sick Leave": "SL",
#             "ESI Leave": "ESI",
#             "Compensatory Off": "C-OFF",
#         }
#         s_status = att_shift_status_with_employee(self.attendance_date, self.attendance_date, self.employee)
#         if self.status == 'On Leave':
#             self.shift_status=s_status
#             self.in_time=''
#             self.out_time=''
#             self.shift=''
#             self.total_working_hours="00:00:00"
#             self.total_extra_hours="00:00:00"
#             self.total_overtime_hours="00:00:00"
#             self.early_exit_hours="00:00:00"
#             self.late_entry_hours="00:00:00"
#         if self.leave_application and self.status == 'Half Day':
#             if not self.in_time and not self.out_time:
#                 self.shift_status=s_status
#                 self.in_time=''
#                 self.out_time=''
#                 self.shift=''
#                 self.total_working_hours="00:00:00"
#                 self.total_extra_hours="00:00:00"
#                 self.total_overtime_hours="00:00:00"
#                 self.early_exit_hours="00:00:00"
#                 self.late_entry_hours="00:00:00"

           

# class CustomLeaveApplication(LeaveApplication):
#     def validate(self):
#         if self.leave_type=='Earned Leave' or self.leave_type=='Casual Leave':
#             frappe.errprint("PAss")
#             sdate = getdate(self.from_date)
#             edate = getdate(self.to_date)
#             before_check = sdate.weekday()
#             after_check = edate.weekday()
#             if before_check==0:
#                 frappe.errprint("PAss1")
#                 prev_day = frappe.utils.add_days(sdate, -2)
#                 if frappe.db.exists('Leave Application', {'employee': self.employee,'to_date':prev_day,'leave_type': self.leave_type,'docstatus': ('!=', 2)}):
#                     frappe.throw("Already another Leave Application found on Saturday.")
#             elif after_check==5:
#                 frappe.errprint("PAss2")
#                 next_day = frappe.utils.add_days(edate, 2)
#                 if frappe.db.exists('Leave Application', {'employee': self.employee,'from_date':next_day,'leave_type': self.leave_type,'docstatus': ('!=', 2)}):
#                     frappe.throw("Already another Leave Application found on Monday.")
#         # if self.leave_balance < self.total_leave_days:
#         #     frappe.throw("Insufficient Leave Balance for this leave type")
            