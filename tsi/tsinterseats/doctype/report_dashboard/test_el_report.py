
# import frappe
# import openpyxl
# import io
# from openpyxl.styles import PatternFill, Border, Side, Alignment, Font
# from openpyxl.utils import get_column_letter
# from datetime import datetime
# from dateutil.relativedelta import relativedelta

# @frappe.whitelist()
# def download(from_date=None, to_date=None):
#     wb = openpyxl.Workbook()
#     ws = wb.active
#     ws.title = "EL Calculation"

#     # Styles
#     header_font = Font(bold=True, color="000000")
#     center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
#     title_font = Font(bold=True, size=14)
#     subtitle_font = Font(bold=True, size=12)
#     thin_border = Border(
#         left=Side(style="thin"), right=Side(style="thin"),
#         top=Side(style="thin"), bottom=Side(style="thin")
#     )
#     fill_header = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
#     yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")

#     # Headers
#     fixed_headers = ["S.No", "Emp ID", "Name"]
#     sub_headers = ["P", "BH", "NPD"]
#     dynamic_months = get_months_list(from_date, to_date)  # ['Jan-24', 'Feb-24', ...]

#     total_columns = len(fixed_headers) + len(dynamic_months) * len(sub_headers)
#     # total_columns += 1  # Because we are starting from Column 2 (B)

#     # Row 1: Title
#     ws.merge_cells(start_row=1, start_column=2, end_row=1, end_column=total_columns)
#     cell = ws.cell(row=1, column=2, value="TS INTERSEATS INDIA PVT LTD")
#     cell.font = title_font
#     cell.alignment = center_align
#     cell.fill = yellow_fill
#     cell.border = thin_border  # Apply border

#     # Row 2: Subtitle
#     ws.merge_cells(start_row=2, start_column=2, end_row=2, end_column=total_columns)
#     cell = ws.cell(row=2, column=2, value="EL EARNINGS FOR THE YEAR OF 2024")
#     cell.font = subtitle_font
#     cell.alignment = center_align
#     cell.fill = yellow_fill
#     cell.border = thin_border  # Apply border

#     # Row 3 and 4: Headers
#     start_col = 1  # Start from column B

#     # Fixed headers (S.No, Emp ID, Name)
#     for idx, header in enumerate(fixed_headers):
#         col = start_col + idx
#         ws.merge_cells(start_row=3, start_column=col, end_row=4, end_column=col)
#         cell = ws.cell(row=3, column=col, value=header)
#         cell.font = header_font
#         cell.alignment = center_align
#         cell.fill = fill_header
#         cell.border = thin_border
#         ws.column_dimensions[get_column_letter(col)].width = 15

#     # Dynamic Month Headers
#     month_start_col = start_col + len(fixed_headers)
#     for month in dynamic_months:
#         merge_start = month_start_col
#         merge_end = month_start_col + 2

#         # Row 3: merged month name
#         ws.merge_cells(start_row=3, start_column=merge_start, end_row=3, end_column=merge_end)
#         for col in range(merge_start, merge_end + 1):
#             cell = ws.cell(row=3, column=col)
#             cell.border = thin_border

#         cell = ws.cell(row=3, column=merge_start, value=month)
#         cell.font = header_font
#         cell.alignment = center_align
#         cell.fill = fill_header

#         # Row 4: P, BH, NPD
#         for i, sub in enumerate(sub_headers):
#             col = month_start_col + i
#             cell = ws.cell(row=4, column=col, value=sub)
#             cell.font = header_font
#             cell.alignment = center_align
#             cell.fill = fill_header
#             cell.border = thin_border
#             ws.column_dimensions[get_column_letter(col)].width = 10

#         month_start_col += 3

#     # Row 5 onwards: Employee data
#     employees = get_employees(frappe._dict({
#         "from_date": from_date,
#         "to_date": to_date,
#         "employee": None
#     }))

#     data_start_row = 5
#     for idx, emp in enumerate(employees, start=1):
#         row = data_start_row + idx - 1
#         base_col = 2  # column B

#         # S.No
#         cell = ws.cell(row=row, column=base_col, value=idx)
#         cell.alignment = center_align
#         cell.border = thin_border

#         # Emp ID
#         cell = ws.cell(row=row, column=base_col + 1, value=emp.name)
#         cell.alignment = center_align
#         cell.border = thin_border

#         # Name
#         cell = ws.cell(row=row, column=base_col + 2, value=emp.employee_name)
#         cell.alignment = center_align
#         cell.border = thin_border

#         # Month-wise dummy data (replace with actual logic later)
#         data_col = base_col + 3
#         for month in dynamic_months:
#             for sub in sub_headers:
#                 cell = ws.cell(row=row, column=data_col, value=0)
#                 cell.alignment = center_align
#                 cell.border = thin_border
#                 data_col += 1

