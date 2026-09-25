from __future__ import unicode_literals
import frappe
from calendar import monthrange
from frappe import _, msgprint
from frappe.utils import flt
from frappe.utils import cstr, add_days, date_diff, getdate, format_date
from frappe import _, bold
from frappe.utils.csvutils import UnicodeWriter, read_csv_content
from frappe.utils.data import format_date
from frappe.utils.file_manager import get_file
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue

from datetime import date, timedelta, datetime
import openpyxl
from openpyxl import Workbook
import re
from frappe import _
import frappe
from frappe.model.document import Document
from datetime import date, timedelta, datetime,time
from frappe.utils import (getdate, cint, add_months, date_diff, add_days,
	nowdate, get_datetime_str, cstr, get_datetime, now_datetime, format_datetime,today, format_date)
import math
from frappe.utils import add_months, cint, flt, getdate, time_diff_in_hours,time_diff_in_seconds
import locale


import openpyxl
import xlrd
import re
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import GradientFill, PatternFill
from six import BytesIO, string_types
import openpyxl.styles as styles

@frappe.whitelist()
def download():
	filename = 'PF Report'
	test = build_xlsx_response(filename)
	
def make_xlsx(data, sheet_name=None, wb=None, column_widths=None):
	args = frappe.local.form_dict
	column_widths = column_widths or []
	if wb is None:
		wb = openpyxl.Workbook()
		 
	ws = wb.create_sheet(sheet_name, 0)
	ws.column_dimensions['B'].width = 13 
	ws.column_dimensions['C'].width = 20 
	ws.column_dimensions['D'].width = 20
	ws.column_dimensions['E'].width = 25
	ws.column_dimensions['F'].width = 10
	ws.column_dimensions['G'].width = 13
	ws.column_dimensions['I'].width = 17
	ws.column_dimensions['L'].width = 20
	ws.column_dimensions['M'].width = 15

	thin_border = Border(
	left=Side(style='thin'),
	right=Side(style='thin'),
	top=Side(style='thin'),
	bottom=Side(style='thin')
	)
	start_date = args.start_date
	month_year = datetime.strptime(start_date, "%Y-%m-%d").strftime("%B-%Y").upper()

	ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=13)
	ws.cell(row=1, column=1).value = f"PF CONTRIBUTION FOR THE MONTH OF {month_year}"
	ws.cell(row=1, column=1).font = Font(bold=True)
	ws.cell(row=1, column=1).alignment = Alignment(horizontal='center', vertical='center')

	ws.cell(row=2, column=1).value = "EMPLOYER PF NO: PY/KRP/0053319/000"
	ws.cell(row=2, column=1).font = Font(bold=True)
	ws.cell(row=2, column=1).alignment = Alignment(horizontal='left', vertical='center')

	headers = [
		"S.No", "Employee ID", "Employee Name", "Department",
		"Bank Account Number", "EPF Wages", "EMPE'S PF", "VPF",
		"EMPLR'S PF(Incl. FPF)", "Family PF", "EPF",
		"A/c. 10(Basic Salary)", "EMPE'S PF + VPF"
	]

	ws.append(headers)

	# ws.append(["S.No","Employee ID","Employee Name","Department","Bank Account Number","EPF Wages","EMPE'S PF", "VPF", "EMPLR'S PF(Incl. FPF)","Family PF","EPF","A/c. 10(Basic Salary)","EMPE'S PF +VPF"])
	align_center = Alignment(horizontal='center',vertical='center')
	for header in ws.iter_rows(min_row=1, max_row=3, min_col=1, max_col=13):
		for cell in header:
			cell.font = Font(bold=True)
			cell.alignment = align_center
			cell.border = thin_border
	
	

	data1= get_data(args)
	for row in data1:
		ws.append(row)
	total_pf_wages = 0
	total_emp_pf = 0
	total_vpf = 0
	total_employer_pf = 0
	total_family_pf = 0
	total_epf = 0
	total_basic_salary = 0
	total_emp_pf_vpf = 0

	for r in data1:
		total_pf_wages += flt(r[5])
		total_emp_pf += flt(r[6])
		total_vpf += flt(r[7])
		total_employer_pf += flt(r[8])
		total_family_pf += flt(r[9])
		total_epf += flt(r[10])
		total_basic_salary += flt(r[11])
		total_emp_pf_vpf += flt(r[12])

	ws.append([
		"", "", "", "", "GRAND TOTAL",
		total_pf_wages,
		total_emp_pf,
		total_vpf,
		total_employer_pf,
		total_family_pf,
		total_epf,
		total_basic_salary,
		total_emp_pf_vpf
	])

	# Style total row
	total_row = ws.max_row
	for row in ws.iter_rows(min_row=total_row, max_row=total_row, min_col=1, max_col=13):
		for cell in row:
			cell.font = Font(bold=True)
			cell.border = thin_border
			cell.alignment = Alignment(vertical='center')


	max_row = ws.max_row
	max_col = ws.max_column

	for row in ws.iter_rows(min_row=2, max_row=max_row, min_col=1, max_col=max_col):
		for cell in row:
			cell.border = thin_border
			cell.alignment = Alignment(vertical='center')
	xlsx_file = BytesIO()
	wb.save(xlsx_file)
	return xlsx_file

def build_xlsx_response(filename):
	xlsx_file = make_xlsx(filename)
	frappe.response['filename'] = filename + '.xlsx'
	frappe.response['filecontent'] = xlsx_file.getvalue()
	frappe.response['type'] = 'binary'

def get_data(args):
	data = []
	row = []
	salary_slips = frappe.db.sql("""select * from `tabSalary Slip` where start_date between '%s' and '%s' and docstatus!=2"""%(args.start_date, args.end_date), as_dict=True)
	i = 1
	for ss in salary_slips:
		emp_id = ss.employee
		emp_name = ss.employee_name
		dep= ss.department
		ac = ss.bank_account_no
		sal = ss.gross_pay
		basic_salary = min(ss.gross_pay, 15000)
		pf = frappe.get_value('Salary Detail',{'salary_component':"PF",'parent':ss.name},"amount") or 0
		vpf = frappe.get_value('Salary Detail',{'salary_component':"VPF",'parent':ss.name},"amount") or 0
		emplyr_pf = round((basic_salary * 0.12) + vpf, 0)
		family_pf = round((basic_salary * 0.0833), 0)
		epf = emplyr_pf- family_pf
		emple_pf = pf+vpf
		row = [i,emp_id or "-",emp_name or "-",dep or "-",ac or "-",sal or 0,
		 pf or 0, vpf or 0,emplyr_pf,family_pf,epf,basic_salary or 0,emple_pf]
		data.append(row)
		i+=1
	return data