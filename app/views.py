import json

from flask import jsonify, make_response, request, redirect

import furl
from app import app, limiter
from app.api.jira_service_handler import JiraServiceHandler


def unauthorized():
    return make_response(jsonify(
        {"status": "error",
         "message": "unauthorized"}
    ), 401)


def _create_jira_support_request(form_elements_dict):
    jira_service_handler = JiraServiceHandler(app)
    project_ticket_route =\
        app.config['JIRA_CATEGORY_PROJECT_ROUTE_DICT'][
            form_elements_dict['category'].strip().title()]
    descStr = ''
    for attrib in sorted(form_elements_dict):
        descStr = ''.join([descStr, '{}={}\n'.format(
            str(attrib).upper(), form_elements_dict[attrib])])

    return jira_service_handler.createNewTicket(
        reporter=form_elements_dict['uid'],
        project_name=project_ticket_route[0],
        request_type=project_ticket_route[1],
        summary='Customer request for {}'.format(
            form_elements_dict['category']),
        desc=descStr
    )


@app.route('/rest/general-support-request/', methods=['POST'])
@limiter.limit("6 per hour")
@limiter.limit("2 per minute")
def general_support_request():
    try:
        f = furl.furl(request.referrer)
        f.remove(['ticket_id', 'message', 'status'])
        response = json.loads(_create_jira_support_request(request.form))

        return redirect(
            ''.join([f.url, '&status=', '200 OK', '&', 'message=',
                     'Support request ({}) successfully '
                     'created'.format(response['issueKey'])]))
    except Exception as ex:
        return redirect(
            ''.join([f.url, '&status=', 'error', '&', 'message=',
                     'Error submitting support '
                     'request: {}'.format(str(ex))]))


@app.route('/rest/hpc-allocation-request/', methods=['POST'])
@limiter.limit("6 per hour")
@limiter.limit("1 per minute")
def hpc_allocation_request():
    try:
        f = furl.furl(request.referrer)
        f.remove(['ticket_id', 'message', 'status'])
        request_form = dict(request.form.items())
        request_form['category'] = "Rivanna HPC"

        response = json.loads(_create_jira_support_request(request_form))

        return redirect(
            ''.join([f.url, '&status=', '200 OK', '&', 'message=',
                     'HPC Allocation request ({}) successfully '
                     'created'.format(response['issueKey'])]))
    except Exception as ex:
        return redirect(
            ''.join([f.url, '&status=', 'error', '&', 'message=',
                     'Error submitting HPC Allocation '
                     'request: {}'.format(str(ex))]))
