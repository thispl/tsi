# Copyright (c) 2024, Abdulla P I and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class VehicleRequest(Document):
	pass

# def after_insert(self):
# 	frappe.db.set_value('On Duty Application','name',{'vehicle_request': 1})
	