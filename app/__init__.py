import logging
import os
import signal

import click
from flask import Flask, jsonify
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_httpauth import HTTPTokenAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_marshmallow import Marshmallow
from flask_sso import SSO
from app.api.email_service_handler import EmailService


app = Flask(__name__, instance_relative_config=True)

# Load the configuration from the instance folder
app.config.from_pyfile('settings.py')

if(app.config['DEBUG']):
    app.debug = True

# Enable CORS
if(app.config['CORS_ENABLED']):
    cors = CORS(app, resources={r"*": {"origins": "*"}})


# Flask-Marshmallow provides HATEOAS links
ma = Marshmallow(app)

# email service
email_service = EmailService(app)

# Single Signon
sso = SSO(app=app)

# Token Authentication
auth = HTTPTokenAuth('Bearer')

# Password Encryption
bcrypt = Bcrypt(app)

limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)

@app.cli.command()
def stop():
    """Stop the server."""
    pid = os.getpid()
    if pid:
        print('Stopping server...')
        os.kill(pid, signal.SIGTERM)
        print('Server stopped.')
    else:
        print('Server is not running.')


from app import views
