import sys

from flask import Flask
from flask_restful import abort, Api
from resources.translate import Translator

app = Flask(__name__)
api = Api(app)

# Setup the Api resource routing here
# Route the URL to the resource
api.add_resource(Diagnostic, '/diagnostic')


if __name__ == '__main__':
    app.run(debug=True)
