import os

from flask import Flask, make_response, jsonify, request, _request_ctx_stack
from flask_restful import abort, Api, reqparse, Resource
from flask_cors import cross_origin
from dotenv import load_dotenv

from app.database.db_setup import get_connection
from app.database.db_queries import post_patient_id, get_patient_id
from app.helpers.auth import AuthHandler

load_dotenv()

app = Flask(__name__)
api = Api(app)

# Environment Variables
MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('DB_NAME')
AUTH0_DOMAIN = '5vid-dev.auth0.com'
API_AUDIENCE = 'api-dev.5vid.co'
ALGORITHMS = ["RS256"]

# Manage Database Connection
db_client = get_connection(mongo_uri=MONGO_URI)
db = db_client[DB_NAME]

auth_handler = AuthHandler(auth0_domain=AUTH0_DOMAIN, algorithms=ALGORITHMS,
                           api_identifier=API_AUDIENCE)

def custom_response(message, status_code):
    return make_response(jsonify(message), status_code)


class Diagnostic(Resource):

    @cross_origin(headers=["Content-Type", "Authorization"])
    def post(self):
        """ Receives a json containing _id, and a string
            saves in a database.
            if id exists in database append text.
            returns OK HTTP 200
            return BAD_REQUEST HTTP 400 if bad JSON
        """
        parser = reqparse.RequestParser()
        payload = auth_handler.get_payload(request)

        try:
            parser.add_argument('patient_id', type=str, required=True, help='ID of patient. (Required)')
            parser.add_argument('diagnose', type=str, required=True, help='Diagnose of the patient')
            parser.add_argument('doctor_id', type=str, required=True, help='ID of the doctor')
            parser.add_argument('report_id', type=str, required=True, help='ID of the report')
        except:
            return {'status': 400}
        patient_info = parser.parse_args()

        response = post_patient_id(patient_info, db)

        if response:
            return {'status': 200}
        else:
            return {'status': 400}

    @cross_origin(headers=["Content-Type", "Authorization"])
    def get(self):
        """ Receives a json containing _id, and returns user
            information.
        """

        parser.add_argument('patient_id', required=True, help="Id of the patient required")
        args = parser.parse_args()
        patient_id = args['id']

        patient_info = get_patient_id(patient_id, db)

        return patient_info if patient_info else custom_response("diagnostic not found", 404)


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
