import frappe
from frappe import _

def execute(filters=None):
    columns, data = [], []
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    columns = [
        _('Date') + ":Date:140",
        _('Visitor Name') + ":Link/Employee:140",
        _('Requester Name') + ":Data:140",
        _('Company Name') + ":Data:140",
        _('Purpose Of Visit') + ":Data:140",
    ]
    
    items = frappe.db.sql("""SELECT name FROM `tabFood Menu` ORDER BY serial_no ASC""", as_dict=True)
    for item in items:
        columns.append(_(item.name) + ":Int:80")
    
    columns.append(_('Total') + ":Int:80")
    return columns

def get_data(filters):
    data = []
    name1 = filters.get('name1')
    params = {"from_date": filters.get('from_date'), "to_date": filters.get('to_date')}

    query = """
        SELECT
            `tabVisitor Pass`.visiting_date,
            `tabVisitor Pass`.name1,
            `tabVisitor Pass`.employee,
            `tabVisitor Pass`.company_name AS company,
            `tabVisitor Pass`.purpose_of_visit,
            `tabFood Items`.item,
            SUM(`tabFood Items`.status) AS count
        FROM
            `tabVisitor Pass`
        LEFT JOIN
            `tabFood Items` ON `tabVisitor Pass`.name = `tabFood Items`.parent
        WHERE
            `tabVisitor Pass`.visiting_date BETWEEN %(from_date)s AND %(to_date)s
    """

    if name1:
        query += " AND `tabVisitor Pass`.name1 = %(name1)s"
        params["name1"] = name1

    query += """
        GROUP BY
            `tabVisitor Pass`.visiting_date,
            `tabVisitor Pass`.name1,
            `tabVisitor Pass`.employee,
            `tabVisitor Pass`.company_name,
            `tabVisitor Pass`.purpose_of_visit,
            `tabFood Items`.item
        ORDER BY
            `tabVisitor Pass`.visiting_date ASC
    """

    c = frappe.db.sql(query, params, as_dict=True)
    items = frappe.db.sql("""SELECT name FROM `tabFood Menu` ORDER BY serial_no ASC""", as_dict=True)

    visitor_data = {}
    for row in c:
        key = (row['visiting_date'], row['name1'])
        item = row['item'] or 0
        count = row['count'] or 0
        if key not in visitor_data:
            visitor_data[key] = {
                'employee': row['employee'],
                'company': row['company'],
                'purpose_of_visit': row['purpose_of_visit'],
                'items': {item: count},
                'total': 0
            }
        else:
            if item not in visitor_data[key]['items']:
                visitor_data[key]['items'][item] = count or 0
            else:
                visitor_data[key]['items'][item] += count or 0
        visitor_data[key]['total'] += count

    for (visiting_date, name1), vdata in visitor_data.items():
        row = [visiting_date, name1, vdata['employee'], vdata['company'], vdata['purpose_of_visit']]
        for item in items:
            row.append(vdata['items'].get(item.name, 0))
        row.append(vdata['total'])
        data.append(row)

    return data