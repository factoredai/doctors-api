from flask_restful import reqparse, Resource
import json
import sys

#from evaluate import Eval
sys.path.insert(0, '../')
print(sys.path)
from database import db_handler as db

parser = reqparse.RequestParser()
parser.add_argument('query')

class Diagnostic(Resource):
    def post(self):
        """ Receives a json containing _id, and a string
            saves in a database.
            if id exists in database append text.
            returns OK HTTP 200
            return BAD_REQUEST HTTP 400 if bad JSON
        """
        parser = reqparse.RequestParser()
        try:
            parser.add_argument('_id', type=int, required=True, help='ID of patient. (Required)')
            parser.add_argument('diagnose', type=str, required=True, help='Diagnose of the patient')
        except:
            return {'status':400}
        args = parser.parse_args()
        _id = args['_id']
        diagnose = args['diagnose']
        response = db.post_patient_id(_id, diagnose)
        if response:
            return {'status': 200}
        else:
            return {'status':400}

    def get(self):
        """ Receives a json containing _id, and returns user
            information.
        """
        db.get_patient_id(#puyt args)
