from flask_restful import reqparse, Resource

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

        db.post_patient_id(#put args)

    def get(self):
        """ Receives a json containing _id, and returns user
            information.
        """
        db.get_patient_id(#puyt args)
