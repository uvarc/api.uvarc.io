# encoding=utf8
from app.api.jira_service_handler import JiraServiceHandler
from app.api import ALLOC_APPROVE_CONFIRM_TYPES, RC_SMALL_LOGO_URL, BII_COST_CENTERS, DS_COST_CENTERS, DecimalEncoder
from app import app, limiter, email_service, aws_service
from itsdangerous import URLSafeTimedSerializer
import furl
import yaml
from flask import json, jsonify, make_response, request, redirect, render_template
from boto3.dynamodb.conditions import Key, Attr
import sys
import requests
import datetime


def unauthorized():
    return make_response(jsonify(
        {"status": "error",
         "message": "unauthorized"}
    ), 401)


def fetch_form_identity_info(form_elements_dict):
        category = None
        allocation_type = None
        storage_choice = None
        app.logger.info("form_elements:{form_elements_dict}".format(form_elements_dict=form_elements_dict))
        if 'category' in form_elements_dict:
            category = form_elements_dict['category']
        if 'Allocation Type' in form_elements_dict:
            allocation_type = form_elements_dict['Allocation Type']
        if 'storage-choice' in form_elements_dict:
            storage_choice = form_elements_dict['storage-choice']
        return category, allocation_type, storage_choice


def update_dynamo_db_tables(ticket_response, form_elements_dict, desc_str, project_ticket_route):
    try:
        # app.logger.info("form_elements:{form_elements_dict}".format(form_elements_dict=form_elements_dict))
        # if 'category' in form_elements_dict:
        #     category = form_elements_dict['category']
        # if 'Allocation Type' in form_elements_dict:
        #     allocation_type = form_elements_dict['Allocation Type']
        # if 'storage-choice' in form_elements_dict:
        #     storage_choice = form_elements_dict['storage-choice']

        category, allocation_type, storage_choice = fetch_form_identity_info(form_elements_dict)

        if category is None:
            app.logger.warning("category not found in form_elements_dict")
            print("Error: 'category' not found in form_elements_dict.")
            return

        if category == 'Rivanna HPC':
            if allocation_type == "Purchase Service Units":
                table_name = app.config['PAID_SU_REQUESTS_INFO_TABLE']
                app.logger.info(f"table_name:{table_name}")
                update_paid_su_requests_info_table(ticket_response, form_elements_dict, desc_str, project_ticket_route, table_name)
            else:
                app.logger.info(f"Invalid allocation_type: {allocation_type}. No updates performed.")
        elif category == 'Storage':
            if storage_choice == 'Research Project':
                table_name = app.config['PROJECT_STORAGE_REQUEST_INFO_TABLE']
                app.logger.info(f"table_name:{table_name}")
                update_project_storage_request_info_table(ticket_response, form_elements_dict, desc_str, project_ticket_route, table_name)
            elif storage_choice == 'Research Standard':
                table_name = app.config['STANDARD_STORAGE_REQUEST_INFO_TABLE']
                app.logger.info(f"table_name:{table_name}")
                update_standard_storage_request_info_table(ticket_response, form_elements_dict, desc_str, project_ticket_route, table_name)
            else:
                app.logger.info(f"Invalid storage choice: {storage_choice}. No updates performed.")

        else:
            app.logger.info(f"Category '{category}' not recognized. No updates performed.")
    except Exception as e:
        app.log_exception(e)
        print("Details: {e}")


def update_paid_su_requests_info_table(ticket_response, form_elements_dict, desc_str, project_ticket_route, table_name):
    try:
        ticket_id = json.loads(ticket_response)['issueKey']
        today = datetime.date.today()
        formatted_date = today.strftime("%Y-%m-%d")
        fundingTypeData = updateFundingtype(form_elements_dict)
        table_data = {
                    'ticket_id': ticket_id,
                    'date': formatted_date,
                    'company': form_elements_dict.get('company-id', ''),
                    'business_unit': form_elements_dict.get('business-unit', ''),
                    'cost_center': form_elements_dict.get('cost-center', ''),
                    'fund': form_elements_dict.get('fund', ''),
                    'grant': fundingTypeData.get('grant', ''),
                    'gift': fundingTypeData.get('gift', ''),
                    'project': fundingTypeData.get('project', ''),
                    'designated': fundingTypeData.get('designated', ''),
                    'bill_amount': form_elements_dict.get('fdm-total', ''),
                    'program': form_elements_dict.get('program', ''),
                    'function': form_elements_dict.get('function', ''),
                    'activity': form_elements_dict.get('activity', ''),
                    'assignee': form_elements_dict.get('assignee', ''),
                    'owner_name': form_elements_dict.get('name', ''),
                    'owner_uid': form_elements_dict.get('uid', ''),
                    'allocation_name': form_elements_dict.get('Allocation Type', ''),
                    'financial-contact': form_elements_dict.get('financial-contact', ''),
                    'group_name': form_elements_dict.get('su-allocation', ''),
                    'project_name': project_ticket_route[0],
                    'descrition': desc_str
                }
        result = aws_service.insert_into_dynamodb(table_name, table_data)
    except Exception as e:
        app.log_exception(e)
        print("Details: {e}")


