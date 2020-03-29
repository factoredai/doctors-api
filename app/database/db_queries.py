
def get_patient_id(patient_id, db):
    """gets a patient by id"""
    patient_info = db['diagnostic'].find_one({'_id': patient_id})
    return patient_info

def post_patient_id(patient_info, db):
    """creates a new patient  with patient info or updates
       if the patient already exists.
    """
    if not db['diagnostic'].find_one({'_id': patient_info['_id']}):
        db['diagnostic'].insert_one(patient_info)
    else:
        current_diagnose = db['diagnostic'].find_one(
            {'_id': patient_info['_id']})['diagnose']

        current_diagnose = current_diagnose + '\n' + patient_info['diagnose']
        db['diagnostic'].update_one({
            '_id': patient_info['_id']
        }, {
            '$set': {
                'diagnose': current_diagnose
            }
        })
    return True
