import json
import logging

NAME = 'UVARC Service'
VERSION = '0.1'


def fetch_connections_info(): return json.load(
    open('/etc/private/uvarc/connections.json'))

conn_info = fetch_connections_info()

ENV_BOOL_FLAGS_TUPLE = (conn_info['ENV'] in (
    'local', 'dev'), conn_info['ENV'] == 'prod')

DEVELOPMENT, PRODUCTION = ENV_BOOL_FLAGS_TUPLE
CORS_ENABLED = False
DEBUG = False

JIRA_CONN_INFO = {
    'HOST' : conn_info['JIRA']['HOSTS'][0],
    'PORT' : conn_info['JIRA']['PORT'],
    'CLIENT_ID' : conn_info['JIRA']['CLIENT_ID'],
    'PASSWORD' : conn_info['JIRA']['CLIENT_SECRET']
}

JIRA_PROJECTS = ('RIVANNA', 'IVY', 'GENERAL_SUPPORT')
JIRA_PROJECT_REQUEST_TYPES = ('RIVANNA_GET_IT_HELP', 'IVY_GET_IT_HELP', 'GENERAL_SUPPORT_TECHNICAL_SUPPORT')

JIRA_PROJECT_INFO_LOOKUP = {
    JIRA_PROJECTS[0]:2, 
    JIRA_PROJECTS[1]:1, 
    JIRA_PROJECTS[2]:10
}

JIRA_PROJECT_REQUEST_TYPE_LOOKUP = {
    JIRA_PROJECT_REQUEST_TYPES[0]:17,
    JIRA_PROJECT_REQUEST_TYPES[1]:1,
    JIRA_PROJECT_REQUEST_TYPES[2]:85
}

JIRA_CATEGORY_PROJECT_ROUTE_DICT = {
  'Rivanna HPC':(JIRA_PROJECTS[0], JIRA_PROJECT_REQUEST_TYPES[0]),
  'Ivy Secure Computing':(JIRA_PROJECTS[1], JIRA_PROJECT_REQUEST_TYPES[1]),
  'Licensed Research Software':(JIRA_PROJECTS[2], JIRA_PROJECT_REQUEST_TYPES[2]),
  'Storage':(JIRA_PROJECTS[2], JIRA_PROJECT_REQUEST_TYPES[2]),
  'Consultation':(JIRA_PROJECTS[2], JIRA_PROJECT_REQUEST_TYPES[2]),
  'Other':(JIRA_PROJECTS[2], JIRA_PROJECT_REQUEST_TYPES[2]),
}
