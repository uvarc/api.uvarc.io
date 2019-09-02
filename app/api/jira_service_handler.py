import json

import requests


class JiraServiceHandler:
    def __init__(self, app):
        self._auth = (app.config['JIRA_CONN_INFO']['CLIENT_ID'],
                      app.config['JIRA_CONN_INFO']['PASSWORD'])
        self._connect_host_url = 'https://{}:{}/rest/'.\
            format(app.config['JIRA_CONN_INFO']['HOST'],
                   app.config['JIRA_CONN_INFO']['PORT'])
        self._default_reporter = app.config['JIRA_CONN_INFO']['CLIENT_ID']
        self._project_info_lookup_dict = app.config['JIRA_PROJECT_INFO_LOOKUP']
        self._project_request_type_lookup_dict =\
            app.config['JIRA_PROJECT_REQUEST_TYPE_LOOKUP']

    def createNewTicket(self,
                        reporter=None,
                        participants=None,
                        project_name='GENERAL_SUPPORT',
                        request_type='GENERAL_SUPPORT_GET_IT_HELP',
                        summary=None,
                        desc=None):
        if(reporter is None):
            reporter = self._default_reporter
        if(participants is None):
            participants = [reporter]
        headers = {'content-type': 'application/json'}
        payload = json.dumps(
            {
                "serviceDeskId":
                    self._project_info_lookup_dict[project_name.upper()],
                "requestTypeId":
                    self._project_request_type_lookup_dict[request_type.upper(
                    )],
                "requestFieldValues": {
                        "summary": summary,
                        "description": desc
                    },
                "requestParticipants": participants,
                "raiseOnBehalfOf": reporter
            }
        )
        r = requests.post(
            ''.join([self._connect_host_url, 'servicedeskapi/request']),
            headers=headers,
            data=payload,
            auth=self._auth
        )
        return r.text

    def addTicketComment(self, ticket_id, comment):
        headers = {
            "Content-Type": "application/json",
        }

        payload = json.dumps(
            {
                "body": comment,
                "public": "true"
            }
        )
        r = requests.post(
            ''.join([self._connect_host_url,
                     'servicedeskapi/request/{issueIdOrKey}/comment'.replace('{issueIdOrKey}', ticket_id)]),
            headers=headers,
            data=payload,
            auth=self._auth
        )
        return r.text
