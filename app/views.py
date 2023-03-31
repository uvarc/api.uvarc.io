# encoding=utf8
from app.api.jira_service_handler import JiraServiceHandler
from app.api import ALLOC_APPROVE_CONFIRM_TYPES, RC_SMALL_LOGO_URL, DecimalEncoder
from app import app, limiter, email_service, aws_service
from itsdangerous import URLSafeTimedSerializer
import boto3
import furl
from flask import jsonify, make_response, request, redirect, render_template
import json
import sys


def unauthorized():
    return make_response(jsonify(
        {"status": "error",
         "message": "unauthorized"}
    ), 401)


def _process_support_request(form_elements_dict, service_host, version):
    jira_service_handler = JiraServiceHandler(app, version != "v1")
    category = form_elements_dict['category']
    if ('categories' in form_elements_dict):
        category = form_elements_dict['categories']

    request_title = form_elements_dict.get('request_title')
    components = None
    if('request-title' in form_elements_dict):
        request_title = form_elements_dict['request-title']
    is_rc_project = False
    if "JIRA_PROJECT_TICKET_ROUTE" in form_elements_dict:
        project_ticket_route = tuple(form_elements_dict.get(
            "JIRA_PROJECT_TICKET_ROUTE").split('|'))
        if(len(project_ticket_route) > 2):
            components = project_ticket_route[2]
    else:
        is_rc_project = True
        project_ticket_route =\
            app.config['JIRA_CATEGORY_PROJECT_ROUTE_DICT'][
                category.strip().title()]
    submitted_attribs = list(form_elements_dict)
    desc_str = ''
    desc_html_str = ''
    name = None
    email = None
    username = None
    department = ''
    school = ''
    format_attribs_order = ['name', 'email', 'uid',
                            'department', 'school', 'category', 'description']
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
                if attrib == 'department':
                    department = value
                if attrib == 'school':
                    school = value
            if attrib != 'department' and attrib != 'school':
                desc_str = ''.join([desc_str, '{}: {}\n'.format(
                    str(attrib).strip().title(), value)])
                desc_html_str = ''.join([desc_html_str, '{}: {} \n\r'.format(
                    str(attrib).strip().title(), value)])
            submitted_attribs.remove(attrib)

    drop_attribs = [
        'op', 'categories', 'request_title',
        'request-title', 'JIRA_PROJECT_TICKET_ROUTE',
        'REQUEST_CLIENT'
    ]
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
        try:
            jira_service_handler.create_new_customer(
                name=name,
                email=email,
            )
        except Exception as ex:
            app.log_exception(ex)
            print(ex) 
    ticket_response = jira_service_handler.create_new_ticket(
        reporter=email,
        project_name=project_ticket_route[0],
        request_type=project_ticket_route[1],
        components=components,
        summary=summary_str,
        desc=desc_str,
        department=department,
        school=school,
        is_rc_project=is_rc_project
    )
    print(ticket_response)
    # ticket_response = '{"issueKey":"RIV-1082"}'
    aws_service.update_dynamodb_jira_tracking(
        json.loads(ticket_response)['issueKey'],
        json.loads(ticket_response)['createdDate']['jira'],
        username,
        email,
        summary_str
    )

    # try:
    #     dynamodbSession = boto3.Session(
    #         aws_access_key_id='AKIAW5BKWSI5YOXZR2FO', 
    #         aws_secret_access_key='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', 
    #         region_name='us-east-1'
    #     )
    #     dynamodb = dynamodbSession.resource('dynamodb')
    #     table = dynamodb.Table('jira-tracking')

    #     response = table.put_item(
    #         Item={
    #             'key': json.loads(ticket_response)['issueKey'],
    #             'submitted': json.loads(ticket_response)['createdDate']['jira'],
    #             'uid': username,
    #             'email': email,
    #             'type': summary_str
    #         }
    #     )
    #     print(json.dumps(response, indent=4, cls=DecimalEncoder))
    # except Exception as ex:
    #     app.log_exception(ex);
    #     print(str(ex))

    if (category == 'Deans Allocation'):
        email_service.send_hpc_allocation_confirm_email(
            from_email_address=form_elements_dict['email'],
            to_email_address=app.config['ALLOCATION_SPONSOR_EMAIL_LOOKUP'][form_elements_dict['sponsor']],
            subject=summary_str,
            ticket_id=json.loads(ticket_response)['issueKey'],
            callback_host=service_host,
            content_dict=form_elements_dict
        )

        jira_service_handler.add_ticket_comment(json.loads(
            ticket_response)['issueKey'], 'Approval request sent to the sponsor for confirmation')

    cc_email_addresses_list = None
    if ('financial-contact' in form_elements_dict
        and form_elements_dict['financial-contact'] is not None
            and form_elements_dict['financial-contact'] != ''):
        cc_email_addresses_list = [form_elements_dict['financial-contact']]
    if ((form_elements_dict.get('ptao1') is not None and form_elements_dict['ptao1'].lstrip() != '' and
         form_elements_dict.get('ptao2') is not None and form_elements_dict['ptao2'].lstrip() != '' and
         form_elements_dict.get('ptao3') is not None and form_elements_dict['ptao3'].lstrip() != '' and
         form_elements_dict.get('ptao4') is not None and form_elements_dict['ptao4'].lstrip() != '') or 
         (form_elements_dict.get('ptao') is not None and form_elements_dict['ptao'].lstrip() != '')):
        pass
        # email_service.send_purchase_ack_email(
        #     from_email_address='hpc-support@virginia.edu',
        #     to_email_address=form_elements_dict['email'],
        #     cc_email_addresses=cc_email_addresses_list,
        #     subject=summary_str,
        #     ticket_id=json.loads(ticket_response)['issueKey'],
        #     content_dict=form_elements_dict
        # )

    return ticket_response


