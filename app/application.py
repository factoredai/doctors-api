import os
import json
import sys
import traceback
from flask import Flask, make_response, jsonify, request, _request_ctx_stack
from flask_restful import abort, Api, reqparse, Resource
from flask_cors import cross_origin, CORS
from dotenv import load_dotenv
from cerberus import Validator

from app.database.db_setup import get_connection
from app.database.db_queries_diagnostic import post_patient_id, get_patient_id
from app.database.db_queries_appointment import (post_appointment,
                                                 modify_appointment,
                                                 get_appointment,
                                                 get_summary)
from app.database.db_queries_report import create_replace_report, get_report_id
from app.helpers.auth import AuthHandler, AuthError

load_dotenv()

app = Flask(__name__)
api = Api(app)
CORS(app=app)

# Environment Variables
MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('DB_NAME')
AUTH0_DOMAIN = os.getenv('AUTH0_DOMAIN')
API_AUDIENCE = os.getenv('API_AUDIENCE')
ALGORITHMS = os.getenv('ALGORITHMS')
VIDEOCALL_CODE_SIZE = int(os.getenv('VIDEOCALL_CODE_SIZE'))

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
                "code": "diagnostic created",
                "message": {
                    "esp": "diagnostico creado",
                    "eng": "diagnostic created"
                }
            }, 201)
        else:
            return custom_response({
                "code": "insertion incompplete",
                "message": {
                    "esp": "diagnostico no se puedo ingresar contacte administrador",
                    "eng": "diagnostic couldn't be created, contact admin"
                }}, 202)

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

        if 'patient_id' not in args and 'doctor_id' not in args and 'report_id' not in args:
            return custom_response({
                "code": "missing parameter",
                "message": {
                    "eng": "patient or doctor id required",
                    "esp": "identificacion del doctor o del paciente requeridos"
                }}, 400)

        patient_id = (args['patient_id'] if 'patient_id' in args else None)
        doctor_id = (args['doctor_id'] if 'doctor_id' in args else None)
        report_id = (args['report_id'] if 'report_id' in args else None)
        last_conduct = (args['last_conduct'] if 'last_conduct' in args else False)

        patient_info = get_patient_id(db, patient_id=patient_id,
                                      doctor_id=doctor_id,
                                      report_id=report_id,
                                      last_conduct=last_conduct
                                      )

        return custom_response({"code": "diagnostics found", "message": patient_info},
                               200) if patient_info else custom_response({
                               "code": "diagnoses non existent",
                               "message": {
                                    "eng": "diagnoses non existent for those parameters",
                                    "esp": "diagnostico no existente para esos parametros de busqueda"
                               }}, 404)


class Appointment(Resource):
    @cross_origin(headers=["Content-Type", "Authorization"])
    def post(self):
        """ Receives appointment information
            doctor_id, patient_id, videocall_code, informed_consent_accepted
        """
        parser = reqparse.RequestParser()
        token_valid = auth_handler.get_payload(request)
        if isinstance(token_valid, AuthError):
            return custom_response(token_valid.error, token_valid.status_code)

        parser.add_argument('patient_id', type=str, required=True,
                            help='ID of patient. (Required)')
        parser.add_argument('doctor_id', type=str, required=True,
                            help='ID of the doctor')
        parser.add_argument('informed_consent_accepted', type=bool,
                            required=False)

        appointment_info = parser.parse_args()

        ack, creation_date, videocall_code = post_appointment(db,
                                                              appointment_info,
                                                              VIDEOCALL_CODE_SIZE)

        if ack:
            return custom_response({
                "code": "appointment created",
                "message":{
                    "creation_date" : creation_date,
                    "videocall_code" : videocall_code
                }
            }, 201)
        else:
            return custom_response({
                "code": "insertion incomplete",
                "message": {
                    "esp": "cita no se pudo crear contacte administrador",
                    "eng": "appointment couldn't be created contact admin"
                }
                }, 202)

    @cross_origin(headers=["Content-Type", "Authorization"])
    def get(self):
        """ Get appointment information by doctor_id, patient_id or both.
        """
        parser = reqparse.RequestParser()
        token_valid = auth_handler.get_payload(request)
        if isinstance(token_valid, AuthError):
            return custom_response(token_valid.error, token_valid.status_code)

        args = request.args.to_dict()

        if 'summary' in args and args['summary']:
            summary = get_summary(db)

            return custom_response({
                "code": "summary",
                "message": summary
            }, 200)

        if 'patient_id' not in args and 'doctor_id' not in args:
            return custom_response({
                "code": "missing parameter",
                "message": {
                    "esp": "para consultar citas debe ingresar id de paciente o doctor",
                    "eng": "to get appointments you must pprovide doctor's id or patient's"
                }}, 400)

        patient_id = (args['patient_id'] if 'patient_id' in args else None)
        doctor_id = (args['doctor_id'] if 'doctor_id' in args else None)

        appointment_info = get_appointment(db, patient_id=patient_id, doctor_id=doctor_id)

        return custom_response({"code": "appointments found", "message": appointment_info},
                               200) if appointment_info else custom_response({
                               "code": "appointments non existent",
                               "message": {
                                    "esp": "citas no encontradas",
                                    "eng": "appointments not found"
                               }}, 404)


    @cross_origin(headers=["Content-Type", "Authorization"])
    def patch(self):
        """ Modifies one or several fields of an appointment
        """
        parser = reqparse.RequestParser()
        token_valid = auth_handler.get_payload(request)
        if isinstance(token_valid, AuthError):
            return custom_response(token_valid.error, token_valid.status_code)

        body = request.get_json()

        if 'informed_consent_accepted' not in body or 'videocall_code' not in body:
            return custom_response({
                "code": "missing parameter",
                "message": {
                    "eng": "consent and video call code required",
                    "esp": "consentimiento y video llamada requerida"
                }}, 400)

        n_matched, modified = modify_appointment(db, videocall_code=body['videocall_code'],
                                      consent=body['informed_consent_accepted'])

        if modified:
            return custom_response({
                "code": "appointment modified",
                "message": {
                    "esp": "consentimiento actualizado",
                    "eng": "consent updated"
                }
            }, 200)
        else:
            return custom_response({
                "code": "appointment not found" if not n_matched else "videocall already consented",
                "message": {
                    "esp": "cita no encontrada" if not n_matched else "videollamada con consetimiento ya aprobado",
                    "eng": "appointment not found" if not n_matched else "videocall with consent already approved"
                }}, 404 if not n_matched else 202)


