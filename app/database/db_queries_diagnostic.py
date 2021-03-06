import datetime as dt
import pymongo


def get_patient_id(db, patient_id=None, doctor_id=None, report_id=None, last_conduct=False):
    """gets a patient by id"""
    query = {}
    if patient_id:
        query['patient_id'] = patient_id
    if doctor_id:
        query['doctor_id'] = doctor_id
    if report_id:
        query['report_id'] = report_id

    patient_info = db['diagnostic'].find(query, {
            'patient_id': 1,
            'doctor_id': 1 ,
            'diagnose': 1,
            'report_id': 1,
            'risk': 1,
            '_diagnostic_date': 1,
            'conduct': 1,
            '_id': 0
        }).sort([("_diagnostic_date", pymongo.DESCENDING),
                 ("patient_id", pymongo.DESCENDING)])

    if last_conduct:
        patient_info = [patient_info[0]] if patient_info.count() else []

    return list(patient_info)

def post_patient_id(patient_info, db):
    """creates a new patient  with patient info or updates
       if the patient already exists.
    """

    if db['diagnostic'].find_one({'report_id': patient_info[
            'report_id'], 'patient_id': patient_info[
            'patient_id'], 'doctor_id': patient_info['doctor_id']}):
        result = db['diagnostic'].update(
            {
                'report_id': patient_info['report_id'],
                'patient_id': patient_info['patient_id'],
                'doctor_id': patient_info['doctor_id']
            },
            {
                '$set' : {
                    'conduct' : patient_info['conduct'],
                    'diagnose' : patient_info['diagnose'],
                    'risk': patient_info['risk'],
                    '_last_update':  dt.datetime.utcnow()
                }
            }
        )

        return {
            'operation': 'update',
            'n_matched': result['n'],
            'modified': result['nModified']
        }

    patient_info['_diagnostic_date'] = dt.datetime.utcnow()
    patient_info['_last_update'] = patient_info['_diagnostic_date']
    inserted = db['diagnostic'].insert_one(patient_info)

    return {
        'operation': 'insert',
        'inserted': inserted.acknowledged,
        '_diagnostic_date': patient_info['_diagnostic_date']
    }