@app.route('/rest/<version>/general-support-request/', methods=['POST'])
@app.route('/rest/general-support-request/', methods=['POST'])
@limiter.limit("30 per hour")
@limiter.limit("10 per minute")
def general_support_request(version='v2'):
    try:
        f = furl.furl(request.referrer)
        f.remove(['ticket_id', 'message', 'status'])
        response = json.loads(_process_support_request(
            request.form, request.host_url if 'localhost' in request.host_url else request.host_url.replace(
                'http', 'https'), version))
        response_url = "http://localhost:1313/thank-you/?" if 'localhost' in request.host_url else "https://www.rc.virginia.edu/thank-you/?"
        if ('REQUEST_CLIENT' in request.form
                and request.form['REQUEST_CLIENT'] == 'ITHRIV'):
            return make_response(jsonify(
                {
                    'status': '200 OK',
                    'ticket_id': response['issueKey'],
                    'message': 'General support request successfully submitted'
                }
            ), 200)
        else:
            return redirect(
                ''.join([response_url, '&status=', '200 OK', '&', 'message=',
                         'Support request ({}) successfully '
                         'created'.format(response['issueKey'])]))
    except Exception as ex:
        app.log_exception(ex)
        print(ex)
        if ('REQUEST_CLIENT' in request.form
                and request.form['REQUEST_CLIENT'] == 'ITHRIV'):
            return make_response(jsonify(
                {
                    "status": "error",
                    "message":
                    "Error submitting general support request : {}".format(
                        str(ex))
                }
            ), 501)
        else:
            return redirect(
                ''.join([response_url, '&status=', 'error', '&', 'message=',
                         'Error submitting support '
                         'request: {}'.format(str(ex))]))


@app.route('/rest/<version>/get-all-customer-requests/', methods=['GET'])
def get_all_customer_requests(version='v2'):
    try:
        return make_response(
            jsonify(
                JiraServiceHandler(app, version != "v1").get_all_tickets_by_customer(
                    request.values.get('email'))))
    except Exception as ex:
        app.log_exception(ex)
        print(ex)
        return make_response(jsonify(
            {
                "status": "error",
                "message":
                "Error fetching customer requests : {}".format(
                    str(ex))
            }
        ), 501)


