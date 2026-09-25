# Copyright (c) 2023, Abdulla P I and contributors
# For license information, please see license.txt

import frappe
from frappe import _, msgprint
from datetime import datetime
from urllib.request import ftpwrapper
from frappe.model.document import Document
from frappe.utils import get_first_day, get_last_day, format_datetime,get_url_to_form,today
from frappe.utils import time_diff
from dateutil.relativedelta import relativedelta
class EarlyOut(Document):
    def validate(self):
        # error will be thrown when permission hours exceeds 60 minutes
        # if self.out > 60:
        #     frappe.throw("Permission Time exceeded 60 minutes")
        total = 0
        count=0
        if isinstance(self.permission_date, str):
            self.permission_date = datetime.strptime(self.permission_date, "%Y-%m-%d").date()
        if self.permission_date.day < 26:
            month_start = (self.permission_date - relativedelta(months=1)).replace(day=26)
            month_end = self.permission_date.replace(day=25)
        else:
            month_start = self.permission_date.replace(day=26)
            month_end = (self.permission_date + relativedelta(months=1)).replace(day=25)
        late_permission = frappe.db.get_all('Late Entry',{'employee':self.employee,'docstatus':['!=',2],"permission_date": ('between',(month_start,month_end))},['*'])
        for late in late_permission:
            count+=1
            total+=late.late
        early_permission = frappe.db.get_all('Early Out',{'employee':self.employee,'docstatus':['!=',2],"permission_date": ('between',(month_start,month_end))},['*'])
        for early in early_permission:
            count+=1
            total+=early.out
        # check early out and other late entry applications, error will be thrown when the sum of permission time is greater than 60  
        if total > 60:
            frappe.throw("Permission Time exceeded 60 minutes")
        # maximum of 2 applications is allowed for late and early applications (each 1)
        if count > 2:
            frappe.throw("Only two documents allowed in a month")
    def on_submit(self):
        if self.out:
            frappe.db.set_value("Attendance",{"name":self.attendance},'early_exit',1)
            frappe.db.set_value("Attendance",{"name":self.attendance},'early_exit_application',self.name)
    def on_cancel(self):
        if self.out:
            frappe.db.set_value("Attendance",{"name":self.attendance},'early_exit',0)
            frappe.db.set_value("Attendance",{"name":self.attendance},'early_exit_application','')
@frappe.whitelist()
def late_time_difference(corrected_out_time,out_time_value):
    value = time_diff(corrected_out_time,out_time_value)
    val = value.total_seconds() / 60
    return val


@frappe.whitelist()
def calculate_overall_late_time(employee,late):
    # method calculate the actual and early out time based on the shift
    data = []
    total = 0
    avaliable_time=0
    month_start = get_first_day(today())
    month_end = get_last_day(today())
    late_permission = frappe.db.get_all('Late Entry',{'employee':employee,"permission_date": ('between',(month_start,month_end))},['*'])
    for late in late_permission:
        total_per_time = frappe.db.get_value('Late Entry',late.name,['late'])
        data.append(int(total_per_time))
    early_permission = frappe.db.get_all('Early Out',{'employee':employee,"permission_date": ('between',(month_start,month_end))},['*'])
    for early in early_permission:
        total_time = frappe.db.get_value('Early Out',early.name,['out'])
        data.append(int(total_time))
        
    total = sum(map(int, [i for i in data if i]))
    total_hours = total
    avaliable_time=60-total
    return total_hours,avaliable_time

@frappe.whitelist()
def date_validation(date):
    dayss = today() <date
    return dayss

@frappe.whitelist()
def out_time(attendance_name):
    value=frappe.db.get_value("Attendance",{"name":attendance_name},['out_time'])
    return value

# @frappe.whitelist()
# def early(doc, method):
#         # if doc.out:
        
#         frappe.db.set_value("Attendance",{"name":doc.name},'early_exit',1)
#         frappe.db.set_value("Attendance",{"name":doc.name},'early_exit_application',doc.name)
# @frappe.whitelist()
# def early(doc, method):
#     early_list = frappe.get_all(
#         "Early Out",
#         filters={
#             "employee": doc.employee,
#             "permission_date": doc.attendance_date
#         },
#         fields=["name"]
#     )
#     doc.early_exit = 1
#     if early_list:
#         doc.early_exit_application = early_list[0]["name"]
#     else:
#         doc.early_exit_application = None  

@frappe.whitelist()
def early(doc, method):
    # Step 1: Get Early Out doc for this employee and date, where out_time is not null
    early_list = frappe.get_all(
        "Early Out",
        filters={
            "employee": doc.employee,
            "permission_date": doc.attendance_date,
        },
        fields=["name", "out_time"]
    )

    # Loop through and find entry where out_time is present
    for early_out in early_list:
        if early_out.get("out_time"):
            doc.early_exit = 1
            doc.early_exit_hours = early_out["out_time"]
            doc.early_exit_application = early_list[0]["name"]
            break  # Use first matching one


