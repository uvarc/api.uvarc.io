import json

from flask import jsonify, make_response, request

from app import app, limiter
from app.api.jira_service_handler import JiraServiceHandler


def unauthorized():
    return make_response(jsonify(
        {"status": "error",
         "message": "unauthorized"}
    ), 401)


def _create_jira_support_request(form_elements_dict):
    jira_service_handler = JiraServiceHandler(app)
    project_ticket_route = app.config['JIRA_CATEGORY_PROJECT_ROUTE_DICT']
    [form_elements_dict['category'].strip()]
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
        response = json.loads(_create_jira_support_request(request.form))

        return make_response(jsonify(
            {
                'status': '200 OK',
                'ticket_id': response['issueKey'],
                'name': request.form['name'],
                'email': request.form['email'],
                'uid': request.form['uid'],
                'message': 'General support request successfully submitted'
            }
        ), 200)
    except Exception as ex:
        return make_response(jsonify(
            {
                "status": "error",
                "message":
                    "Error submitting general support request : {}".format(
                        str(ex))
            }
        ), 501)


@app.route('/rest/hpc-allocation-request/', methods=['POST'])
@limiter.limit("6 per hour")
@limiter.limit("1 per minute")
def hpc_allocation_request():
    try:
        request_form = dict(request.form.items())
        request_form['category'] = "Rivanna HPC"

        response = json.loads(_create_jira_support_request(request_form))

        return make_response(jsonify(
            {
                'status': '200 OK',
                'ticket_id': response['issueKey'],
                'name': request.form['name'],
                'email': request.form['email'],
                'uid': request.form['uid'],
                'message': 'HPC allocation request successfully submitted'
            }
        ), 200)
    except Exception as ex:
        return make_response(jsonify(
            {
                "status": "error",
                "message":
                "Error submitting HPC allocation request : {}".format(str(ex))
            }
        ), 501)
