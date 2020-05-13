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
from app.database.db_queries_doctors import post_doctor_id, get_doctor_application, modify_doctor
from app.database.db_queries_feedback import post_feedback, get_feedback

load_dotenv()

app = Flask(__name__)
app.url_map.strict_slashes = False
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
    def put(self):
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
        parser.add_argument('risk', type=str, required=False, help='Risk of the patient required',
                            choices=('low', 'medium', 'high'))

        patient_info = parser.parse_args()

        result = post_patient_id(patient_info, db)

        if result['operation'] == 'update':

            if result['modified']:
                return custom_response({
                    "code": "diagnostic modified",
                    "message": {
                        "esp": "diagnostico actualizado",
                        "eng": "diagnostic updated"
                    }
                }, 200)
            return custom_response({
                "code": "diagnostic not found" if not result['n_matched'] else "the diagnostic didn't change",
                "message": {
                    "esp": "diagnostico no encontrado" if not result['n_matched'] else "estado de diagnostico no cambio",
                    "eng": "diagnostico not found" if not result['n_matched'] else "the diagnostic didn't change"
                }}, 404 if not result['n_matched'] else 202)

        if not result['inserted']:
            return custom_response({
                "code": "insertion incompplete",
                "message": {
                    "esp": "diagnostico no se puedo ingresar contacte administrador",
                    "eng": "diagnostico couldn't be created, contact admin"
                }}, 202)
        return custom_response({
            "code": "new diagnositc",
            "message": {
                "_diagnostic_date": result['_diagnostic_date']
            }
        }, 201)

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

        args = request.args.to_dict()

        if 'summary' in args and args['summary']:
            summary = get_summary(db)
            return custom_response({"code": "summary", "message": {"accepted_consent_videocalls": summary}}, 200)

        token_valid = auth_handler.get_payload(request)
        if isinstance(token_valid, AuthError):
            return custom_response(token_valid.error, token_valid.status_code)

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


class Doctor(Resource):
    @cross_origin(headers=["Content-Type", "Authorization"])
    def get(self):
        parser = reqparse.RequestParser()
        token_valid = auth_handler.get_payload(request)
        if isinstance(token_valid, AuthError):
            return custom_response(token_valid.error, token_valid.status_code)

        doctor_application = get_doctor_application(db)

        return (custom_response({"code": "Application found", "message": doctor_application},
                               200) if doctor_application else custom_response({
                               "code": "Application is non existent",
                               "message": {
                                    "esp": "Aplicación no encontradas",
                                    "eng": "Application not found"
                               }}, 404))

    @cross_origin(headers=["Content-Type", "Authorization"])
    def patch(self):
        parser = reqparse.RequestParser()
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
                    "eng": "JSON with invalid syntax"
                }}, 400)

        email_regex = '(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'

        schema = {
                    'cellphone': {'type': 'string','required':True, 'regex': '[0-9]{10}'},
                    'email': {'type': 'string','required':True, 'regex': email_regex},
                    'registered' : {'type' : 'boolean', 'required': True}
                }
        validator = Validator(schema)

        if not validator.validate(body):
            return custom_response({'code': 'invalid json structure',
                                    'message':validator.errors}, 400)

        result = modify_doctor(db, cellphone=body['cellphone'],
                               email=body['email'], registered=body['registered'])

        if result['n_modified']:
            return custom_response({
                "code": "doctor registered",
                "message": {
                    "esp": "doctor se registró",
                    "eng": "doctor registered"
                }
            }, 200)

        return custom_response({
            "code": "doctor not found" if not result['n_matched'] else "the doctor status didn't change",
            "message": {
                "esp": "doctor no encontrado" if not result['n_matched'] else "estado de doctor no cambio",
                "eng": "doctor not found" if not result['n_matched'] else "the doctor status didn't change"
            }}, 404 if not result['n_matched'] else 202)

    def post(self):
        try:
            body = request.get_json()
        except:
            return custom_response({
                "code": "Bad JSON",
                "message": {
                    "esp": "El JSON está mal construido",
                    "eng": "JSON with invalid syntax"
                }}, 400)

        email_regex = '(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'
        schema = {
                    "first_name": {'type': 'string', 'required':True},
                    "last_name": {'type': 'string','required':True},
                    "cellphone": {'type': 'string','required':True, 'regex': '[0-9]{10}'},
                    "email": {'type': 'string','required':True, 'regex':email_regex},
                    "professional_card_photo": {'type': 'string','required':True},
                    "official_id_photo": {'type': 'string','required':True}
                }
        validator = Validator(schema)

        if not validator.validate(body):
            return custom_response({'code': 'Valores ingresados inválidos',
                                    'message':validator.errors}, 400)

        result = post_doctor_id(db, body)
        if result['inserted']:
            return custom_response({
                "code": "Solicitud realizada",
                "message":{
                    "creation_date" : result['_request_date']
                }
            }, 201)
        else:
            return custom_response({
                "code": "Application incomplete",
                "message": {
                    "esp": "La solicitud no se pudo crear contacte administrador",
                    "eng": "Application couldn't be created contact admin"
                }
                }, 202)


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
                    "code": "report modified",
                    "message": {
                        "esp": "reporte actualizado",
                        "eng": "report updated"
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

class Feedback(Resource):
    def post(self):
        try:
            body = request.get_json()
        except:
            return custom_response({
                "code": "Bad JSON",
                "message": {
                    "esp": "El JSON está mal construido",
                    "eng": "JSON with invalid syntax"
                }}, 400)

        schema = {
            "feedback": {'type': 'string', 'required':True}
        }
        validator = Validator(schema)

        if not validator.validate(body):
            return custom_response({'code': 'Valores ingresados inválidos',
                                    'message':validator.errors}, 400)

        result = post_feedback(db, body)

        if result['inserted']:
            return custom_response({
                "code": "feedback inserted",
                "message":{
                    "creation_date" : result['_feedback_date']
                }
            }, 201)
        else:
            return custom_response({
                "code": "feedback incomplete",
                "message": {
                    "esp": "sugerencia no se pudo crear contacte administrador",
                    "eng": "feedback couldn't be created contact admin"
                }
                }, 202)

    @cross_origin(headers=["Content-Type", "Authorization"])
    def get(self):
        token_valid = auth_handler.get_payload(request)
        if isinstance(token_valid, AuthError):
            return custom_response(token_valid.error, token_valid.status_code)

        feedback_info = get_feedback(db)

        return custom_response({"code": "feedback found", "message": feedback_info},
                               200) if feedback_info else custom_response({
                               "code": "feedback non existent",
                               "message": {
                                    "eng": "feedback doesn't exist",
                                    "esp": "sugerencias no existen"
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
api.add_resource(Doctor, '/doctor')
api.add_resource(Report, '/report')
api.add_resource(Feedback, '/feedback')