#     # Save file
#     output = io.BytesIO()
#     wb.save(output)
#     output.seek(0)

#     frappe.response['filename'] = 'EL Calculation.xlsx'
#     frappe.response['filecontent'] = output.getvalue()
#     frappe.response['type'] = 'binary'
#     frappe.response['doctype'] = None


# def get_months_list(from_date_str, to_date_str):
#     months = []
#     start = datetime.strptime(from_date_str, "%Y-%m-%d")
#     end = datetime.strptime(to_date_str, "%Y-%m-%d")

#     current = start
#     while current <= end:
#         months.append(current.strftime("%b-%y"))  # e.g. 'Jan-24'
#         current += relativedelta(months=1)

#     return months


# def get_employees(filters):
#     conditions = ''
#     if filters.get('employee'):
#         conditions += "AND employee = '%s' " % (filters['employee'])

#     employees = frappe.db.sql("""
#         SELECT name, employee_name, department, date_of_joining
#         FROM tabEmployee
#         WHERE status = 'Active' AND date_of_joining <= %s %s
#     """ % ("%s", conditions), (filters['to_date'],), as_dict=True)

#     left_employees = frappe.db.sql("""
#         SELECT name, employee_name, department, date_of_joining, relieving_date
#         FROM tabEmployee
#         WHERE status = 'Left' AND relieving_date >= %s %s
#     """ % ("%s", conditions), (filters['from_date'],), as_dict=True)

#     employees.extend(left_employees)
#     return employees


import frappe
import openpyxl
import io
from openpyxl.styles import PatternFill, Border, Side, Alignment, Font
from openpyxl.utils import get_column_letter
from datetime import datetime
from dateutil.relativedelta import relativedelta

@frappe.whitelist()
def download(from_date=None, to_date=None):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "EL Calculation"

    # Styles
    header_font = Font(bold=True, color="000000")
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    title_font = Font(bold=True, size=14)
    subtitle_font = Font(bold=True, size=12)
    thin_side = Side(style="thin", color="000000")
    thin_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
    fill_header = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")

    fixed_headers = ["S.No", "Emp ID", "Name"]
    sub_headers = ["P", "BH", "NPD"]
    total_sub_headers = ["P", "PH", "NPD"]  # For total columns, note PH instead of BH

    dynamic_months = get_months_list(from_date, to_date)  # e.g. ['Jan-24', 'Feb-24']

    # Calculate total columns = fixed + (months * sub_headers) + total_sub_headers(3 cols)
    total_columns = len(fixed_headers) + len(dynamic_months) * len(sub_headers) + len(total_sub_headers)
    start_col = 1  # Column A

    # Row 1: Title (merged)
    ws.merge_cells(start_row=1, start_column=start_col, end_row=1, end_column=total_columns)
    cell = ws.cell(row=1, column=start_col, value="TS INTERSEATS INDIA PVT LTD")
    cell.font = title_font
    cell.alignment = center_align
    cell.fill = yellow_fill
    for col in range(start_col, total_columns + 1):
        ws.cell(row=1, column=col).border = thin_border

    # Row 2: Subtitle (merged)
    ws.merge_cells(start_row=2, start_column=start_col, end_row=2, end_column=total_columns)
    cell = ws.cell(row=2, column=start_col, value="EL EARNINGS FOR THE YEAR OF 2024")
    cell.font = subtitle_font
    cell.alignment = center_align
    cell.fill = yellow_fill
    for col in range(start_col, total_columns + 1):
        ws.cell(row=2, column=col).border = thin_border

    # Fixed headers rows 3 & 4 (merged vertically)
    for idx, header in enumerate(fixed_headers):
        col = start_col + idx
        ws.merge_cells(start_row=3, start_column=col, end_row=4, end_column=col)
        cell = ws.cell(row=3, column=col, value=header)
        cell.font = header_font
        cell.alignment = center_align
        cell.fill = fill_header
        cell.border = thin_border
        ws.column_dimensions[get_column_letter(col)].width = 15

    # Dynamic month headers & subheaders
    month_start_col = start_col + len(fixed_headers)
    for month in dynamic_months:
        merge_start = month_start_col
        merge_end = month_start_col + len(sub_headers) - 1

        ws.merge_cells(start_row=3, start_column=merge_start, end_row=3, end_column=merge_end)
        month_cell = ws.cell(row=3, column=merge_start, value=month)
        month_cell.font = header_font
        month_cell.alignment = center_align
        month_cell.fill = fill_header
        for col in range(merge_start, merge_end + 1):
            ws.cell(row=3, column=col).border = thin_border
            ws.column_dimensions[get_column_letter(col)].width = 10

        for i, sub in enumerate(sub_headers):
            col = month_start_col + i
            sub_cell = ws.cell(row=4, column=col, value=sub)
            sub_cell.font = header_font
            sub_cell.alignment = center_align
            sub_cell.fill = fill_header
            sub_cell.border = thin_border

        month_start_col += len(sub_headers)

    # TOTAL WORKING FOR THE YEAR 2024 (merged 3 columns)
    total_col_start = month_start_col
    total_col_end = total_col_start + len(total_sub_headers) - 1

    ws.merge_cells(start_row=3, start_column=total_col_start, end_row=3, end_column=total_col_end)
    total_header_cell = ws.cell(row=3, column=total_col_start, value="TOTAL WORKING FOR THE YEAR 2024")
    total_header_cell.font = header_font
    total_header_cell.alignment = center_align
    total_header_cell.fill = fill_header
    for col in range(total_col_start, total_col_end + 1):
        ws.cell(row=3, column=col).border = thin_border
        ws.column_dimensions[get_column_letter(col)].width = 10

    for i, sub in enumerate(total_sub_headers):
        col = total_col_start + i
        sub_cell = ws.cell(row=4, column=col, value=sub)
        sub_cell.font = header_font
        sub_cell.alignment = center_align
        sub_cell.fill = fill_header
        sub_cell.border = thin_border

    # Employee data rows (start row 5)
    employees = get_employees(frappe._dict({
        "from_date": from_date,
        "to_date": to_date,
        "employee": None
    }))

    data_start_row = 5
    for idx, emp in enumerate(employees, start=1):
        row = data_start_row + idx - 1
        base_col = start_col

        # S.No
        cell = ws.cell(row=row, column=base_col, value=idx)
        cell.alignment = center_align
        cell.border = thin_border

        # Emp ID
        cell = ws.cell(row=row, column=base_col + 1, value=emp.name)
        cell.alignment = center_align
        cell.border = thin_border

        # Name
        cell = ws.cell(row=row, column=base_col + 2, value=emp.employee_name)
        cell.alignment = center_align
        cell.border = thin_border

        # Fetch present counts per month for employee
        present_map = get_present_counts_by_month(emp.name, from_date, to_date)

        data_col = base_col + len(fixed_headers)  # Starting after fixed headers

        # Month-wise data: Fill P with present count, others zero
        for month in dynamic_months:
            for sub in sub_headers:
                val = 0
                if sub == "P":
                    val = present_map.get(month, 0)
                cell = ws.cell(row=row, column=data_col, value=val)
                cell.alignment = center_align
                cell.border = thin_border
                data_col += 1

        # Total columns dummy data (P, PH, NPD)
        for _ in total_sub_headers:
            cell = ws.cell(row=row, column=data_col, value=0)  # replace with real total if needed
            cell.alignment = center_align
            cell.border = thin_border
            data_col += 1

    # Save to memory
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    frappe.response['filename'] = 'EL Calculation.xlsx'
    frappe.response['filecontent'] = output.getvalue()
    frappe.response['type'] = 'binary'
    frappe.response['doctype'] = None


