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

    request_title = form_elements_dict.get('request_title')
    if('request-title' in form_elements_dict):
        request_title = form_elements_dict['request-title']

    project_ticket_route =\
        app.config['JIRA_CATEGORY_PROJECT_ROUTE_DICT'][
            category.strip().title()]
    submitted_attribs = list(form_elements_dict)
    desc_str = ''
    desc_html_str = ''
    name = None
    email = None
    username = None
    format_attribs_order = ['name', 'email', 'uid',
                            'department', 'category', 'description']
    for attrib in format_attribs_order:
        if (attrib in submitted_attribs):
            if(attrib == 'category'):
                value = category
            else:
                value = form_elements_dict[attrib]
                if(attrib == 'name'):
                    name = value
                if(attrib == 'email'):
                    email = value
                if(attrib == 'uid'):
                    username = value

            desc_str = ''.join([desc_str, '{}: {}\n'.format(
                str(attrib).strip().title(), value)])
            desc_html_str = ''.join([desc_html_str, '{}: {} \n\r'.format(
                str(attrib).strip().title(), value)])
            submitted_attribs.remove(attrib)

    drop_attribs = ['op', 'categories', 'request_title', 'request-title']
    submitted_attribs = list(set(submitted_attribs) - set(drop_attribs))
    for attrib in sorted(submitted_attribs):
        desc_str = ''.join([desc_str, '{}: {}\n'.format(
            str(attrib).strip().title(), form_elements_dict[attrib])])
        desc_html_str = ''.join([desc_html_str, '{}: {} \n\r'.format(
            str(attrib).strip().title(), form_elements_dict[attrib])])
    if request_title is not None:
        summary_str = request_title
    else:
        summary_str = '{} Request'.format(category)

    if (name is not None and name != '' and email is not None and email != ''):
        jira_service_handler.createNewCustomer(
            name=name,
            email=email
        )
    ticket_response = jira_service_handler.createNewTicket(
        reporter=email,
        project_name=project_ticket_route[0],
        request_type=project_ticket_route[1],
        summary=summary_str,
        desc=desc_str
    )
    # ticket_response = '{"issueKey":"RIV-1082"}'
    if (category == 'Deans Allocation'):
        email_service.send_hpc_allocation_confirm_email(
            from_email_address=form_elements_dict['email'],
            to_email_address=app.config['ALLOCATION_SPONSOR_EMAIL_LOOKUP'][form_elements_dict['sponsor']],
            subject=summary_str,
            ticket_id=json.loads(ticket_response)['issueKey'],
            callback_host=service_host,
            content_dict=form_elements_dict
        )

        jira_service_handler.addTicketComment(json.loads(
            ticket_response)['issueKey'], 'Approval request sent to the sponsor for confirmation')

    cc_email_addresses_list = None
    if ('financial-contact' in form_elements_dict
        and form_elements_dict['financial-contact'] is not None
            and form_elements_dict['financial-contact'] != ''):
        cc_email_addresses_list = [form_elements_dict['financial-contact']]
    if ((form_elements_dict.get('ptao1') is not None and form_elements_dict['ptao1'].lstrip() != '' and
         form_elements_dict.get('ptao2') is not None and form_elements_dict['ptao2'].lstrip() != '' and
         form_elements_dict.get('ptao3') is not None and form_elements_dict['ptao3'].lstrip() != '' and
         form_elements_dict.get(
             'ptao4') is not None and form_elements_dict['ptao4'].lstrip() != ''
         ) or (form_elements_dict.get('ptao') is not None and form_elements_dict['ptao'].lstrip() != '')):
        email_service.send_purchase_ack_email(
            from_email_address='hpc-support@virginia.edu',
            to_email_address=form_elements_dict['email'],
            cc_email_addresses=cc_email_addresses_list,
            subject=summary_str,
            ticket_id=json.loads(ticket_response)['issueKey'],
            content_dict=form_elements_dict
        )

    return ticket_response


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
                    and response['errorMessage'] is not None
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


@app.route('/rest/konami/', methods=['POST'])
@limiter.limit("6 per hour")
@limiter.limit("1 per minute")
def update_konami_discovery():
    try:
        if ('email' in request.form
            and request.form['email'] is not None
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
