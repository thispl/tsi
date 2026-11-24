# Copyright (c) 2023, Abdulla P I and contributors
# For license information, please see license.txt
import frappe
from frappe import _
import datetime
from datetime import date, datetime, timedelta


def execute(filters=None):
    columns, data = [] ,[]
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    column = [_('Date') + ":Date:140",]

    items = frappe.db.sql(""" select name,serial_no from `tabFood Menu` order by serial_no asc""",as_dict =1)
    
    for i in items:
        column.extend([_(i.name) + ":Data:140",])

    return column

def get_data(filters):
    data = []
    frm = datetime.strptime(filters.from_date, '%Y-%m-%d').date()
    to = datetime.strptime(filters.to_date, '%Y-%m-%d').date()
    delta = to - frm

    items = frappe.db.sql(""" select name,serial_no from `tabFood Menu` order by serial_no asc""",as_dict =1)

    queries = []
    if filters.checkbox == 1:
        queries.append(""" select `tabVisitor Pass`.posting_date as date,
                sum(`tabFood Items`.status) as count, `tabFood Items`.item
            from `tabVisitor Pass`
            left join `tabFood Items` on `tabVisitor Pass`.name = `tabFood Items`.parent
            where `tabVisitor Pass`.posting_date between %s and %s
            group by `tabVisitor Pass`.posting_date, `tabFood Items`.item """)
    else:
        queries.append(""" select `tabCanteen Coupons`.date as date,
                sum(`tabFood Items`.status) as count, `tabFood Items`.item
            from `tabCanteen Coupons`
            left join `tabFood Items` on `tabCanteen Coupons`.name = `tabFood Items`.parent
            where `tabCanteen Coupons`.date between %s and %s
            group by `tabCanteen Coupons`.date, `tabFood Items`.item """)
        queries.append(""" select `tabVisitor Pass`.posting_date as date,
                sum(`tabFood Items`.status) as count, `tabFood Items`.item
            from `tabVisitor Pass`
            left join `tabFood Items` on `tabVisitor Pass`.name = `tabFood Items`.parent
            where `tabVisitor Pass`.posting_date between %s and %s
            group by `tabVisitor Pass`.posting_date, `tabFood Items`.item """)

    day_counts = {}
    for q in queries:
        for row in frappe.db.sql(q, (frm, to), as_dict=True):
            if row.item is not None:
                day_counts.setdefault(row.date, {}).setdefault(row.item, 0)
                day_counts[row.date][row.item] += row.count or 0

    for i in range(delta.days + 1):
        day = frm + timedelta(days=i)
        counts = day_counts.get(day, {})
        row = [day]
        status = []
        for s in items:
            status.append(counts.get(s.name, 0))
        row.extend(status)
        data.append(row)

    return data

def get_dates_between(start_date, end_date):
  
  dates = []
  current_date = start_date
  while current_date <= end_date:
   dates.append(current_date)
  current_date += datetime.timedelta(days=1)

  return dates