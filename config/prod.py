import json

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
    'HOST': conn_info['JIRA']['HOSTS'][0],
    'PORT': conn_info['JIRA']['PORT'],
    'CLIENT_ID': conn_info['JIRA']['CLIENT_ID'],
    'PASSWORD': conn_info['JIRA']['CLIENT_SECRET']
}
JIRA_CLOUD_CONN_INFO = {
    'HOST': conn_info['JIRA_CLOUD']['HOSTS'][0],
    'PORT': conn_info['JIRA_CLOUD']['PORT'],
    'CLIENT_ID': conn_info['JIRA_CLOUD']['CLIENT_ID'],
    'PASSWORD': conn_info['JIRA_CLOUD']['CLIENT_SECRET']
}

JIRA_PROJECTS = ('RIVANNA', 'IVY', 'GENERAL_SUPPORT',
                 'UVA_RESEARCH_CONCIERGE_SERVICES', 'SENTINEL', 'CHASE')
JIRA_PROJECT_REQUEST_TYPES = (
    'RIVANNA_GET_IT_HELP',
    'IVY_GET_IT_HELP',
    'GENERAL_SUPPORT_TECHNICAL_SUPPORT',
    'ITHRIV_CONCIERGE_INQUIRY',
    'SENTINEL_GET_IT_HELP',
    'CHASE_GET_IT_HELP'
)

JIRA_PROJECT_INFO_LOOKUP = {
    JIRA_PROJECTS[0]: 2,
    JIRA_PROJECTS[1]: 1,
    JIRA_PROJECTS[2]: 10,
    JIRA_PROJECTS[3]: 13,
    JIRA_PROJECTS[4]: 12,
}

JIRA_PROJECT_REQUEST_TYPE_LOOKUP = {
    JIRA_PROJECT_REQUEST_TYPES[0]: 17,
    JIRA_PROJECT_REQUEST_TYPES[1]: 1,
    JIRA_PROJECT_REQUEST_TYPES[2]: 85,
    JIRA_PROJECT_REQUEST_TYPES[3]: 123,
    JIRA_PROJECT_REQUEST_TYPES[4]: 106
}

JIRA_CATEGORY_PROJECT_ROUTE_DICT = {
    'Rivanna Hpc': (JIRA_PROJECTS[0], JIRA_PROJECT_REQUEST_TYPES[0]),
    'Rivanna': (JIRA_PROJECTS[0], JIRA_PROJECT_REQUEST_TYPES[0]),
    'Ivy': (JIRA_PROJECTS[1], JIRA_PROJECT_REQUEST_TYPES[1]),
    'Software':
        (JIRA_PROJECTS[2], JIRA_PROJECT_REQUEST_TYPES[2]),
    'Storage': (JIRA_PROJECTS[2], JIRA_PROJECT_REQUEST_TYPES[2]),
    'Deans Allocation': (JIRA_PROJECTS[0], JIRA_PROJECT_REQUEST_TYPES[0]),
    'Consultation': (JIRA_PROJECTS[2], JIRA_PROJECT_REQUEST_TYPES[2]),
    'Other': (JIRA_PROJECTS[2], JIRA_PROJECT_REQUEST_TYPES[2]),
    'General': (JIRA_PROJECTS[2], JIRA_PROJECT_REQUEST_TYPES[2]),
    'Sentinel': (JIRA_PROJECTS[3], JIRA_PROJECT_REQUEST_TYPES[3]),
    'Chase': (JIRA_PROJECTS[4], JIRA_PROJECT_REQUEST_TYPES[4]),
    'Dcos': (JIRA_PROJECTS[2], JIRA_PROJECT_REQUEST_TYPES[2]),
    'Omero': (JIRA_PROJECTS[2], JIRA_PROJECT_REQUEST_TYPES[2]),
    'Skyline': (JIRA_PROJECTS[2], JIRA_PROJECT_REQUEST_TYPES[2]),
}

# SMTP Email Settings
MAIL_SERVER = conn_info["SMTP"]["HOSTS"][0]
MAIL_PORT = conn_info["SMTP"]["PORT"]
MAIL_USERNAME = conn_info["SMTP"]["CLIENT_ID"]
MAIL_PASSWORD = conn_info["SMTP"]["CLIENT_SECRET"]
MAIL_USE_SSL = False
MAIL_USE_TLS = False
MAIL_TIMEOUT = 10
MAIL_SECRET_KEY = conn_info["SMTP"]["SECURE_KEY"]

ALLOCATION_SPONSOR_EMAIL_LOOKUP = {
    'cas': 'dh2t@virginia.edu',
    'seas': 'wbk3a@virginia.edu',
    'dsi': 'lpa2a@virginia.edu',
    'hs': 'jcm6t@virginia.edu',
    'other': 'lpa2a@virginia.edu'
}
KONAMI_ENPOINT_DEFAULT_SENDER = 'nem2p@virginia.edu'
KONAMI_ENPOINT_DEFAULT_RECEIVER = 'nem2p@virginia.edu'
