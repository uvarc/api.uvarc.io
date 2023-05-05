import json
import os

NAME = 'UVARC Service'
VERSION = '0.2'

def fetch_connections_info():
    if 'SETTINGS_JSON' in os.environ:
        settings = json.loads(os.environ['SETTINGS_JSON'])
        settings["JIRA_CLOUD"]['CLIENT_SECRET'] = os.environ['JIRA_CLOUD_CLIENT_SECRET'].replace('\n','')
        settings["SMTP"]['SECURE_KEY'] = os.environ['SMTP_CLIENT_SECRET'].replace('\n','')
        settings["AWS"]['CLIENT_ID'] = os.environ['AWS_CLIENT_ID'].replace('\n','')
        settings["AWS"]['CLIENT_SECRET'] = os.environ['AWS_CLIENT_SECRET'].replace('\n','')
        return settings
    else:
        return json.load(open('/etc/private/uvarc/connections.json'))

conn_info = fetch_connections_info()
print(conn_info)

ENV_BOOL_FLAGS_TUPLE = (conn_info['ENV'] in (
    'local', 'dev'), conn_info['ENV'] == 'prod')

DEVELOPMENT, PRODUCTION = ENV_BOOL_FLAGS_TUPLE
CORS_ENABLED = False

JIRA_CLOUD_CONN_INFO = {
    'HOST': conn_info['JIRA_CLOUD']['HOSTS'][0],
    'PORT': conn_info['JIRA_CLOUD']['PORT'],
    'CLIENT_ID': conn_info['JIRA_CLOUD']['CLIENT_ID'],
    'PASSWORD': conn_info['JIRA_CLOUD']['CLIENT_SECRET']
}

AWS_CONN_INFO = {
    'CLIENT_ID': conn_info['AWS']['CLIENT_ID'],
    'CLIENT_SECRET': conn_info['AWS']['CLIENT_SECRET']
}

JIRA_PROJECTS = ('RIVANNA', 'IVY', 'GENERAL_SUPPORT',
                 'SENTINEL', 'CHASE', 'ACCORD_SUPPORT', 'UVA_RESEARCH_CONCIERGE_SERVICES')

JIRA_PROJECT_REQUEST_TYPES = (
    'RIVANNA_GET_IT_HELP',
    'IVY_GET_IT_HELP',
    'GENERAL_SUPPORT_TECHNICAL_SUPPORT',
    'SENTINEL_GET_IT_HELP',
    'CHASE_GET_IT_HELP',
    'ACCORD_SUPPORT_TECHNICAL_SUPPORT',
    'ITHRIV_CONCIERGE_INQUIRY',
)

JIRA_PROJECT_INFO_LOOKUP = {
    JIRA_PROJECTS[0]: 2,
    JIRA_PROJECTS[1]: 1,
    JIRA_PROJECTS[2]: 10,
    JIRA_PROJECTS[3]: 13,
    JIRA_PROJECTS[4]: 12,
    JIRA_PROJECTS[5]: 66,
}

JIRA_PROJECT_REQUEST_TYPE_LOOKUP = {
    JIRA_PROJECT_REQUEST_TYPES[0]: 17,
    JIRA_PROJECT_REQUEST_TYPES[1]: 1,
    JIRA_PROJECT_REQUEST_TYPES[2]: 85,
    JIRA_PROJECT_REQUEST_TYPES[3]: 123,
    JIRA_PROJECT_REQUEST_TYPES[4]: 106,
    JIRA_PROJECT_REQUEST_TYPES[5]: 536
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
    'Accord Support': (JIRA_PROJECTS[5], JIRA_PROJECT_REQUEST_TYPES[5]),
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

if DEVELOPMENT:
    DEBUG = True
    ALLOCATION_SPONSOR_EMAIL_LOOKUP = {
        'cas': 'rkc7h@virginia.edu',
        'seas': 'rkc7h@virginia.edu',
        'sds': 'rkc7h@virginia.edu',
        'hs': 'rkc7h@virginia.edu',
        'other': 'rkc7h@virginia.edu'
    }
    STORAGE_SPONSOR_EMAIL_LOOKUP = {
        'BII': ['5dc086be7dcf390c61844167'],
        'DS': ['5dc086be7dcf390c61844167', '5dcd9d408365670de7e906bf']
    }

    KONAMI_ENPOINT_DEFAULT_SENDER = 'rkc7h@virginia.edu'
    KONAMI_ENPOINT_DEFAULT_RECEIVER = 'rkc7h@virginia.edu'

if PRODUCTION:
    DEBUG = False
    ALLOCATION_SPONSOR_EMAIL_LOOKUP = {
        'cas': 'lg8b@virginia.edu',
        'seas': 'wbk3a@virginia.edu',
        'sds': 'vsh@virginia.edu',
        'hs': 'jcm6t@virginia.edu',
        'other': 'nem2p@virginia.edu,rkc7h@virginia.edu'
    }
    STORAGE_SPONSOR_EMAIL_LOOKUP = {
        'BII': ['qm:a75bda54-5373-4d0e-ad89-e747db3a3e8c%3A7220cbd2-3c35-40cb-8314-b6d1e8176afa'],
        'DS': ['qm:a75bda54-5373-4d0e-ad89-e747db3a3e8c:90fdaa72-1fd7-4fd5-a5d5-5d213744966f','qm:a75bda54-5373-4d0e-ad89-e747db3a3e8c:6e343f8e-15d2-42f2-b045-44e949b4fef6','qm:a75bda54-5373-4d0e-ad89-e747db3a3e8c:77e2eaba-3e0a-472e-8190-61ff8b01ccf6']
    }
    KONAMI_ENPOINT_DEFAULT_SENDER = 'nem2p@virginia.edu'
    KONAMI_ENPOINT_DEFAULT_RECEIVER = 'nem2p@virginia.edu'

