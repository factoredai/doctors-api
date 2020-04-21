import datetime as dt
import pymongo

def post_doctor_id(db, doctor_info):
    """creates a new doctor with doctor info or updates
       if the doctor already exists.
    """
    doctor_info['_request_date'] = dt.datetime.utcnow()
    doctor_info['registered'] = False
    inserted = db['doctor'].insert_one(doctor_info)

    return {
        'operation': 'insert',
        'inserted': inserted.acknowledged,
        '_request_date': doctor_info['_request_date']
    }

def modify_doctor(db, cellphone, email, registered):
    result = db['doctor'].update(
        {
            'cellphone' :  cellphone,
            'email' : email
        },
        {
            '$set' : {
                'registered' : registered,
                '_registration_date' : dt.datetime.utcnow()
            }
        },
        upsert=False
    )

    return {
        'operation' : 'update',
        'n_matched' : result['n'],
        'n_modified' : result['nModified']
    }

def get_doctor_application(db):
    """gets a doctor application by email"""
    query = {'registered' : False}

    doctor_application = db['doctor'].find(query, {
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

    return list(doctor_application)
