import os
import oracledb as oracle
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import re
import json
import requests
from requests.auth import HTTPDigestAuth
import datetime

import sys
sys.path.append('./structs/')
from structs import *
from tqdm import tqdm


class mongoDBController():
    def __init__(self):
        #self.run_requirements()
        self.OracleConnection = self.connect(option="Oracle")
        self.MongoConnection = self.connect(option="MongoDB")  
        if self.OracleConnection!=None and self.MongoConnection!=None:
            cursor = self.OracleConnection.cursor()
            self.dropDBs()
            self.ensureDBs()
            self.migrate()
            self.createViews()
            if self.testMongoAPI():
                functionId = self.createAtlasFunction("teste")
                if functionId:
                    self.createTrigger(functionId)
            self.runQueries()

            self.OracleConnection.close()
            self.MongoConnection.close()
            print("Migration Completed")
        else:
            print("Migration Failed")

    def dropDBs(self):
        #Drop the Oracle database
        
        try:
            print("Dropping Oracle databases")
            cursor = self.OracleConnection.cursor()
            #Lets get all the table names from the hospital.sql file
            file = open("./data/hospital.sql", "r")
            full_sql = file.read()
            regexTables = re.findall(r"CREATE TABLE (\w+)", full_sql)
            for table in regexTables:
                try:
                    cursor.execute("DROP TABLE " + table + " CASCADE CONSTRAINTS")
                except Exception as e:
                    pass

            regexProcedures = re.findall(r"CREATE OR REPLACE PROCEDURE (\w+)", full_sql)
            for procedure in regexProcedures:
                try:
                    cursor.execute("DROP PROCEDURE " + procedure)
                except Exception as e:
                    pass
            
            regexFunctions = re.findall(r"CREATE OR REPLACE FUNCTION (\w+)", full_sql)
            for function in regexFunctions:
                try:
                    cursor.execute("DROP FUNCTION " + function)
                except Exception as e:
                    pass
            regexTriggers = re.findall(r"CREATE OR REPLACE TRIGGER (\w+)", full_sql)
            for trigger in regexTriggers:
                try:
                    cursor.execute("DROP TRIGGER " + trigger)
                except Exception as e:
                    pass
                
            sequenceRegex = re.findall(r"CREATE SEQUENCE (\w+)", full_sql)
            for sequence in sequenceRegex:
                try:
                    cursor.execute("DROP SEQUENCE " + sequence)
                except Exception as e:
                    pass

            viewRegex = re.findall(r"CREATE VIEW (\w+)", full_sql)
            for view in viewRegex:
                try:
                    cursor.execute("DROP VIEW " + view)
                except Exception as e:
                    pass

            print("Oracle database dropped")


        except Exception as e:
            print("Error dropping the Oracle database")
            print("Exception: ", e)
        
        #Drop the MongoDB database
        try:
            #Lets drop the mongo database
            print("Dropping Mongo databases...")
            self.MongoConnection.drop_database("BDNOSQLTP")
            print("MongoDB database dropped")
        except Exception as e:
            print("Error dropping the MongoDB database")
            print("Exception: ", e)
    


    def ensureDBs(self):
        #Verify if the database is running in the Oracle connection
        #If not, create it
        #Verify if the database is running in the MongoDB connection
        #If not, create it
        try:
            self.ensureOracle()
            self.ensureMongo()
            return True
        except Exception as e:
            return False
        


    def migrate(self):

        try:
            
            #Lets get all the patients
            cursor = self.OracleConnection.cursor()
            cursor.execute("SELECT * FROM PATIENT")
            patients = cursor.fetchall()
            for patient in tqdm(patients, desc="Migrating patients", unit="patient"):
                try:
                    patientID = patient[0]
                    patientFname = patient[1]
                    patientLname = patient[2]
                    patientBloodType = patient[3]
                    patientPhone = patient[4]
                    patientEmail = patient[5]
                    patientGender = patient[6]
                    patientPolicyNumber = patient[7]
                    patientBirthday = patient[8]

                    
                    #Lets get the medical history of the patient   
                    cursor.execute(f"SELECT * FROM MEDICAL_HISTORY WHERE IDPATIENT = {patientID}")
                    medical_histories = cursor.fetchall()
                    medical_histories_list = []
                    for medical_history in medical_histories:
                        try:
                            medical_histories_list.append(MedicalHistory(medical_history[0], medical_history[3], medical_history[1], medical_history[2]))

                        except Exception as e:
                            pass
                    
                    #Lets get the insurance of the patient
                    
                    cursor.execute(f"SELECT * FROM INSURANCE WHERE policy_number='{patientPolicyNumber}'")
                    insurance = cursor.fetchone()
                    
                    try:
                        insurancePolNum = insurance[0]
                        insuranceProvider = insurance[1]
                        insuranceType = insurance[2]
                        insuranceCoPay = insurance[3]
                        insuranceCoverage = insurance[4]
                        insuranceMaternity = insurance[5]
                        insuranceDental = insurance[6]
                        insuranceVision = insurance[7]

                        patientInsurance = Insurance(insurancePolNum, insuranceProvider, insuranceType, insuranceCoPay, insuranceCoverage, insuranceMaternity, insuranceDental, insuranceVision)
                    except Exception as e:
                        print("Error getting the insurance of the patient")
                        print("Exception: ", e)
                    
                    #Lets get the emergency contacts of the patient
                    cursor.execute(f"SELECT * FROM EMERGENCY_CONTACT WHERE IDPATIENT = {patientID}")
                    emergency_contacts = cursor.fetchall()
                    emergency_contacts_list = []
                    for emergency_contact in emergency_contacts:
                        try:
                            emergencyContactName = emergency_contact[0]
                            emergencyContactPhone = emergency_contact[1]
                            emergencyContactRelation = emergency_contact[2]
                            emergency_contacts_list.append(EmergencyContact(emergencyContactName, emergencyContactPhone, emergencyContactRelation))
                        except Exception as e:
                            pass
                
                    #Lets get the patients episodes
                    cursor.execute(f"SELECT * FROM EPISODE WHERE PATIENT_IDPATIENT = {patientID}")
                    episodes = cursor.fetchall()
                    episodesList = []
                    
                    for episode in episodes:
                        episodeId = episode[0]
                        #Lets get the prescriptions of the episode
                        cursor.execute(f"SELECT * FROM PRESCRIPTION WHERE IDEPISODE = {episodeId}")
                        prescriptions = cursor.fetchall()
                        prescriptions_list = []
                        for prescription in prescriptions:
                            try:
                                prescriptionId = prescription[0]
                                prescriptionDate = prescription[1]
                                prescriptionMedicine = prescription[3]
                                prescriptionDosage = prescription[2]

                                #Lets get the medicine data
                                cursor.execute(f"SELECT * FROM MEDICINE WHERE IDMEDICINE = 1")
                                medicine = cursor.fetchone()
                                prescriptionMedicine = Medicine(medicine[0], medicine[1], medicine[2], medicine[3])

                                prescriptions_list.append(Prescription(prescriptionId, prescriptionDate, prescriptionMedicine, prescriptionDosage))
                            except Exception as e:
                                print("Error getting the prescriptions of the episode")
                        
                        #Lets get the bills of the episode
                        cursor.execute(f"SELECT * FROM BILL WHERE IDEPISODE = {episodeId}")
                        bills = cursor.fetchall()
                        bills_list = [] 
                        for bill in bills:
                            billId = bill[0]
                            billRoomCost = bill[1]
                            billTestCost = bill[2]
                            billAddCharges = bill[3]
                            billTotalCost = bill[4]
                            billRegisterDate = bill[6]
                            billPaymentStatus = bill[7]

                            bills_list.append(Bill(billId, billRoomCost, billTestCost, billAddCharges, billTotalCost, billRegisterDate, billPaymentStatus))

                        #Lets get the episodes screenings
                        cursor.execute(f"SELECT * FROM LAB_SCREENING WHERE EPISODE_IDEPISODE = {episodeId}")
                        screenings = cursor.fetchall()
                        screenings_list = []
                        for screening in screenings:
                            try:
                                screeningId = screening[0]
                                screeningCost = screening[1]
                                screeningDate = screening[2]
                                screeningTechnicianId = screening[3]

                                #Lets get the technician data
                                cursor.execute(f"SELECT STAFF_EMP_ID FROM TECHNICIAN WHERE STAFF_EMP_ID = {screeningTechnicianId}")
                                technician = cursor.fetchone()
                                screeningTechnicianId = technician[0]

                                #Lets get the technician data by querying the staff table
                                cursor.execute(f"SELECT * FROM STAFF WHERE EMP_ID = {screeningTechnicianId}")
                                technician = cursor.fetchone()
                                technicianDeptId = technician[8]

                                #Lets get the department data
                                cursor.execute(f"SELECT * FROM DEPARTMENT WHERE IDDEPARTMENT = {technicianDeptId}")
                                technicianDept = cursor.fetchone()
                                technicianDept = Department(technicianDept[0], technicianDept[1], technicianDept[2], technicianDept[3])

                                technician = Employee(technician[0], technician[1], technician[2], technician[3], technician[4], technician[5], technician[6], technician[7], technicianDept, technician[9])

                                screen = LabScreening(screeningId, screeningCost, screeningDate, technician)

                                screenings_list.append(screen)
                            except Exception as e:
                                print("Error getting the screenings of the episode")
                                print("Exception: ", e)

                        #Lets get the episodes appointment
                        cursor.execute(f"SELECT * FROM APPOINTMENT WHERE IDEPISODE = {episodeId}")
                        appointments = cursor.fetchall()
                        appointments_list = []
                        for appointment in appointments:
                            try:
                                scheduledOn = appointment[0]
                                appointmentDate = appointment[1]
                                appointmentTime = appointment[2]
                                appointmentDoctorId = appointment[3]
                                appointmentEpisodeId = appointment[4]

                                #Lets get the doctor data
                                cursor.execute(f"SELECT * FROM DOCTOR WHERE emp_id = {appointmentDoctorId}")
                                doctor = cursor.fetchone()
                                qualifications = doctor[1]

                                #Lets get the doctor data by querying the staff table
                                cursor.execute(f"SELECT * FROM STAFF WHERE EMP_ID = {appointmentDoctorId}")
                                doctor = cursor.fetchone()
                                doctorDeptId = doctor[8]
                                
                                #Lets get the department data
                                cursor.execute(f"SELECT * FROM DEPARTMENT WHERE IDDEPARTMENT = {doctorDeptId}")
                                doctorDept = cursor.fetchone()
                                doctorDept = Department(doctorDept[0], doctorDept[1], doctorDept[2], doctorDept[3])


                                doctor = Doctor(Employee(doctor[0], doctor[1], doctor[2], doctor[3], doctor[4], doctor[5], doctor[6], doctor[7], doctorDept, doctor[9]), qualifications)
                                #scheduled_on, appointment_date, appointment_time, doctor
                                appointments_list.append(Appointment(scheduledOn, appointmentDate, appointmentTime, doctor))
                            except Exception as e:
                                print("Error getting the appointments of the episode")
                                print("Exception: ", e)
                        
                        #Lets get all the hospitalizations of the episode
                        cursor.execute(f"SELECT * FROM HOSPITALIZATION WHERE IDEPISODE = {episodeId}")
                        hospitalizations = cursor.fetchall()
                        hospitalizations_list = []
                        for hospitalization in hospitalizations:
                            try:
                                hospitalizationAdmissionDate = hospitalization[0]
                                hospitalizationDischargeDate = hospitalization[1]
                                hospitalizationRoomId = hospitalization[2]
                                episodeId = hospitalization[3]
                                hospitalizationResponsibleNurseId = hospitalization[4]
                                

                                #Lets get the nurse data by querying the staff table
                                cursor.execute(f"SELECT * FROM STAFF WHERE EMP_ID = {hospitalizationResponsibleNurseId}")
                                nurse = cursor.fetchone()

                                #Lets get the department data
                                cursor.execute(f"SELECT * FROM DEPARTMENT WHERE IDDEPARTMENT = {nurse[8]}")
                                nurseDept = cursor.fetchone()
                                nurseDept = Department(nurseDept[0], nurseDept[1], nurseDept[2], nurseDept[3])
                                nurse = Employee(nurse[0], nurse[1], nurse[2], nurse[3], nurse[4], nurse[5], nurse[6], nurse[7], nurseDept, nurse[9])
                                
                                #Lets get the room data
                                cursor.execute(f"SELECT * FROM ROOM WHERE IDROOM = {hospitalizationRoomId}")
                                room = cursor.fetchone()
                                room = Room(room[0], room[1], room[2])

                                hospitalizations_list.append(Hospitalization(hospitalizationAdmissionDate, hospitalizationDischargeDate, room, nurse))
                            
                            #Verify for another migration in order to get to know why the episodes are empty
                            except Exception as e:
                                print("Error getting the hospitalizations of the episode")
                                print("Exception: ", e)

                        episodesList.append(Episode(episodeId, patientID, prescriptions_list, bills_list, screenings_list, appointments_list, hospitalizations_list))
                    
                    #Lets conver the Patient to  a json object and insert it into the MongoDB
                    patient = Patient(patientID, patientFname, patientLname, patientBloodType, patientPhone, patientEmail, patientGender, patientBirthday, medical_histories_list, patientInsurance, emergency_contacts_list, episodesList)
                    self.mongoDB["Patient"].insert_one(patient.to_json())

                except Exception as e:
                    print("Error migrating patient")
                    print("Exception: ", e)

            #Now that we have our database we will create the views
           
        except Exception as e:
            print("Error migrating from Oracle to MongoDB")
            print("Exception: ", e)

    def createViews(self):
         for view in self.sqlViews:
            #Lets get the view name
            viewName = re.findall(r"CREATE VIEW (\w+)", view)[0]

            #For each Patient apoointment we will get 
            #scheduled_on, appointment_date, appointment_time, doctor, department name, patient
            print("Creating view: ", viewName)
            self.mongoDB.create_collection(
                viewName,
                viewOn = "Patient",
                pipeline=[
                {
                    '$unwind': {
                        'path': '$episodes'
                    }
                }, {
                    '$unwind': {
                        'path': '$episodes.appointments'
                    }
                }, {
                    '$project': {
                        'appointment_scheduled_date': '$episodes.appointments.scheduled_on', 
                        'appointment_date': '$episodes.appointments.appointment_date', 
                        'appointment_time': '$episodes.appointments.appointment_time', 
                        'doctor_id': '$episodes.appointments.doctor.employee.employee_id', 
                        'doctor_qualifications': '$episodes.appointments.doctor.qualifications', 
                        'department_name': '$episodes.appointments.doctor.employee.department.dept_name', 
                        'patient_first_name': '$fname', 
                        'patient_last_name': '$lname', 
                        'patient_blood_type': '$blood_type', 
                        'patient_phone': '$phone', 
                        'patient_email': '$email', 
                        'patient_gender': '$gender'
                    }
                }
                ])
            
            print("View created in MongoDB")



    def ensureOracle(self):
        sql_command=""
        try:
            cursor = self.OracleConnection.cursor()


            # Lets execute the script hospotal.sql to create the tables
            file = open("./data/hospital.sql", "r")
            full_sql = file.read()

            #Lets capture the procedures and triggers from the script in order to then execute them in the mongo db
            proceduresRegex = r"CREATE\s+OR\s+REPLACE\s+PROCEDURE\s+\w+\s*\([^)]*\)\s*IS\s*[\s\S]*END;\s*\/"
            triggersRegex = r"CREATE\s+OR\s+REPLACE\s+TRIGGER\s+\w+\sAFTER\s[INSERT|UPDATE|DELETE]\sOF\s\w+\sON\s\w+\sFOR\sEACH\sROW\s*DECLARE\s+.*\s+BEGIN\s*[\s\S]*END;\s*\/"
            viewsRegex = r"CREATE\s+VIEW\s+\w+\sAS\s[\s\S]*?;"

            self.sqlprocedures = re.findall(proceduresRegex, full_sql)
            self.sqltriggers = re.findall(triggersRegex, full_sql)
            self.sqlViews = re.findall(viewsRegex, full_sql)
            
            #Lets verify if the tables already exist if so return
            regexTables = re.findall(r"CREATE TABLE (\w+)", full_sql)
            for table in regexTables:
                try:
                    cursor.execute(f"SELECT * FROM {table}")
                    print("Tables already created in Oracle. Skipping...")
                    return True
                except Exception as e:
                    pass

            #Lets strip them from the full_sql
            full_sql = re.sub(proceduresRegex, "", full_sql)
            full_sql = re.sub(triggersRegex, "", full_sql)
            #Lets capture all the comments from the script
           # comments = re.findall(r"/\*+[\s\S]*?\*+/", full_sql)
            full_sql = re.sub(r"/\*+[\s\S]*?\*+/", "", full_sql)

            # Split the script into individual statements
            sql_commands = full_sql.split(';')
            numCommands = len(sql_commands)
            commandId = 0
            for i in tqdm(range(numCommands), desc="Running SQL commands", unit="command"):
                try:
                    sql_command = sql_commands[i]
                    cursor.execute(sql_command.strip())
                except Exception as e:
                    pass

                commandId+=1

            #Lets execute the trigger and procedures for that we will remove all the ; in the trigger or procedure
            for procedure in self.sqlprocedures:
                try:
                    cursor.execute(procedure.strip())
                except Exception as e:
                    print(f"Error creating the procedure in Oracle: {procedure.strip()}")
                    print("Exception: ", e)

            for trigger in self.sqltriggers:
                try:
                    cursor.execute(trigger.strip())
                except Exception as e:
                    print(f"Error creating the trigger in Oracle: {trigger.strip()}")
                    print("Exception: ", e)

            # Lets get the procedures
            print("Tables created in Oracle")
            return True            
        
        except Exception as e:
            print("Error creating the table in Oracle")
            print("Exception: ", e)
            print("SQL Command: ", sql_command)
            return False
        

    # Probably not correct, but mongo creates the collection on the fly just by doing self.MongoConnection["BDNOSQLTP"]
    def ensureMongo(self):
        try:
            # In mongo I dont think that I have the need to create the database since I can retrieve it automatically
            self.mongoDB = self.MongoConnection["BDNOSQLTP"]
            return True
        except Exception as e:
            print("Error creating the collections in MongoDB")
            print("Exception: ", e)
            return False
        
    def testMongoAPI(self):
        url = "https://eu-west-2.aws.data.mongodb-api.com/app/data-moivwoh/endpoint/data/v1/action/findOne"
        payload = json.dumps({
            "collection": "Patient",
            "database": "BDNOSQLTP",
            "dataSource": "bdnosql",
            "projection": {
                "_id": 1
            }
        })
        headers = {
        'Content-Type': 'application/json',
        'Access-Control-Request-Headers': '*',
        'api-key': 'xkoPtLXJUZgJGRgmP7UQbbeP6prjC38UvfR9KcIPbvSDW33QahuLvsNNzSOjZhBJ',
        'Accept': 'application/ejson'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        
        if response.status_code == 200:
            print("API working")
            return True
        
        else:
            print("API not working")
            return False
        
    def createTrigger(self, trigger, functionId):
        #https://www.mongodb.com/docs/atlas/app-services/admin/api/v3/#tag/triggers/operation/adminCreateTrigger
        try:
            groupId = self.mongoGroupId
            appId = "data-moivwoh"
            uri = f"https://services.cloud.mongodb.com/api/admin/v3.0/groups/{groupId}/apps/{appId}/triggers"

            headers = {
                "Content-Type": "application/json",
                f"Authorization": "Bearer {self.mongoBearer}"
            }

            payload = {
                "name": trigger["name"],
                "type": "DATABASE",
                "function_id": functionId,
                "config": {
                    "operation_types": trigger["operations"],
                    "database": trigger["database"],
                    "collection": trigger["collection"],
                    "service_id": "5adeb649b8b998486770ae7c",
                    "match": {},
                    "project": {},
                    "full_document": True
                }
            }

            response = requests.post(uri, headers=headers, json=payload)

            if response.status_code == 201:
                print("Trigger created in MongoDB")
            else:
                print("Error creating the trigger in MongoDB")
                print("Response: ", response.json())

        except Exception as e:
            print("Error creating the trigger in MongoDB")
            print("Exception: ", e)


    def runQueries(self):
        #Lets load the queries from the queries.json file
        try:
            print("Running query: Get Patient by ID")
            if len(list(self.MongoConnection["BDNOSQLTP"]["Patient"].find({"patient_id": 1})))>0:
                print("Query executed successfully")
                

            print("Running query: Get Patient by Name")
            pipeline =[ { "$match": { "patient_id": 1 } }, 
                       { "$unwind": "$episodes" }]
            
            if len(list(self.MongoConnection["BDNOSQLTP"]["Patient"].aggregate(pipeline)))>0:
                print("Query executed successfully")
               
            
            print("Running query: Get all patients with specific blood type")
            result = self.MongoConnection["BDNOSQLTP"]["Patient"].find({ "blood_type": 'O-' })
            if len(list(self.MongoConnection["BDNOSQLTP"]["Patient"].find({ "blood_type": 'O-' })))>0:
                print("Query executed successfully")
               

            print("Running query: Find the average age of all Patients")
            pipeline = [
                    {"$group": 
                     {"_id": None, 
                        "averageAge": 
                            {"$avg": 
                             {"$divide": 
                                [
                                        {"$subtract": [
                                            datetime.datetime.now(), 
                                            "$birthday"
                                        ]}, 1000 * 60 * 60 * 24 * 365
                                ]
                             }
                            }
                     }
                    }
            ]
            if len(list(self.MongoConnection["BDNOSQLTP"]["Patient"].aggregate(pipeline)))>0:
                print("Query executed successfully")

            print("Running query: Find all the patients that have an appointment in a specific date")
            payload = [
                { "$unwind": "$episodes" },
                { "$unwind": "$episodes.appointments" },
                { "$match": { "episodes.appointments.appointment_date": datetime.datetime(2018, 11, 29, 0, 0) } }
            ]
            if len(list(self.MongoConnection["BDNOSQLTP"]["Patient"].aggregate(payload)))>0:
                print("Query executed successfully")
            
            pipeline = [
                { "$unwind": "$medical_history" },
                { "$group": { "_id": "$medical_history.condition", "frequency": { "$sum": 1 } } },
                { "$sort": { "frequency": -1 } },
                { "$limit": 1 }
            ]
            print("Running query: Find the most common medical condition")
            if len(list(self.MongoConnection["BDNOSQLTP"]["Patient"].aggregate(pipeline)))>0:
                print("Query executed successfully")
            
            print("All queries ran succesfully...")
               
        except Exception as e:
            print("Error loading the queries")
            print("Exception: ", e)


    def createAtlasFunction(self, function):
        #https://www.mongodb.com/docs/atlas/app-services/admin/api/v3/#tag/functions/operation/adminCreateFunction
        try:
            appId = "data-moivwoh"
            groupId = self.mongoProjectId

            functionCode = """
                exports = async function(changeEvent) {
                // A Database Trigger will always call a function with a changeEvent.
                // Documentation on ChangeEvents: https://docs.mongodb.com/manual/reference/change-events/
                console.log("Updated date in hospitalization");
                // This sample function will listen for events and replicate them to a collection in a different Database
                // Access the _id of the changed document:
                const docId = 0;
                console.log(changeEvent.operationType)

                // Get the MongoDB service you want to use (see "Linked Data Sources" tab)
                // Note: In Atlas Triggers, the service name is defaulted to the cluster name.
                const serviceName = "bdnosql";
                const database = "BDNOSQL";
                const collection = context.services.get(serviceName).db(database).collection(changeEvent.ns.coll);

                // Get the "FullDocument" present in the Insert/Replace/Update ChangeEvents
                try {

                    // If this is an "update" or "replace" event, then replace the document in the other collection
                    if (changeEvent.operationType === "update" || changeEvent.operationType === "replace") {
                    
                    var document = changeEvent.update.fullDocument;
                    var documentBefore = changeEvent.update.fullDocumentBeforeChange;
                    console.log("documentBefore");
                    console.log(documentBefore);
                    console.log("documentAfter\n");
                    console.log(document);
                    var flag = false;
                    

                    for (var i=0; i<documentBefore.episodes.length; i++) {
                        
                        for (var j=0; j<documentBefore.episodes[i].hospitalizations.length; j++) {
                            var hospitalizationBefore = documentBefore.episodes[i].hospitalizations[j]; 
                            var hospitalization = document.episodes[i].hospitalizations[j];
                            if (hospitalizationBefore.dischargeDate["$date"] == null && hospitalization.dischargeDate["$date"] != null) {
                                flag = true;

                                var roomCost = hospitalization.room["room_cost"];
                                console.log("Room Cost: "+roomCost);
                                
                                var testCost = 0;
                                for (var k=0; k<documentBefore.episodes[i].screenings.length; k++) {
                                    testCost += documentBefore.episodes[i].screenings[k].screening_cost;
                                }
                                console.log("Testing cost: "+testCost);
                    
                                var otherCharges = 0;
                                for (var k=0; k<documentBefore.episodes[i].prescriptions.length; k++) {
                                    otherCharges += documentBefore.episodes[i].prescriptions[k].medicine.medicine_cost * documentBefore.episodes[i].prescriptions[k].dosage;
                                }
                                console.log("Prescription Charges: "+otherCharges);
                    
                
                                var totalCost = roomCost + testCost + otherCharges;
                                
                                console.log("totalCost");
                                console.log(totalCost);
                
                                await collection.insertOne({
                                    idepisode: document.idepisode,
                                    room_cost: roomCost,
                                    test_cost: testCost,
                                    other_charges: otherCharges,
                                    total: totalCost,
                                    payment_status: "PENDING",
                                    registered_at: new Date()
                                });
                                
                                console.log("Cost of the room updated to: "+totalCost);
                            }
                        
                    }
                    if (!flag)
                        await collection.replaceOne({"_id": docId}, changeEvent.fullDocument);
                    }
                    
                    console.log("Succesfully updated the document");
                    }
                } catch(err) {
                    console.log("error performing mongodb write: ", err.message);
                }
                };
            """

            
            url = f"https://services.cloud.mongodb.com/api/admin/v3.0/groups/{groupId}/apps/{appId}/functions"
            payload = json.dumps({
                "name": function,
                "private" : False,
                "source" : functionCode
            })
            headers = {
            'Content-Type': 'application/json',
            'Access-Control-Request-Headers': '*',
            f'Authorization': 'Bearer {self.mongoBearer}',
            'Accept': 'application/ejson'
            }


            response = requests.request("POST", url, headers=headers, data=payload)
            if (response.status_code == 201):
                print("Function created in MongoDB")
                
                return response.json()["_id"]
            else:
                return False
            
        except Exception as e:
            return False


    def connect(self, option):
        if (option == "Oracle" or option==0):
            try: 
                load_dotenv()

                user_db = os.getenv('ORACLE_USER')
                password_db = os.getenv('ORACLE_PASSWORD')

                connection = oracle.connect(user=user_db, 
                                            mode=oracle.AUTH_MODE_SYSDBA,
                                            password=password_db,
                                            host="localhost", 
                                            port=1521, 
                                            service_name="xe"
                                        )


                print("Successfull connection to Oracle Database")
                return connection
            except Exception as e:
                print('Error connecting to the database: ', e)
                return None
            
        if (option == "MongoDB" or option==1):
            try:
                mongoUserName = os.getenv('MONGO_USER') 
                mongoPassword = os.getenv('MONGO_PASSWORD')
                uri = f"mongodb+srv://{mongoUserName}:{mongoPassword}@bdnosql.isx6fkl.mongodb.net/?retryWrites=true&w=majority&appName=bdnosql"

                client = MongoClient(uri, server_api=ServerApi('1'))
                client.admin.command('ping')

                self.mongoBearer = os.getenv('MONGO_BEARER')
                self.mongoProjectId = os.getenv('MONGO_PROJECT_ID')
                self.mongoGroupId = os.getenv('MONGO_GROUP_ID')
                
                print("Successfull connection to MongoDB Database")
                return client
            except Exception as e:
                print('Error connecting to the database')
                print("Error: ", e)
                return None

    def run_requirements(self):
        # Lets get all the installed pip packages
        os.system('pip install -r requirements.txt')



mongoDBController()