def update_project_storage_request_info_table(ticket_response, form_elements_dict, desc_str, project_ticket_route, table_name):
    try:
        ticket_id = json.loads(ticket_response)['issueKey']
        today = datetime.date.today()
        formatted_date = today.strftime("%Y-%m-%d")
        fundingTypeData = updateFundingtype(form_elements_dict)
        table_data = {
                    'ticket_id': ticket_id,
                    'date': formatted_date,
                    'company': form_elements_dict.get('company-id', ''),
                    'business_unit': form_elements_dict.get('business-unit', ''),
                    'cost_center': form_elements_dict.get('cost-center', ''),
                    'fund': form_elements_dict.get('fund', ''),
                    'grant': fundingTypeData.get('grant', ''),
                    'gift': fundingTypeData.get('gift', ''),
                    'project': fundingTypeData.get('project', ''),
                    'designated': fundingTypeData.get('designated', ''), 
                    'bill_amount': form_elements_dict.get('fdm-total', ''),
                    'program': form_elements_dict.get('program', ''),
                    'function': form_elements_dict.get('function', ''),
                    'activity': form_elements_dict.get('activity', ''),
                    'assignee': form_elements_dict.get('assignee', ''),
                    'owner_name': form_elements_dict.get('name', ''),
                    'owner_uid': form_elements_dict.get('uid', ''),
                    'allocation_name': form_elements_dict.get('Allocation Type', ''),
                    'financial-contact': form_elements_dict.get('financial-contact', ''),
                    'group_name': form_elements_dict.get('mygroup-ownership', ''),
                    'project_name': project_ticket_route[0],
                    'descrition': desc_str
                }
        result = aws_service.insert_into_dynamodb(table_name, table_data)
    except Exception as e:
        app.log_exception(e)
        print("Details: {e}")


def update_standard_storage_request_info_table(ticket_response, form_elements_dict, desc_str, project_ticket_route, table_name):
    try:
        ticket_id = json.loads(ticket_response)['issueKey']
        today = datetime.date.today()
        formatted_date = today.strftime("%Y-%m-%d")
        fundingTypeData = updateFundingtype(form_elements_dict)
        table_data = {
                    'ticket_id': ticket_id,
                    'date': formatted_date,
                    'company': form_elements_dict.get('company-id', ''),
                    'business_unit': form_elements_dict.get('business-unit', ''),
                    'cost_center': form_elements_dict.get('cost-center', ''),
                    'fund': form_elements_dict.get('fund', ''),
                    'grant': fundingTypeData.get('grant', ''),
                    'gift': fundingTypeData.get('gift', ''),
                    'project': fundingTypeData.get('project', ''),
                    'designated': fundingTypeData.get('designated', ''),
                    'bill_amount': form_elements_dict.get('fdm-total', ''),
                    'program': form_elements_dict.get('program', ''),
                    'function': form_elements_dict.get('function', ''),
                    'activity': form_elements_dict.get('activity', ''),
                    'assignee': form_elements_dict.get('assignee', ''),
                    'owner_name': form_elements_dict.get('name', ''),
                    'owner_uid': form_elements_dict.get('uid', ''),
                    'allocation_name': form_elements_dict.get('Allocation Type', ''),
                    'financial-contact': form_elements_dict.get('financial-contact', ''),
                    'group_name': form_elements_dict.get('mygroup-ownership', ''),
                    'project_name': project_ticket_route[0],
                    'descrition': desc_str
                }
        result = aws_service.insert_into_dynamodb(table_name, table_data)
    except Exception as e:
        app.log_exception(e)
        print("Details: {e}")


