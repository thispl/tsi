import frappe
from frappe.model.document import Document
from frappe.utils import time_diff
from datetime import datetime
from datetime import timedelta
import pdfkit
from frappe.utils import getdate
from datetime import date
from frappe.utils.data import get_datetime
from tsi.mark_attendance import att_shift_status_with_employee
from frappe import throw,_
from frappe.utils import (
    add_days,
    add_months,
    cint,
    date_diff,
    flt,
    get_first_day,
    get_last_day,
    get_link_to_form,
    getdate,
    rounded,
    today,
)

@frappe.whitelist()
def salary_details(doc):
    # method to get the salary details from the applicant for print format (called in jinja)
    data = '<table class="table table-bordered" style="width:80%;margin-left:16mm;">' 
    ware = frappe.get_doc("Job Applicant", doc.name)
    border_color = "black" 
    data += '<tr>'
    data += '<td style="text-align:center; border: 1px solid {0};"><b>S.NO</b></td>'.format(border_color)  
    data += '<td style="text-align:center; border: 1px solid {0};"><b>PARTICULARS</b></td>'.format(border_color)  
    data += '<td style="text-align:center; border: 1px solid {0};"><b>AMOUNT (PER MONTHS) RS.</b></td>'.format(border_color)  
    data += '<tr>'
    a = 1

    for item in ware.salary_details:
        data += '<tr>'
        data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, a)  
        data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, item.particulars or '')  
        data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, item.amount_per_month_rs or 0)  
        data += '</tr>'
        a += 1

    data += '<tr>'
    data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, a)  
    data += '<td style="text-align:center; border: 1px solid {0};"><b>Total A</b></td>'.format(border_color)  
    data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, doc.total or 0)  
    data += '</tr>'
    a += 1

    for item in ware.yearly_salary_details:
        data += '<tr>'
        data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, a)  
        data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, item.particulars or '')  
        data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, item.amount_per_month_rs or 0)  
        data += '</tr>'
        a += 1

    data += '<tr>'
    data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, a)  
    data += '<td style="text-align:center; border: 1px solid {0};"><b>Total B</b></td>'.format(border_color)  
    data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, doc.total_b or 0)  
    data += '</tr>'
    a += 1

    data += '<tr>'
    data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, a)  
    data += '<td style="text-align:center; border: 1px solid {0};"><b>Total A-B</b></td>'.format(border_color)  
    data += '<td style="text-align:center; border: 1px solid {0};">{1}</td>'.format(border_color, doc.total_a_b or 0)  
    data += '</tr>'
    data += '</table>'
    return data