def get_months_list(from_date_str, to_date_str):
    months = []
    start = datetime.strptime(from_date_str, "%Y-%m-%d")
    end = datetime.strptime(to_date_str, "%Y-%m-%d")
    current = start
    while current <= end:
        months.append(current.strftime("%b-%y"))  # e.g. 'Jan-24'
        current += relativedelta(months=1)
    return months


def get_employees(filters):
    conditions = ''
    if filters.get('employee'):
        conditions += "AND employee = '%s' " % (filters['employee'])

    employees = frappe.db.sql("""
        SELECT name, employee_name, department, date_of_joining
        FROM tabEmployee
        WHERE status = 'Active' AND date_of_joining <= %s %s
    """ % ("%s", conditions), (filters['to_date'],), as_dict=True)

    left_employees = frappe.db.sql("""
        SELECT name, employee_name, department, date_of_joining, relieving_date
        FROM tabEmployee
        WHERE status = 'Left' AND relieving_date >= %s %s
    """ % ("%s", conditions), (filters['from_date'],), as_dict=True)

    employees.extend(left_employees)
    return employees


def get_present_counts_by_month(employee, from_date, to_date):
    present_records = frappe.db.sql("""
        SELECT 
            MONTH(attendance_date) AS month,
            YEAR(attendance_date) AS year,
            COUNT(*) AS present_count
        FROM tabAttendance
        WHERE
            docstatus != 2
            AND employee = %s
            AND status = 'Present'
            AND attendance_date BETWEEN %s AND %s
        GROUP BY YEAR(attendance_date), MONTH(attendance_date)
    """, (employee, from_date, to_date), as_dict=True)

    present_map = {}
    for row in present_records:
        label = datetime(row['year'], row['month'], 1).strftime("%b-%y")  # e.g., "Jul-24"
        present_map[label] = row['present_count']

    return present_map