def updateFundingtype(form_elements_dict):
    funding_type = form_elements_dict.get('funding-type', '')
    funding_number = form_elements_dict.get('funding-number', '')
    funding_data = {
        'project': '',
        'gift': '',
        'grant': '',
        'designated': ''
    }
    if funding_type == 'Project':
        funding_data['project'] = funding_number
    elif funding_type == 'Gift':
        funding_data['gift'] = funding_number
    elif funding_type == 'Grant':
        funding_data['grant'] = funding_number
    elif funding_type == 'Designated':
        funding_data['designated'] = funding_number
    return funding_data


def validationForBillingInfo(form_elements_dict):
    category, allocation_type, storage_choice = fetch_form_identity_info(form_elements_dict)
    if (category == 'Rivanna HPC' and allocation_type == "Purchase Service Units") or (category == 'Storage' and storage_choice in ['Research Standard','Research Project']):
        fundingTypeData = updateFundingtype(form_elements_dict)
        billing_data = {
            'company': form_elements_dict.get('company-id', ''),
            'cost_center': form_elements_dict.get('cost-center', ''),
            'business_unit': form_elements_dict.get('business-unit', ''),
            'fund': form_elements_dict.get('fund', ''),
            'grant': fundingTypeData.get('grant', ''),
            'gift': fundingTypeData.get('gift', ''),
            'project': fundingTypeData.get('project', ''),
            'designated': fundingTypeData.get('designated', ''),
            'function': form_elements_dict.get('function', ''),
            'program': form_elements_dict.get('program', ''),
            'activity': form_elements_dict.get('activity', ''),
            'assignee': form_elements_dict.get('assignee', '')
        }
        api_url = "https://uvarc-unified-service.hpc.virginia.edu/uvarc/api/resource/rcwebform/fdm/verify"
        headers = {"Content-Type": "application/json", 'Origin': 'https://uvarc-api.pods.uvarc.io'}
        try:
            app.logger.info("starting to validation API")
            payload = json.dumps(billing_data)
            app.logger.info(payload)
            response = requests.post(api_url, headers=headers, data=payload)
            # app.logger.info("response:", response)
            response_dict = eval(json.loads(response.text)[0])
            if response_dict.get("Valid") == "true":
                print("Billing validation successful.")
            else:
                error_message = response_dict.get("ErrorText")
                raise ValueError(f"Billing validation failed: {error_message}")

        except Exception as ex:
            app.log_exception(ex)
            print(ex)
            raise ex


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
    discipline = ''
    discipline_other = ''
    cost_center = ''
    format_attribs_order = ['name', 'email', 'uid',
                            'department', 'school', 'discipline', 'discipline-other', 'category', 'description', 'cost-center']
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
                if attrib == 'discipline':
                    discipline = value
                if attrib == 'discipline-other':
                    discipline_other = value
                if attrib == 'cost-center':
                    cost_center = value
            if attrib != 'department' and attrib != 'school' and attrib != 'discipline' and attrib != 'discipline-other' :
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

    # ret = jira_service_handler.create_new_customer(
    #             name='SDS RC',
    #             email='SDS_RC@virginia.edu',
    #         )
    response = validationForBillingInfo(form_elements_dict)
     
    if (name is not None and name != '' and email is not None and email != ''):
        try:
            jira_service_handler.create_new_customer(
                name=name,
                email=email,
            )            
        except Exception as ex:
            app.log_exception(ex)
            print(ex)
    participants = None
    if department.lower().startswith('ds-') or 'data science' in department.lower() or 'data science' in discipline.lower():
        participants = app.config['STORAGE_SPONSOR_EMAIL_LOOKUP']['DS']
    elif category == 'Storage':
        if cost_center in BII_COST_CENTERS and ((not department.lower().startswith('ds-')) and 'data science' not in department.lower()):
            participants = app.config['STORAGE_SPONSOR_EMAIL_LOOKUP']['BII']

    # ticket_response = '{"issueKey":"RIV-1082"}'
    ticket_response = jira_service_handler.create_new_ticket(
        reporter=email if '@' not in email else email.split('@')[0],
        participants=participants,
        project_name=project_ticket_route[0],
        request_type=project_ticket_route[1],
        components=components,
        summary=summary_str,
        desc=desc_str,
        department=department,
        school=school,
        discipline=discipline if discipline != 'other' else discipline_other,
        is_rc_project=is_rc_project
    )

    app.logger.info(ticket_response)
    print('Ticket Response: ' + str(ticket_response))
    
    aws_service.update_dynamodb_jira_tracking(
        json.loads(ticket_response)['issueKey'],
        json.loads(ticket_response)['createdDate']['jira'],
        username,
        email,
        summary_str
    )

    try:
        update_dynamo_db_tables(ticket_response, form_elements_dict, desc_str, project_ticket_route)
    except Exception as e:
        # Log and handle any unexpected errors
        app.log_exception(e)
        print(f"Error: An error occurred. Details: {e}")

    if category == 'Deans Allocation':
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
    elif category == 'Storage':
        if cost_center in BII_COST_CENTERS and department.lower() != 'ds-data science':
            customer = json.loads(jira_service_handler.get_customer(app.config['STORAGE_SPONSOR_EMAIL_LOOKUP']['BII'][0]))
            if 'emailAddress' in customer:
                to_email_address = customer['emailAddress']
                email_service.send_storage_request_confirm_email(
                    from_email_address=form_elements_dict['email'],
                    to_email_address=to_email_address,
                    subject=summary_str,
                    ticket_id=json.loads(ticket_response)['issueKey'],
                    callback_host=service_host,
                    content_dict=form_elements_dict
                )
            else:
                raise Exception(customer)

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
    response_url = "http://localhost:1313/thank-you/?" if 'localhost' in request.host_url else "https://www.rc.virginia.edu/thank-you/?"
    try:
        f = furl.furl(request.referrer)
        f.remove(['ticket_id', 'message', 'status'])
        response = json.loads(_process_support_request(
            request.form, request.host_url, version))
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


