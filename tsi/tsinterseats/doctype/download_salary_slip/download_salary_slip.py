# Copyright (c) 2025, Abdulla P I and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DownloadSalarySlip(Document):
	@frappe.whitelist()
	def get_salary_slip(self):
		if self.month:
			month_map = {
				'Jan': 1,
				'Feb': 2,
				'Mar': 3,
				'Apr': 4,
				'May': 5,
				'Jun': 6,
				'Jul': 7,
				'Aug': 8,
				'Sep': 9,
				'Oct': 10,
				'Nov': 11,
				'Dec': 12
			}

			month_number = month_map.get(self.month)
			if not month_number:
				frappe.throw("Invalid month value: {}".format(self.month))

			slips = frappe.db.sql("""
				SELECT name 
				FROM `tabSalary Slip` 
				WHERE MONTH(end_date) = %s 
				AND YEAR(end_date) = %s 
				AND employee = %s 
				AND docstatus = 1
			""", (month_number, self.year, self.employee_id), as_dict=True)

			return slips
