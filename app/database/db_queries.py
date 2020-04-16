import datetime as dt
import pymongo
import random
import string


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
            'conduct': 1,
            '_id': 0
        }).sort([("_diagnostic_date", pymongo.DESCENDING),
                 ("patient_id", pymongo.DESCENDING)])
    return list(patient_info)

def post_patient_id(patient_info, db):
    """creates a new patient  with patient info or updates
       if the patient already exists.
    """
    patient_info['_diagnostic_date'] = dt.datetime.utcnow()
    inserted = db['diagnostic'].insert_one(patient_info)

    return inserted.acknowledged, patient_info['_diagnostic_date']


def post_appointment(db, appointment_info, videocall_code_size):
    """ Creates an apointment with user info and consent in false if is not
        present in appointment_info
    """
    appointment_info['_appointment_creation_date'] = dt.datetime.utcnow()

    while True:
        videocall_code_rand = ''.join(
            random.choices(string.digits, k=videocall_code_size))
        if  not db['appointment'].find_one(
                {'videocall_code' : videocall_code_rand}):
            break

    appointment_info['videocall_code'] = videocall_code_rand
    appointment_info['informed_consent_accepted'] = (
        False if not appointment_info['informed_consent_accepted'] else True)

    inserted = db['appointment'].insert_one(appointment_info)

    return inserted.acknowledged, appointment_info[
        '_appointment_creation_date'], videocall_code_rand


def modify_appointment(db, consent, videocall_code):
    """Modify informed consent by videocall_code"""
    result = db['appointment'].update(
        {
            'videocall_code': videocall_code
        },
        {
            '$set' : {
                'informed_consent_accepted' : consent
            }
        },
        upsert=False
    )

    return result['n'], result['nModified']
