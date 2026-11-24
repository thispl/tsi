# Copyright (c) 2023, Abdulla P I and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import datetime
from datetime import timedelta

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	columns = [_('Date') + ":Date:140", _('Employee') + ":Link/Employee:140", _('Employee Name') + ":Data:140"]
	items = frappe.db.sql("""SELECT name FROM `tabFood Menu` ORDER BY serial_no ASC""", as_dict=True)
	for item in items:
		columns.append(_(item.name) + ":Int:80")
	columns.append(_('Total') + ":Int:80")  
	return columns

def get_data(filters):
	data = []
	employee = filters.get('employee')
	params = {"from_date": filters.get('from_date'), "to_date": filters.get('to_date')}

	query = """
		SELECT
			`tabCanteen Coupons`.date,
			`tabCanteen Coupons`.employee,
			`tabCanteen Coupons`.employee_name,
			`tabFood Items`.item,
			SUM(`tabFood Items`.status) AS count
		FROM
			`tabCanteen Coupons`
		LEFT JOIN
			`tabFood Items` ON `tabCanteen Coupons`.name = `tabFood Items`.parent
		WHERE
			`tabCanteen Coupons`.date BETWEEN %(from_date)s AND %(to_date)s
	"""

	if employee:
		query += " AND `tabCanteen Coupons`.employee = %(employee)s"
		params["employee"] = employee

	query += """
		GROUP BY
			`tabCanteen Coupons`.date,
			`tabCanteen Coupons`.employee,
			`tabCanteen Coupons`.employee_name,
			`tabFood Items`.item
		ORDER BY
			`tabCanteen Coupons`.date ASC
	"""

	c = frappe.db.sql(query, params, as_dict=True)
	items = frappe.db.sql("""SELECT name FROM `tabFood Menu` ORDER BY serial_no ASC""", as_dict=True)

	employee_data = {}
	for row in c:
		key = (row['date'], row['employee'])
		item = row['item']
		count = row['count'] or 0

		if key not in employee_data:
			employee_data[key] = {
				'employee_name': row['employee_name'],
				'items': {item: count},
				'total': 0
			}
		else:
			if item not in employee_data[key]['items']:
				employee_data[key]['items'][item] = count
			else:
				employee_data[key]['items'][item] += count

		employee_data[key]['total'] += count

	for (date, employee_id), emp_data in employee_data.items():
		row = [date, employee_id, emp_data['employee_name']]
		for item in items:
			row.append(emp_data['items'].get(item.name, 0))
		row.append(emp_data['total'])
		data.append(row)

	return data