@app.route('/rest/get_items/', methods=['GET'])
def get_items():
    try:
        table_name = request.args.get('tableName')
        date_str = request.args.get('date_str')
        result = aws_service.get_items_from_dynamodb_by_date(table_name, date_str)
        return jsonify(result)
    except Exception as ex:
        app.log_exception(ex)
        print(ex)


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

        print("Testing: "+str(request.host_url))
        response = json.loads(_process_support_request(
            request_form, request.host_url, version))

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


@app.route('/rest/<version>/confirm-storage-request/<token>/', methods=['GET', 'POST'])
@app.route('/rest/confirm-storage-request/<token>/', methods=['GET', 'POST'])
@limiter.limit("12 per hour")
@limiter.limit("4 per minute")
def confirm_storage_request(token, version='v2'):
    try:
        for salt_str in ALLOC_APPROVE_CONFIRM_TYPES:
            sig_okay, ticket_id = URLSafeTimedSerializer(
                app.config["MAIL_SECRET_KEY"]
            ).loads_unsafe(token, salt=salt_str, max_age=1209600)
            if (sig_okay):
                if(salt_str == ALLOC_APPROVE_CONFIRM_TYPES[2] and request.environ['REQUEST_METHOD'] == 'GET'):
                    return render_template(
                        'confirm_explanation_storage.html',
                        logo_url=RC_SMALL_LOGO_URL,
                        confirmation_str='{} confirmation form'.format(
                            salt_str),
                        confirm_approve_url=request.base_url if 'localhost' in request.base_url else request.base_url.replace(
                            'http', 'https'),
                        show_condition="visibility: show;",
                        confirm_str=salt_str,
                        default_storage='',
                    )
                if(salt_str == ALLOC_APPROVE_CONFIRM_TYPES[1] and request.environ['REQUEST_METHOD'] == 'GET'):
                    return render_template(
                        'confirm_explanation_storage.html',
                        logo_url=RC_SMALL_LOGO_URL,
                        confirmation_str='{} confirmation form'.format(
                            salt_str),
                        confirm_approve_url=request.base_url if 'localhost' in request.base_url else request.base_url.replace(
                            'http', 'https'),
                        show_condition="visibility: hidden;",
                        confirm_str=salt_str,
                        default_storage=0,
                    )
                comment_list = [
                    'Confirmation received from sponsor: ', salt_str.upper()]
                if request.environ['REQUEST_METHOD'] == 'POST':
                    if salt_str == ALLOC_APPROVE_CONFIRM_TYPES[2]:
                        comment_list = comment_list + ['\n\nStorage approved by sponsor: ', request.form['storage-request-approved-by-dean'],
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
                    'confirm_response_storage.html',
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
            'confirm_response_storage.html',
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


def sort_list(items):
    return items['partition']


def sort_system(items):
    return items['sort']

# def unauthorized():
#     return make_response(jsonify(
#       {"status": "error",
#       "message": "unauthorized"}
#     ), 401)


@app.route('/', methods=['GET'])
def index():
    return make_response(jsonify(
      {'status': '200 OK',
      'message': 'Please make a resource request. Options are /status/rivanna or /status/available'}
    ), 200)


@app.route('/hhc', methods=['POST'])
def hhc():
    return make_response(jsonify(
        {
            'status': '200 OK',
            'response_type': 'in_channel',
            'text': 'hey remind users about UVA HHC',
            'request': 'data'
        }
    ), 200)


@app.route('/status', methods=['GET'])
def status():
    return make_response(jsonify(
        {
            'status': '200 OK',
            'command': 'this is so easy' 
        }
    ), 200)


@app.route('/status/rivanna', methods=['GET'])
def rivanna_status():
    table = aws_service.get_dynamodb_resource().Table('rivannaq')
    queue = []
    std = table.scan()
    for i in std[u'Items']:
        queue.append(i)
    # queue.sort(key=sort_list, reverse=True)
    queue.sort(key=sort_system)
    return make_response(jsonify(queue), 200)


@app.route('/badge/<system>', methods=['GET'])
def badge_status(system):
    table = aws_service.get_dynamodb_resource().Table('status')
    state = []
    stat = table.scan()
    for j in stat[u'Items']:
        state.append(j)
    state.sort(key=sort_system)
    return make_response(jsonify(state), 200)


@app.route('/status/available', methods=['GET','POST'])
def available_status():
    table = aws_service.get_dynamodb_resource().Table('status')

    master_token = 'ftxBBFb3XqQDDzPNIzBlR9VZ'
    if request.method == 'GET':
        state = []
        stat = table.scan()
        for j in stat[u'Items']:
            state.append(j)
        state.sort(key=sort_system)
        return make_response(jsonify(state), 200)
    if request.method == 'POST':
        reqt = request.json
        s_token = reqt['token']
        if (s_token != master_token):
            return make_response(jsonify(
                {
                    'reply': '403 Forbidden: Invalid Token',
                    'status': 'disallowed'
                }
            ), 403)
            sys.exit(1)
        s_system = reqt['system']
        s_state = reqt['state']
        s_message = ""
        s_color = ""
        s_image = '/images/status/green.png'
        if (s_state == 0):
            s_image = '/images/status/green.png'
            s_message = 'No issues'
            s_color = '5cb85c'
        elif (s_state == 1):
            s_image = '/images/status/yellow.png'
            s_message = 'Incident'
            s_color = 'ffff00'
        elif (s_state == 2):
            s_image = '/images/status/red.png'
            s_message = 'Outage'
            s_color = 'red'
        elif (s_state == 3):
            s_image = '/images/status/blue.png'
            s_message = 'Maintenance'
            s_color = 'blue'
        response = table.update_item(
            Key={'system': s_system},
            UpdateExpression="set statez = :r, image = :i, message = :m, color = :c",
            ExpressionAttributeValues={
                ':r': s_state,
                ':i': s_image,
                ':m': s_message,
                ':c': s_color
            },
        )
        # resp_code = response.ResponseMetadata.HTTPStatusCode
        return make_response(jsonify(
                {
                    'reply': '200 OK. Status Updated',
                    'system': s_system,
                    'image': s_image,
                    'status': s_state
                }
            ), 200)


# Update standard rc.virginia.edu website status
@app.route('/status/messages', methods=['GET','POST'])
def status_messages():
    table = aws_service.get_dynamodb_resource().Table('status-messages')
    master_token = 'ftxBBFb3XqQDDzPNIzBlR9VZ'
    if request.method == 'GET':
        messages = []
        msgs = table.scan()
        for j in msgs[u'Items']:
            messages.append(j)
        return make_response(jsonify(messages), 200)
    if request.method == 'POST':
        reqt = request.json
        s_token = reqt['token']
        if (s_token != master_token):
            return make_response(jsonify(
                {
                    'reply': '403 Forbidden: Invalid Token',
                    'status': 'disallowed' 
                }
            ), 403)
            sys.exit(1)
        s_message = "message"
        s_body = reqt['body']
        now = datetime.datetime.now()
        rightnow = now.strftime("%Y-%m-%d %H:%M:%S")
        body = rightnow + ' ' + s_body
        response = table.update_item(
            Key={'message': s_message},
            UpdateExpression="set body = :b",
            ExpressionAttributeValues={
                ':b': body,
            },
        )
        return make_response(jsonify(
            {
                'reply': '200 OK. Status Updated',
                'method': "update-message",
                'body': s_body
            }
        ), 200)


# Update ACCORD status on accord.uvarc.io
@app.route('/accord/messages', methods=['GET','POST'])
def accord_messages():
    table = aws_service.get_dynamodb_resource().Table('accord-messages')
    master_token = 'ftxBBFb3XqQDDzPNIzBlR9VZ'
    if request.method == 'GET':
        messages = []
        msgs = table.scan()
        for j in msgs[u'Items']:
            messages.append(j)
        return make_response(jsonify(messages), 200)
    if request.method == 'POST':
        reqt = request.json
        s_token = reqt['token']
        if (s_token != master_token):
            return make_response(jsonify(
                {
                    'reply': '403 Forbidden: Invalid Token',
                    'status': 'disallowed'
                }
            ), 403)
            sys.exit(1)
        s_message = "message"
        s_body = reqt['body']
        now = datetime.datetime.now()
        rightnow = now.strftime("%Y-%m-%d %H:%M:%S")
        body = rightnow + ' ' + s_body
        response = table.update_item(
            Key={'message': s_message},
            UpdateExpression="set body = :b",
            ExpressionAttributeValues={
                ':b': body,
            },
        )
        return make_response(jsonify(
            {
                'reply': '200 OK. Status Updated',
                'method': "update-message",
                'body': s_body
            }
        ), 200)


@app.route('/dbs', methods=['POST'])
def manage_dbs():
    # table = dynamodb.Table('dbservices')
    master_token = 'ftxBBFb3XqQDDzPNIzBlR9VZ'
    if request.method == 'POST':
        reqt = request.form
        text = request.form['text']
        user = request.form['user_name']
        response_url = request.form['response_url']
        message = {"text": "Got your request!"}
        reply = requests.post(response_url, data=message, headers={"Content-type": "application/json"})
        # reqt = request.json
        # s_token = reqt['token']
        # if (s_token != master_token):
        #   return make_response(jsonify(
        #     {'reply': '403 Forbidden: Invalid Token',
        #      'status': 'disallowed' }
        #   ), 403)
        #   sys.exit(1)
        # s_message = "message"
        # s_body = reqt['body']
        # now = datetime.datetime.now()
        # rightnow = now.strftime("%Y-%m-%d %H:%M:%S")
        # body = rightnow + ' ' + s_body
        # response = table.update_item(
        #   Key={'message': s_message},
        #   UpdateExpression="set body = :b",
        #   ExpressionAttributeValues={
        #     ':b': body,
        #   },
        #  )
        print(reqt)
        return make_response(jsonify(
            {
                'reply': '200 OK',
                'text': text, 'user': user,
                'response_url': response_url 
            }
        ), 200)

    """
    team_domain = reqt['team_domain']
    user_name = reqt['user_name']
    command = reqt['command']
    text = reqt['text']
    response_url = reqt['response_url']

    'token': token,
    'team_domain': team_domain,
    'user_name': user_name,
    'command': command,
    'text': text,
    'response_url': response_url }
    token=ftxBBFb3XqQDDzPNIzBlR9VZ
    team_id=T0001
    team_domain=example
    channel_id=C2147483705
    channel_name=test
    user_id=U2147483697
    user_name=Steve
    command=/weather
    text=94070
    response_url=https://hooks.slack.com/commands/1234/5678
    """


@app.route('/status/full', methods=['GET'])
def full_status():
    table = aws_service.get_dynamodb_resource().Table('status')
    status = []
    riv = Key('system').eq('rivanna')
    ivy = Key('system').eq('ivy')
    sky = Key('system').eq('skyline')
    dco = Key('system').eq('dcos')
    val = Key('system').eq('value')
    pro = Key('system').eq('project')
    glo = Key('system').eq('globus')
    stat = table.scan(FilterExpression=riv)
    for j in stat[u'Items']:
        status.append({"system": "rivanna", "statez": j['statez']})
    # status.sort(key=sort_system)
    return make_response(jsonify(status), 200)


@app.route('/support', methods=['POST'])
def support():
    return make_response(jsonify(
        {
            'status': '200 OK',
            'message': 'make a resource request'
        }
    ), 200)
