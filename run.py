#!/usr/bin/python3

from __future__ import print_function
import boto3
from botocore.exceptions import ClientError
import json
import time
import datetime
import random
import string
from flask import Flask, jsonify, request, abort, make_response
import logme

app = Flask(__name__)

def unauthorized():
  return make_response(jsonify(
    {"status": "error",
    "message": "unauthorized"}
  ), 401)

@app.route('/', methods=['GET'])
def index():
  return make_response(jsonify(
    {'status': '200 OK',
    'message': 'make a resource request'}
  ), 200)

if __name__ == '__main__':
  app.run()
  # app.run(debug=True,host='0.0.0.0')
