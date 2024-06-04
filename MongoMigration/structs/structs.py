class Patient:
    def __init__(self, patient_id, fname, lname, blood_type, phone, email, gender, birthday, medicalHistory, insurance, emergencyContacts, episodes):
        self.patient_id = patient_id
        self.fname = fname
        self.lname = lname
        self.blood_type = blood_type
        self.phone = phone
        self.email = email
        self.gender = gender
        self.birthday = birthday
        self.medical_histories = medicalHistory
        self.insurance = insurance
        self.emergency_contacts = emergencyContacts
        self.episodes = episodes

    def to_json(self):
        return {
            'patient_id': self.patient_id,
            'fname': self.fname,
            'lname': self.lname,
            'blood_type': self.blood_type,
            'phone': self.phone,
            'email': self.email,
            'gender': self.gender,
            'insurance': self.insurance.to_json(),
            'birthday': self.birthday,
           'medical_history': [medical_history.to_json() for medical_history in self.medical_histories],
           'emergency_contacts': [emergency_contact.to_json() for emergency_contact in self.emergency_contacts],
            'episodes': [episode.to_json() for episode in self.episodes]
        }
    
class MedicalHistory:
    def __init__(self, medical_history_id, patient_id, condition, record_date):
        self.medical_history_id = medical_history_id
        self.patient_id = patient_id
        self.condition = condition
        self.record_date = record_date
    
    def to_json(self):
        return {
            'medical_history_id': self.medical_history_id,
            'patient_id': self.patient_id,
            'condition': self.condition,
            'record_date': self.record_date
        }

class Insurance:
    def __init__(self, policy_number, provider, insurance_type, co_pay, coverage, maternity, dental, vision):
        self.policy_number = policy_number
        self.provider = provider
        self.insurance_type = insurance_type
        self.co_pay = co_pay
        self.coverage = coverage
        self.maternity = maternity
        self.dental = dental
        self.vision = vision

    def to_json(self):
        return {
            'policy_number': self.policy_number,
            'provider': self.provider,
            'insurance_type': self.insurance_type,
            'co_pay': self.co_pay,
            'coverage': self.coverage,
            'maternity': self.maternity,
            'dental': self.dental,
            'vision': self.vision
        }

class EmergencyContact:
    def __init__(self, name, phone, relation):
        self.name = name
        self.phone = phone
        self.relation = relation
    
    def to_json(self):
        return {
            'name': self.name,
            'phone': self.phone,
            'relation': self.relation
        }

class Episode:
    def __init__(self, episode_id, patient_id, prescriptions, bills, screenings, appointments, hospitalizations):
        self.episode_id = episode_id
        self.patient_id = patient_id
        self.prescriptions = prescriptions
        self.bills = bills
        self.screenings = screenings
        self.appointments = appointments
        self.hospitalizations = hospitalizations
    
    def to_json(self):
        return {
            'episode_id': self.episode_id,
            'patient_id': self.patient_id,
            'prescriptions': [prescription.to_json() for prescription in self.prescriptions],
            'bills': [bill.to_json() for bill in self.bills],
            'screenings': [screening.to_json() for screening in self.screenings],
            'appointments': [appointment.to_json() for appointment in self.appointments],
            'hospitalizations': [hospitalization.to_json() for hospitalization in self.hospitalizations]
        }

class Prescription:
    def __init__(self, prescription_id, prescription_date, medicine, dosage):
        self.prescription_id = prescription_id
        self.prescription_date = prescription_date
        self.medicine = medicine
        self.dosage = dosage
    
    def to_json(self):
        return {
            'prescription_id': self.prescription_id,
            'prescription_date': self.prescription_date,
            'medicine': self.medicine.to_json(),
            'dosage': self.dosage
        }
    
class Medicine:
    def __init__(self, medicine_id, medicine_name, medicine_quantity, medicine_cost):
        self.medicine_id = medicine_id
        self.medicine_name = medicine_name
        self.medicine_quantity = medicine_quantity
        self.medicine_cost = medicine_cost

    def to_json(self):
        return {
            'medicine_id': self.medicine_id,
            'medicine_name': self.medicine_name,
            'medicine_quantity': self.medicine_quantity,
            'medicine_cost': self.medicine_cost
        }


