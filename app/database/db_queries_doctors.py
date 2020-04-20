import datetime as dt
import pymongo

def post_doctor_id(db, doctor_info):
    """creates a new doctor with doctor info or updates
       if the doctor already exists.
    """
    doctor_info['_request_date'] = dt.datetime.utcnow()
    inserted = db['doctors'].insert_one(doctor_info)

    return inserted.acknowledged, doctor_info['_request_date']

def get_doctor_application(db, doctor_email):
    """gets a doctor application by email"""
    query = {}
    if doctor_email:
        query['doctor_email'] = doctor_email

    doctor_application = db['doctors'].find(query, {
            'first_name': 1,
            'last_name': 1 ,
            'cellphone': 1,
            'email': 1,
            'professional_card_photo': 1,
            'conduct': 1,
            'official_id_photo': 1,
            '_request_date':1,
            '_id':0
        }).sort([("_request_date", pymongo.DESCENDING)])
    print(doctor_application)
    return list(doctor_application)

