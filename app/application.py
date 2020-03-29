import os

from flask import Flask, make_response, jsonify
from flask_restful import abort, Api
from flask_restful import reqparse, Resource
from dotenv import load_dotenv

from app.database.db_setup import get_connection
from app.database.db_queries import post_patient_id, get_patient_id

load_dotenv()

app = Flask(__name__)
application = app # For beanstalk
api = Api(app)

MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('DB_NAME')

db_client = get_connection(mongo_uri=MONGO_URI)
db = db_client[DB_NAME]

parser = reqparse.RequestParser()
parser.add_argument('query')


def custom_error(message, status_code):
    return make_response(jsonify(message), status_code)


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
            parser.add_argument('document', type=str, required=True, help='ID of patient. (Required)')
            parser.add_argument('diagnose', type=str, required=True, help='Diagnose of the patient')
            parser.add_argument('med_id', type=str, required=True, help='ID of the doctor')
        except:
            return {'status': 400}
        patient_info = parser.parse_args()

        response = post_patient_id(patient_info, db)

        if response:
            return {'status': 200}
        else:
            return {'status': 400}

    def get(self):
        """ Receives a json containing _id, and returns user
            information.
        """

        parser.add_argument('id', required=True, help="Name cannot be blank!")
        args = parser.parse_args()
        patient_id = args['id']

        patient_info = get_patient_id(patient_id, db)
        print(patient_info)

        return patient_info if patient_info else custom_error("diagnostic not found", 404)


class HealthCheck(Resource):
    def get(self):
        try:
            info = db_client.server_info()
            return "Db OK"
        except Exception:
            return "DB error"


# Setup the Api resource routing here
# Route the URL to the resource
api.add_resource(Diagnostic, '/diagnostic')
api.add_resource(HealthCheck, '/')