class Bill:
    def __init__(self, bill_id, room_cost, test_cost, add_charges, total_cost, register_date, payment_status):
        self.bill_id = bill_id
        self.room_cost = room_cost
        self.test_cost = test_cost
        self.add_charges = add_charges
        self.total_cost = total_cost
        self.register_date = register_date
        self.payment_status = payment_status

    def to_json(self):
        return {
            'bill_id': self.bill_id,
            'room_cost': self.room_cost,
            'test_cost': self.test_cost,
            'add_charges': self.add_charges,
            'total_cost': self.total_cost,
            'register_date': self.register_date,
            'payment_status': self.payment_status
        }

class LabScreening:
    def __init__(self, screening_id, screening_cost, screening_date, screening_technician):
        self.screening_id = screening_id
        self.screening_date = screening_date
        self.screening_technician = screening_technician
        self.screening_cost = screening_cost

    def to_json(self):
        return {
            'screening_id': self.screening_id,
            'screening_date': self.screening_date,
            'screening_technician': self.screening_technician.to_json(),
            'screening_cost': self.screening_cost
        }

class Appointment:
    def __init__(self, scheduled_on, appointment_date, appointment_time, doctor):
        self.scheduled_on = scheduled_on
        self.appointment_date = appointment_date
        self.appointment_time = appointment_time
        self.doctor = doctor

    def to_json(self):
        return {
            'scheduled_on': self.scheduled_on,
            'appointment_date': self.appointment_date,
            'appointment_time': self.appointment_time,
            'doctor': self.doctor.to_json()
        } 

class Doctor:
    def  __init__(self, employee, qualifications):
        self.employee = employee
        self.qualifications = qualifications

    def to_json(self):
        return {
            'employee': self.employee.to_json(),
            'qualifications': self.qualifications
        }
    
class Hospitalization:
    def __init__(self,admissionDate, dischargeDate, room, responsibleNurse):
        self.admissionDate = admissionDate
        self.dischargeDate = dischargeDate
        self.room = room
        self.responsibleNurse = responsibleNurse

    def to_json(self):
        return {
            'admissionDate': self.admissionDate,
            'dischargeDate': self.dischargeDate,
            'room': self.room.to_json(),
            'responsibleNurse': self.responsibleNurse.to_json()
        }
    
class Nurse:
    def __init__(self, employee):
        self.employee = employee

    def to_json(self):
        return {
            'employee': self.employee.to_json()
        }
    
class Room:
    def __init__(self, room_id, room_type, room_cost):
        self.room_id = room_id
        self.room_type = room_type
        self.room_cost = room_cost

    def to_json(self):
        return {
            'room_id': self.room_id,
            'room_type': self.room_type,
            'room_cost': self.room_cost
        }

class Employee:
    def __init__(self, employee_id, fname, lname, dateJoining, dateSeparation, email, address,ssn, department, is_active):
        self.employee_id = employee_id
        self.fname = fname
        self.lname = lname
        self.dateJoining = dateJoining
        self.dateSeparation = dateSeparation
        self.email = email
        self.address = address
        self.ssn = ssn
        self.department = department
        self.is_active = is_active
    
    def to_json(self):
        return {
            'employee_id': self.employee_id,
            'fname': self.fname,
            'lname': self.lname,
            'dateJoining': self.dateJoining,
            'dateSeparation': self.dateSeparation,
            'email': self.email,
            'address': self.address,
            'department': self.department.to_json(),
            'ssn': self.ssn,
            'is_active': self.is_active
        }
    
class Department:
    def __init__(self, department_id, dept_head, dept_name, dept_employeeCount):
        self.department_id = department_id
        self.dept_head = dept_head
        self.dept_name = dept_name
        self.dept_employeeCount = dept_employeeCount
    
    def to_json(self):
        return {
            'department_id': self.department_id,
            'dept_head': self.dept_head,
            'dept_name': self.dept_name,
            'dept_employeeCount': self.dept_employeeCount
        }