class Report(Resource):

    @cross_origin(headers=["Content-Type", "Authorization"])
    def put(self):
        """Insert a report with the status of the report so far, if the
           report doesn't exists create it, if it does replace it.
        """
        token_valid = auth_handler.get_payload(request)
        if isinstance(token_valid, AuthError):
            return custom_response(token_valid.error, token_valid.status_code)

        try:
            body = request.get_json()
        except:
            return custom_response({
                "code": "Bad JSON",
                "message": {
                    "esp": "El JSON está mal construido",
                    "eng": "JSON"
                }}, 400)

        schema = {
                    'report_id': {'type': 'string', 'required':True},
                    'statuses': {
                        'type' : 'list',
                        'required' : True,
                        'schema': {
                            'type' : 'dict',
                            'schema':{
                                'name' : {'type': 'string', 'required': True},
                                'active' : {'type': 'boolean', 'required': True}
                            }
                        }
                    }
                }
        validator = Validator(schema)

        if not validator.validate(body):
            return custom_response({'code': 'invalid values',
                                    'message':validator.errors}, 400)

        result = create_replace_report(db, body)

        if result['operation'] == 'update':

            if result['modified']:
                return custom_response({
                    "code": "appointment modified",
                    "message": {
                        "esp": "consentimiento actualizado",
                        "eng": "consent updated"
                    }
                }, 200)
            return custom_response({
                "code": "report not found" if not result['n_matched'] else "the report status didn't change",
                "message": {
                    "esp": "reporte no encontrado" if not result['n_matched'] else "estado de reporte no cambio",
                    "eng": "report not found" if not result['n_matched'] else "the report status didn't change"
                }}, 404 if not result['n_matched'] else 202)

        if not result['inserted']:
            return custom_response({
                "code": "insertion incompplete",
                "message": {
                    "esp": "reporte no se puedo ingresar contacte administrador",
                    "eng": "report couldn't be created, contact admin"
                }}, 202)
        return custom_response({
            "code": "new report",
            "message": {
                "_report_creation_date": result['_report_creation_date']
            }
        }, 201)

    @cross_origin(headers=["Content-Type", "Authorization"])
    def get(self):
        """Get report by id"""

        parser = reqparse.RequestParser()
        token_valid = auth_handler.get_payload(request)
        if isinstance(token_valid, AuthError):
            return custom_response(token_valid.error, token_valid.status_code)

        args = request.args.to_dict()

        if 'report_id' not in args:
            return custom_response({
                "code": "missing parameter",
                "message": {
                    "eng": "report id required",
                    "esp": "id del reporte requerido"
                }}, 400)

        report_info = get_report_id(db, report_id=args['report_id'])

        return custom_response({"code": "report found", "message": report_info},
                               200) if report_info else custom_response({
                               "code": "report non existent",
                               "message": {
                                    "eng": "report doesn't exist",
                                    "esp": "reporte no existe"
                               }}, 404)

class HealthCheck(Resource):
    def get(self):
        try:
            info = db_client.server_info()
            return make_response(jsonify({"message": 'DB_OK'}))
        except Exception:
            print('Error in healthcheck')
            print(traceback.format_exc())
            print("Error: %s", sys.exc_info())
            return "DB error"


# Setup the Api resource routing here
# Route the URL to the resource
api.add_resource(Diagnostic, '/diagnostic')
api.add_resource(HealthCheck, '/health-check')
api.add_resource(Appointment, '/appointment')
api.add_resource(Report, '/report')
