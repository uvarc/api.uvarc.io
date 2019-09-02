import json

from flask import jsonify, make_response, request, redirect, render_template

import furl
from itsdangerous import URLSafeTimedSerializer

from app import app, limiter, email_service
from app.api import ALLOC_APPROVE_CONFIRM_TYPES, RC_SMALL_LOGO_URL
from app.api.jira_service_handler import JiraServiceHandler


def unauthorized():
    return make_response(jsonify(
        {"status": "error",
         "message": "unauthorized"}
    ), 401)


def _process_support_request(form_elements_dict, service_host):
    jira_service_handler = JiraServiceHandler(app)
    category = form_elements_dict['category']
    if ('categories' in form_elements_dict):
        category = form_elements_dict['categories']

    project_ticket_route =\
        app.config['JIRA_CATEGORY_PROJECT_ROUTE_DICT'][
            category.strip().title()]
    submitted_attribs = list(form_elements_dict)
    desc_str = ''
    desc_html_str = ''
    format_attribs_order = ['name', 'email', 'uid',
                            'department', 'category', 'description']
    for attrib in format_attribs_order:
        if (attrib in submitted_attribs):
            if(attrib == 'category'):
                value = category
            else:
                value = form_elements_dict[attrib]
            desc_str = ''.join([desc_str, '{}: {}\n'.format(
                str(attrib).strip().title(), value)])
            desc_html_str = ''.join([desc_html_str, '{}: {} \n\r'.format(
                str(attrib).strip().title(), value)])
            submitted_attribs.remove(attrib)

    drop_attribs = ['op', 'categories']
    submitted_attribs = list(set(submitted_attribs) - set(drop_attribs))

    for attrib in sorted(submitted_attribs):
        desc_str = ''.join([desc_str, '{}: {}\n'.format(
            str(attrib).strip().title(), form_elements_dict[attrib])])
        desc_html_str = ''.join([desc_html_str, '{}: {} \n\r'.format(
            str(attrib).strip().title(), form_elements_dict[attrib])])
    summary_str = '{} Request'.format(category)

    ticket_response = jira_service_handler.createNewTicket(
        reporter=form_elements_dict['uid'],
        project_name=project_ticket_route[0],
        request_type=project_ticket_route[1],
        summary=summary_str,
        desc=desc_str
    )
    # ticket_response = '{"issueKey":"RIV-1082"}'
    if (category == 'Deans Allocation'):
        to_email_address = _send_allocation_approval_request(
            service_host=service_host,
            ticket_id=json.loads(ticket_response)['issueKey'],
            content=form_elements_dict
        )

        jira_service_handler.addTicketComment(json.loads(
            ticket_response)['issueKey'], 'Approval request sent to the sponsor for confirmation')

    return ticket_response


def _send_allocation_approval_request(service_host,
                                      ticket_id,
                                      content):

    tracking_code = email_service.send_hpc_allocation_confirm_email(
        from_email_address=content['email'],
        to_email_address=app.config['ALLOCATION_SPONSOR_EMAIL_LOOKUP'][content['sponsor']],
        subject='Deans Allocation Request',
        ticket_id=ticket_id,
        callback_host=service_host,
        content_dict=content
    )
    return app.config['ALLOCATION_SPONSOR_EMAIL_LOOKUP'][content['sponsor']]


@app.route('/rest/general-support-request/', methods=['POST'])
@limiter.limit("6 per hour")
@limiter.limit("2 per minute")
def general_support_request():
    try:
        f = furl.furl(request.referrer)
        f.remove(['ticket_id', 'message', 'status'])
        response = json.loads(_process_support_request(
            request.form, request.host_url))
        return redirect(
            ''.join([f.url, '&status=', '200 OK', '&', 'message=',
                     'Support request ({}) successfully '
                     'created'.format(response['issueKey'])]))
    except Exception as ex:
        print(ex)
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

        response = json.loads(_process_support_request(
            request_form, request.host_url))

        return redirect(
            ''.join([f.url, '&status=', '200 OK', '&', 'message=',
                     'HPC Allocation request ({}) successfully '
                     'created'.format(response['issueKey'])]))
    except Exception as ex:
        return redirect(
            ''.join([f.url, '&status=', 'error', '&', 'message=',
                     'Error submitting HPC Allocation '
                     'request: {}'.format(str(ex))]))


@app.route('/rest/confirm-hpc-allocation-request/<token>/', methods=['GET'])
@limiter.limit("6 per hour")
@limiter.limit("1 per minute")
def confirm_hpc_allocation_request(token):
    try:
        for salt_str in ALLOC_APPROVE_CONFIRM_TYPES:
            sig_okay, ticket_id = URLSafeTimedSerializer(
                app.config["MAIL_SECRET_KEY"]
            ).loads_unsafe(token, salt=salt_str, max_age=1209600)
            if (sig_okay):
                response = json.loads(JiraServiceHandler(
                    app).addTicketComment(ticket_id, ''.join(['Confirmation received from sponsor: ', salt_str])))
                if ('errorMessage' in response
                    and response['errorMessage'] != None
                        and response['errorMessage'] != ''):
                    raise Exception(response['errorMessage'])
                return render_template(
                    'confirm_response.html',
                    logo_url=RC_SMALL_LOGO_URL,
                    confirmation_str='Confirmation ({}) updated successfully. Thankyou'.format(
                        salt_str)
                )

        raise Exception(
            'The link for confirmation received has either expired or invalid. Please contact research computing')
    except Exception as ex:
        return render_template(
            'confirm_response.html',
            logo_url=RC_SMALL_LOGO_URL,
            confirmation_str='Error submitting HPC Allocation approval confirmation: {}'.format(
                str(ex))
        )


@app.route('/rest/konami/', methods=['GET'])
@limiter.limit("6 per hour")
@limiter.limit("1 per minute")
def update_konami_discovery():
    try:
        if ('email' in request.form
            and request.form['email'] != None
                and request.form['email'] != ''):
            email_service.send_email(
                subject='Konami discovered',
                sender=app.config['KONAMI_ENPOINT_DEFAULT_SENDER'],
                recipients=[app.config['KONAMI_ENPOINT_DEFAULT_RECEIVER']],
                text_body=request.form['email'],
                html_body=request.form['email']
            )
            return redirect('https://www.rc.virginia.edu')
        else:
            raise Exception('Email is missing')
    except Exception as ex:
        return make_response(jsonify(
            {
                "status": "error",
                "message":
                    "Error processing update_konami_discovery request : {}".format(
                        str(ex))
            }
        ))
