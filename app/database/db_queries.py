
def get_patient_id(patient_id, db):
    """gets a patient by id"""
    patient_info = db['diagnostic'].find({
        'document': patient_id}, {
            'document': 1,
            'med_id': 1 ,
            'diagnose': 1,
            '_id': 0
        })
    return list(patient_info)

def post_patient_id(patient_info, db):
    """creates a new patient  with patient info or updates
       if the patient already exists.
    """
    inserted = db['diagnostic'].insert_one(patient_info)

    return inserted.acknowledged
