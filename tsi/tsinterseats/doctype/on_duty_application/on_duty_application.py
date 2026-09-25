from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime, timedelta
from tsi.mark_attendance import update_att_with_employee

class OnDutyApplication(Document):
    def validate(self):
        # Check if an existing approved On Duty Application exists
        if frappe.db.exists("On Duty Application", {'employee': self.employee, 'od_date': self.od_date, 'docstatus': 1}):
            frappe.throw(_("On Duty Application Already Found for this Employee and Date"))
        if self.session =="Flexible":
        # Ensure flexible_time and flexible_to_time are valid before comparison
            if self.flexible_time and self.flexible_to_time:
                time_format = "%H:%M:%S"  # Adjust format if time is stored differently
                
                try:
                    from_time = datetime.strptime(str(self.flexible_time), time_format).time()
                    to_time = datetime.strptime(str(self.flexible_to_time), time_format).time()
                    
                    if from_time >= to_time:
                        frappe.throw(_("From time must be less than To time"))
                except ValueError:
                    frappe.throw(_("Invalid time format"))
    def on_submit(self):
        # Check if the submitted OnDuty application has a shift type, date, and session
        frappe.errprint('attendance11111')
        if self.shift and self.od_date and self.session:
            frappe.errprint('attendance')
            if isinstance(self.from_time, str):
                try:
                    start_time = datetime.strptime(self.from_time, "%H:%M:%S.%f")
                except ValueError:
                    start_time = datetime.strptime(self.from_time, "%H:%M")
            else:
                total_seconds = int(self.from_time.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
                start_time = datetime.strptime(time_str, "%H:%M:%S")

            if isinstance(self.to_time, str):
                try:
                    end_time = datetime.strptime(self.to_time, "%H:%M:%S.%f")
                except ValueError:
                    end_time = datetime.strptime(self.to_time, "%H:%M")
            else:
                total_seconds = int(self.to_time.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
                end_time = datetime.strptime(time_str, "%H:%M:%S")

            time_difference = end_time - start_time
            total_seconds = time_difference.total_seconds()
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            formatted_total_hours = '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))
            attendance = frappe.db.exists("Attendance", {
                "employee": self.employee,
                "attendance_date": self.od_date
            })
            frappe.errprint(attendance)
            if attendance:
                attendance_doc = frappe.get_doc("Attendance", attendance)
                if self.session == 'Flexible':
                    attendance_doc.on_duty_application = self.name
                    attendance_doc.session_from_time = self.flexible_time
                    attendance_doc.session_to_time = self.flexible_to_time
                    frappe.errprint("TEST!")
                    if isinstance(self.flexible_time, str):
                        try:
                            start_time_flex = datetime.strptime(self.flexible_time, "%H:%M:%S.%f")
                        except ValueError:
                            start_time_flex = datetime.strptime(self.flexible_time, "%H:%M")
                    else:
                        total_seconds = int(self.flexible_time.total_seconds())
                        hours, remainder = divmod(total_seconds, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
                        start_time_flex = datetime.strptime(time_str, "%H:%M:%S")
                    if isinstance(self.flexible_to_time, str):
                        try:
                            end_time_flex = datetime.strptime(self.flexible_to_time, "%H:%M:%S.%f")
                        except ValueError:
                            end_time_flex = datetime.strptime(self.flexible_to_time, "%H:%M")
                    else:
                        total_seconds = int(self.flexible_to_time.total_seconds())
                        hours, remainder = divmod(total_seconds, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
                        end_time_flex = datetime.strptime(time_str, "%H:%M:%S")
                    time_difference = end_time_flex - start_time_flex
                    frappe.errprint("TEST2")
                    frappe.errprint(attendance_doc.name)
                    total_seconds = time_difference.total_seconds()
                    hours, remainder = divmod(total_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    formatted_total_hours = '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))
                    attendance_doc.shift = self.shift
                    attendance_doc.total_working_hours = formatted_total_hours
                    attendance_doc.save(ignore_permissions=True)
                else:
                    if self.session == "Full day":
                        attendance_doc.status = "Present"
                        attendance_doc.shift_status = "P(OD)"
                    if self.session == "First Half":
                        if attendance_doc.status == "Half Day":
                            attendance_doc.status = "Present"
                            attendance_doc.shift_status = "OD/P"
                        else:
                            attendance_doc.status = "Half Day"
                            attendance_doc.shift_status = "HD(OD)"
                    if self.session == "Second Half":
                        if attendance_doc.status == "Half Day":
                            attendance_doc.status = "Present"
                            attendance_doc.shift_status = "P/OD"
                        else:
                            attendance_doc.status = "Half Day"
                            attendance_doc.shift_status = "HD(OD)"
                    attendance_doc.on_duty_application = self.name
                    attendance_doc.session_from_time = self.from_time
                    attendance_doc.session_to_time = self.to_time
                    attendance_doc.shift = self.shift
                    attendance_doc.total_working_hours = formatted_total_hours
                    attendance_doc.save(ignore_permissions=True)
            else:
                attendance_doc = frappe.new_doc("Attendance")
                attendance_doc.employee = self.employee
                attendance_doc.attendance_date = self.od_date
                if self.session == 'Flexible':
                    attendance_doc.on_duty_application = self.name
                    attendance_doc.session_from_time = self.flexible_time
                    attendance_doc.session_to_time = self.flexible_to_time
                    start_time_str=str(self.flexible_time)
                    end_time_str=str(self.flexible_to_time)
                    start_time = datetime.strptime(start_time_str, "%H:%M:%S")
                    end_time = datetime.strptime(end_time_str, "%H:%M:%S")
                    time_difference = end_time - start_time

                    # Calculate the time difference in seconds
                    total_seconds = time_difference.total_seconds()

                    # Calculate hours, minutes, and seconds from total seconds
                    hours, remainder = divmod(total_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)

                    # Format the total working hours as 'HH:MM:SS'
                    formatted_total_hours = '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))
                    attendance_doc.status = "Present"
                    attendance_doc.shift = self.shift
                    attendance_doc.total_working_hours = formatted_total_hours
                    attendance_doc.save(ignore_permissions=True)
                else:
                    if self.session == "Full day":
                        attendance_doc.status = "Present"
                        attendance_doc.shift_status = "P(OD)"
                    if self.session == "First Half":
                        attendance_doc.status = "Half Day"
                        attendance_doc.shift_status = "HD(OD)"
                    if self.session == "Second Half":
                        attendance_doc.status = "Half Day"
                        attendance_doc.shift_status = "HD(OD)"
                    attendance_doc.on_duty_application = self.name
                    attendance_doc.session_from_time = self.from_time
                    attendance_doc.session_to_time = self.to_time
                    attendance_doc.shift = self.shift
                    attendance_doc.total_working_hours = formatted_total_hours
                    attendance_doc.save(ignore_permissions=True)
                # attendance_doc.insert()
        elif self.session !="Flexible":
            frappe.msgprint(_("Please provide shift type, date, and session for the OnDuty application."))

    def on_cancel(self):
        if frappe.db.exists('Attendance',{'on_duty_application':self.name,'docstatus':['!=',2]}):
            att=frappe.db.get_value('Attendance',{'docstatus':['!=',2],'on_duty_application':self.name},['name'])
            frappe.db.set_value('Attendance',att,'on_duty_application','')
            if frappe.db.exists("Overtime Request",{'on_duty_application':self.name,'docstatus':['!=',2]}):
                ot=frappe.db.get_value("Overtime Request",{'on_duty_application':self.name,'docstatus':['!=',2]},['name'])
                frappe.db.set_value("Overtime Request",ot,'on_duty_application','')
                frappe.db.set_value("Overtime Request",ot,'ot_hour',0.0)
            att_doc=frappe.get_doc("Attendance",att)
            if att_doc.in_time and att_doc.out_time and att_doc.shift:        
                update_att_with_employee(self.od_date,self.od_date,self.employee)
            else:
                frappe.db.set_value('Attendance',att,'status','Absent')
                frappe.db.set_value('Attendance',att,'shift_status','AB')
                frappe.db.set_value('Attendance',att,'shift','')
                frappe.db.set_value('Attendance',att,'total_working_hours','00:00:00')
                frappe.db.set_value('Attendance',att,'total_overtime_hours','00:00:00')
                frappe.db.set_value('Attendance',att,'overtime_hours',0.0)
                frappe.db.set_value('Attendance',att,'working_hours',0.0)
                

    
        

@frappe.whitelist()
def get_shift_time(name):
    # Fetch the "Start Time" and "End Time" values based on the selected "Shift Type"
    shift_doc = frappe.get_doc("Shift Type", name)
    if shift_doc:
        # Calculate hours and minutes from timedelta objects
        start_hours, start_minutes = divmod(shift_doc.start_time.seconds // 60, 60)
        end_hours, end_minutes = divmod(shift_doc.end_time.seconds // 60, 60)

        # Convert hours and minutes to strings and format the time data
        start_time = '{:02}:{:02}'.format(start_hours, start_minutes)
        end_time = '{:02}:{:02}'.format(end_hours, end_minutes)

        return {
            "start_time": start_time,
            "end_time": end_time
        }
    else:
        return {}
   