# Copyright (c) 2023, Abdulla P I and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_first_day, today, get_last_day, format_datetime, add_years, date_diff, add_days, getdate, cint, format_date,get_url_to_form

class ResignationForm(Document):
    def on_submit(self):
        if self.workflow_state == 'Approved':
            # frappe.db.set_value('Employee', self.employee,'relieving_date', self.relieving_date)
            if not frappe.db.exists('No Due Form', {'employee': self.name}):
                form = frappe.new_doc('No Due Form')
                form.employee = self.employee
                form.employee_name = self.employee_name
                form.designation = frappe.db.get_value('Employee',{'employee':self.employee},['designation'])
                form.department = frappe.db.get_value('Employee',{'employee':self.employee},['department']) 
                form.save(ignore_permissions=True)
                frappe.db.commit()
            else:
                message = ('Already Employee %s has NO Due Form'%(self.employee)) 
                frappe.log_error('NO Due Form',message)   

            frappe.db.set_value('Employee', self.name,'relieving_date', self.relieving_date)
            frappe.db.set_value('Employee', self.name, 'no_due_alert', 1)
            # frappe.db.set_value('Employee', self.name, 'relieving_date',self.hod_relieving_date )
            frappe.db.set_value('Employee', self.name, 'resignation_letter_date',self.posting_date)
            frappe.db.set_value('Employee', self.name, 'reason_for_leaving',self.reason)
            
    def on_cancel(self):
        emp = frappe.get_doc("Employee",self.employee)
        emp.resignation_letter_date = ''
        emp.relieving_date = ''
        emp.reason_for_leaving = ''
        emp.save(ignore_permissions = True)


    def amend_to_submit(self):
        pass

@frappe.whitelist()
def get_user_details(user_id):
    employee = frappe.db.get_value('Employee',{'status':'Active','name':user_id},['user_id'])
    return employee
