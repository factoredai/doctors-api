import datetime as dt
import pymongo
import random
import string


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

def get_appointment(db, patient_id=None, doctor_id=None):
    """gets a patient by id"""
    query = {}
    if patient_id:
        query['patient_id'] = patient_id
    if doctor_id:
        query['doctor_id'] = doctor_id

    appointment_info = db['appointment'].find(query, {
            'patient_id': 1,
            'doctor_id': 1 ,
            'videocall_code': 1,
            'informed_consent_accepted': 1,
            '_appointment_creation_date': 1,
            '_id': 0
        }).sort([("_appointment_creation_date", pymongo.DESCENDING),
                 ("patient_id", pymongo.DESCENDING)])
    return list(appointment_info)
