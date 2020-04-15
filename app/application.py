import os

from flask import Flask, make_response, jsonify, request, _request_ctx_stack
from flask_restful import abort, Api, reqparse, Resource
from flask_cors import cross_origin
from dotenv import load_dotenv

from app.database.db_setup import get_connection
from app.database.db_queries import post_patient_id, get_patient_id
from app.helpers.auth import AuthHandler, AuthError

load_dotenv()

app = Flask(__name__)
api = Api(app)

# Environment Variables
MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('DB_NAME')
AUTH0_DOMAIN = os.getenv('AUTH0_DOMAIN')
API_AUDIENCE = os.getenv('API_AUDIENCE')
ALGORITHMS = os.getenv('ALGORITHMS')

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
        token_valid = auth_handler.get_payload(request)
        if isinstance(token_valid, AuthError):
            return custom_response(token_valid.error, token_valid.status_code)

        parser.add_argument('patient_id', type=str, required=True, help='ID of patient. (Required)')
        parser.add_argument('diagnose', type=str, required=True, help='Diagnose of the patient')
        parser.add_argument('doctor_id', type=str, required=True, help='ID of the doctor')
        parser.add_argument('report_id', type=str, required=True, help='ID of the report')
        parser.add_argument('conduct', type=str, required=True, help='Recommendation for the patient required')

        patient_info = parser.parse_args()

        response = post_patient_id(patient_info, db)

        if response:
            return custom_response({
                "code": "Diagnostic Created",
                "Message": "Diagnostico creado"
            }, 201)
        else:
            return custom_response({
                "code": "Insertion incompplete",
                "message": "Diagnostico no se puedo ingresar contacte administrador"}, 202)

    @cross_origin(headers=["Content-Type", "Authorization"])
    def get(self):
        """ Receives a json containing _id, and returns user
            information.
        """
        parser = reqparse.RequestParser()

        token_valid = auth_handler.get_payload(request)
        if isinstance(token_valid, AuthError):
            return custom_response(token_valid.error, token_valid.status_code)

        args = request.args.to_dict()

        if 'patient_id' not in args and 'doctor_id' not in args:
            return custom_response({
                "code": "missing parameter",
                "description": "patient or doctor id required"}, 400)

        patient_id = (args['patient_id'] if 'patient_id' in args else None)
        doctor_id = (args['doctor_id'] if 'doctor_id' in args else None)

        patient_info = get_patient_id(db, patient_id=patient_id, doctor_id=doctor_id)

        return custom_response(patient_info, 200) if patient_info else custom_response({
            "code": "diagnoses non existent",
            "description": "diagnoses non existent for that parameters"}, 404)



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
api.add_resource(HealthCheck, '/health-check')

