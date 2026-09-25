import frappe

@frappe.whitelist()
def update_mis_status_on_submit(doc, method):
    # Get the employee's name from the Full and Final Statement record
    employee = doc.employee

    # Update the MIS status of the employee to "Left"
    employee_doc = frappe.get_doc('Employee', employee)
    employee_doc.status = 'Left'
    employee_doc.save()
