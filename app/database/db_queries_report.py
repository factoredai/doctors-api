import datetime as dt
import pymongo


def create_replace_report(db, report_info):
    """ Creates an apointment with user info and consent in false if is not
        present in appointment_info
    """

    if db['report'].find_one({'report_id': report_info['report_id']}):
        result = db['report'].update(
            {'report_id' : report_info['report_id']},
            {
                '$set' : {
                    'statuses' : report_info['statuses'],
                    '_last_update' : dt.datetime.utcnow()
                }
            }
        )

        return {
            'operation': 'update',
            'n_matched': result['n'],
            'modified': result['nModified']
        }

    report_info['_report_creation_date'] = dt.datetime.utcnow()
    report_info['_last_update'] = report_info['_report_creation_date']
    inserted = db['report'].insert_one(report_info)
    return {
        'operation': 'insert',
        'inserted': inserted.acknowledged,
        '_report_creation_date': report_info['_report_creation_date']
    }

def get_report_id(db, report_id):
    """Gets a report by and id from the database"""

    report_info = db['report'].find_one({'report_id': report_id}, {'_id': 0})

    return report_info
