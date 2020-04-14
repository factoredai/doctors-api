import datetime as dt
import pymongo

def get_patient_id(db, patient_id=None, doctor_id=None):
    """gets a patient by id"""
    query = {}
    if patient_id:
        query['patient_id'] = patient_id
    if doctor_id:
        query['doctor_id'] = doctor_id

    patient_info = db['diagnostic'].find(query, {
            'patient_id': 1,
            'doctor_id': 1 ,
            'diagnose': 1,
            'report_id': 1,
            '_diagnostic_date': 1,
            '_id': 0
        }).sort([("_diagnostic_date", pymongo.DESCENDING),
                 ("patient_id", pymongo.DESCENDING)])
    return list(patient_info)

def post_patient_id(patient_info, db):
    """creates a new patient  with patient info or updates
       if the patient already exists.
    """
    patient_info['_diagnostic_date'] = dt.datetime.now()
    inserted = db['diagnostic'].insert_one(patient_info)

    return inserted.acknowledged
