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

### ToDo ###
#
# 1. POST handler required for SUPPORT endpoint
#      https://staging.rc.virginia.edu/form/support-request/?email=bmVtMnBAdmlyZ2luaWEuZWR1&uid=bmVtMnA&name=TmVhbCBNYWdlZQ
# 2. POST handler required for CONSULTATION endpoint
#      https://staging.rc.virginia.edu/form/consult/?email=bmVtMnBAdmlyZ2luaWEuZWR1&uid=bmVtMnA&name=TmVhbCBNYWdlZQ
# 3. POST handler required for ALLOCATIONS forms:
#      - Standard
#      - Purchased
#      - Instructional
#      - Administrative (given by research deans)
#    https://staging.rc.virginia.edu/userinfo/rivanna/allocations/
#
###########

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

@app.route('/support', methods=['POST'])
def support():
  name = request.form['name']
  email = request.form['email']
  uid = request.form['uid']
  return make_response(jsonify(
    {'status': '200 OK',
    'name': name,
    'email': email,
    'uid': uid,
    'message': 'make a resource request'}
  ), 200)

if __name__ == '__main__':
  app.run()
  # app.run(debug=True,host='0.0.0.0')
