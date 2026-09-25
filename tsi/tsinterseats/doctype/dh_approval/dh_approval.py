# Copyright (c) 2023, Abdulla P I and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class DHApproval(Document):
    def validate(self):
        if frappe.db.exists("DH Approval",{'dh_date':self.dh_date,'employee':self.employee,'docstatus':['!=',2],'name':['!=',self.name]}):
           frappe.throw(_("Already another document found on this date"))

           
