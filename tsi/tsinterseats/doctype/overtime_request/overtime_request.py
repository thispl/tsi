# Copyright (c) 2023, Abdulla P I and contributors
# For license information, please see license.txt

import fractions
from frappe.model.document import Document
import frappe
import datetime
from datetime import datetime, timedelta

from datetime import date, datetime,time
from frappe.utils import add_days,today
import datetime as dt
# import pandas as pd
from frappe.utils import (
    add_days,
    add_to_date,
    cint,
    flt,
    get_datetime,
    get_link_to_form,
    get_time,
    getdate,
    time_diff,
    time_diff_in_hours,
    time_diff_in_seconds,
)

class OvertimeRequest(Document):
    def validate(self):
        if self.on_duty_application:
            doc=frappe.db.get_value("On Duty Application",{'name':self.on_duty_application},['docstatus'])
            if doc!=1:
                frappe.throw(f"On Duty Application is not found for the employee {self.employee}.")
        if frappe.db.exists("Overtime Request",{'docstatus':['!=',2],'employee':self.employee,'ot_date':self.ot_date,'name':['!=',self.name]}):
            frappe.throw(f"Already another request found for {self.employee} on {self.ot_date} ")
        
    # def leave_application_rejection_remark(doc, method):
    #     # Only apply check if current state is Draft and attempting to Reject
    #     if doc.docstatus == 0 and doc.workflow_state == "L1 Pending":
    #         if not doc.reason:
    #             # Stay in Draft state if no remark is given
    #             frappe.db.set_value("Overtime Request", doc.name, {
    #                 "workflow_state": "Draft",
    #                 "docstatus": 0
    #             })
    #             frappe.throw("Rejection Remark is mandatory to reject from Draft state.")


@frappe.whitelist()
def on_duty_application(employee,od_date):
    data =[]
    if frappe.db.exists('On Duty Application', {'employee': employee, 'od_date': od_date, 'docstatus':1}):
        on_duty = frappe.get_doc('On Duty Application',{'employee':employee,'od_date':od_date,'docstatus':1})
        if on_duty:
            if on_duty.session == 'Flexible':
                if on_duty.flexible_time and on_duty.flexible_to_time:
                    ot_hour = 0
                else:
                    ot_hour = 0
                data =[on_duty.name,on_duty.flexible_time,on_duty.flexible_to_time,round(ot_hour,1)]
            else:
                if on_duty.from_time and on_duty.to_time:
                    ot_hour = 0
                else:
                    ot_hour = 0
                data =[on_duty.name,on_duty.from_time,on_duty.to_time,round(ot_hour,1)]
    else:
        frappe.msgprint(f"On Duty Application is not found for the employee {employee}.")
    return data
    