@app.route('/rest/<version>/hpc-allocation-request/', methods=['POST'])
@app.route('/rest/hpc-allocation-request/', methods=['POST'])
@limiter.limit("30 per hour")
@limiter.limit("10 per minute")
def hpc_allocation_request(version='v2'):
    try:
        f = furl.furl(request.referrer)
        f.remove(['ticket_id', 'message', 'status'])
        request_form = dict(request.form.items())
        request_form['category'] = "Rivanna HPC"

        response = json.loads(_process_support_request(
            request_form, request.host_url if 'localhost' in request.host_url else request.host_url.replace(
                'http', 'https'), version))

        return redirect(
            ''.join([f.url, '&status=', '200 OK', '&', 'message=',
                     'HPC Allocation request ({}) successfully '
                     'created'.format(response['issueKey'])]))
    except Exception as ex:
        app.log_exception(ex)
        print(ex)
        return redirect(
            ''.join([f.url, '&status=', 'error', '&', 'message=',
                     'Error submitting HPC Allocation '
                     'request: {}'.format(str(ex))]))


@app.route('/rest/<version>/confirm-hpc-allocation-request/<token>/', methods=['GET', 'POST'])
@app.route('/rest/confirm-hpc-allocation-request/<token>/', methods=['GET', 'POST'])
@limiter.limit("12 per hour")
@limiter.limit("4 per minute")
def confirm_hpc_allocation_request(token, version='v2'):
    try:
        for salt_str in ALLOC_APPROVE_CONFIRM_TYPES:
            sig_okay, ticket_id = URLSafeTimedSerializer(
                app.config["MAIL_SECRET_KEY"]
            ).loads_unsafe(token, salt=salt_str, max_age=1209600)
            if (sig_okay):
                if(salt_str == ALLOC_APPROVE_CONFIRM_TYPES[2] and request.environ['REQUEST_METHOD'] == 'GET'):
                    return render_template(
                        'confirm_explanation.html',
                        logo_url=RC_SMALL_LOGO_URL,
                        confirmation_str='{} confirmation form'.format(
                            salt_str),
                        confirm_approve_url=request.base_url if 'localhost' in request.base_url else request.base_url.replace(
                            'http', 'https'),
                        show_condition="visibility: show;",
                        confirm_str=salt_str,
                        default_sus='',
                    )
                if(salt_str == ALLOC_APPROVE_CONFIRM_TYPES[1] and request.environ['REQUEST_METHOD'] == 'GET'):
                    return render_template(
                        'confirm_explanation.html',
                        logo_url=RC_SMALL_LOGO_URL,
                        confirmation_str='{} confirmation form'.format(
                            salt_str),
                        confirm_approve_url=request.base_url if 'localhost' in request.base_url else request.base_url.replace(
                            'http', 'https'),
                        show_condition="visibility: hidden;",
                        confirm_str=salt_str,
                        default_sus=0,
                    )
                comment_list = [
                    'Confirmation received from sponsor: ', salt_str.upper()]
                if request.environ['REQUEST_METHOD'] == 'POST':
                    if salt_str == ALLOC_APPROVE_CONFIRM_TYPES[2]:
                        comment_list = comment_list + ['\n\nSUs approved by sponsor: ', request.form['su-request-approved-by-dean'],
                                                       '\n\nExplanation: ', request.form['deans-explanation']]
                    elif salt_str == ALLOC_APPROVE_CONFIRM_TYPES[1]:
                        comment_list = comment_list + \
                            ['\n\nExplanation: ', request.form['deans-explanation']]

                response = json.loads(JiraServiceHandler(
                    app, version != "v1").add_ticket_comment(ticket_id, ''.join(comment_list)))
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
        app.log_exception(ex)
        print(ex)
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
        app.log_exception(ex)
        print(ex)
        return make_response(jsonify(
            {
                "status": "error",
                "message":
                    "Error processing update_konami_discovery request : {}".format(
                        str(ex))
            }
        ))
