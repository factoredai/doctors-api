from flask_restful import reqparse, Resource

import sys

#from evaluate import Eval
sys.path.insert(0, '../')
print(sys.path)
from evaluate import Eval

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


    def get(self):
        """ Receives a json containing _id, and returns user
            information.
        """
