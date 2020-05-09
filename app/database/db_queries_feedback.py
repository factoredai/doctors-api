import datetime as dt
import pymongo

def post_feedback(db, feedback_info):
    """creates new_feedback"""
    feedback_info['_feedback_date'] = dt.datetime.utcnow()
    inserted = db['feedback'].insert_one(feedback_info)

    return {
        'operation': 'insert',
        'inserted': inserted.acknowledged,
        '_feedback_date': feedback_info['_feedback_date']
    }
