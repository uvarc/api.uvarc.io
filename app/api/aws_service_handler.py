import datetime
import boto3
import json
from app.api import DecimalEncoder


class AWSServiceHandler:
    def __init__(self, app):
        self.app = app
        self.aws_access_key_id = app.config['AWS_CONN_INFO']['CLIENT_ID']
        self.aws_secret_access_key = app.config['AWS_CONN_INFO']['CLIENT_SECRET']

    def get_dynamodb_resource(self):
        try:
            return boto3.Session(
                aws_access_key_id=self.aws_access_key_id, 
                aws_secret_access_key=self.aws_secret_access_key, 
                region_name='us-east-1'
            ).resource('dynamodb')
        except Exception as ex:
            self.app.log_exception(ex)
            print(str(ex))
            raise ex

    def update_dynamodb_jira_tracking(self, jira_issue_key, create_date, username, email, desc):
        try:
            dynamodb_session = boto3.Session(
                aws_access_key_id=self.aws_access_key_id, 
                aws_secret_access_key=self.aws_secret_access_key, 
                region_name='us-east-1'
            )
            dynamodb = dynamodb_session.resource('dynamodb')
            table = dynamodb.Table('jira-tracking')

            response = table.put_item(
                Item={
                    'key': jira_issue_key,
                    'submitted': create_date,
                    'uid': username,
                    'email': email,
                    'type': desc
                }
            )
            self.app.logger.info(json.dumps(response, indent=4, cls=DecimalEncoder))
            print(json.dumps(response, indent=4, cls=DecimalEncoder))
        except Exception as ex:
            self.app.log_exception(ex)
            print(str(ex))

    def insert_into_dynamodb(self, tableName, data):
        try:
            dynamodb_session = boto3.Session(
                aws_access_key_id=self.aws_access_key_id, 
                aws_secret_access_key=self.aws_secret_access_key, 
                region_name='us-east-1'
            )
            dynamodb = dynamodb_session.resource('dynamodb')
            table = dynamodb.Table(tableName)

            response = table.put_item(Item=data) 
            print("Item inserted successfully: {response}")
            self.app.logger.info(json.dumps(response, indent=4, cls=DecimalEncoder))
            print(json.dumps(response, indent=4, cls=DecimalEncoder))
        except Exception as ex:
            self.app.log_exception(ex)
            print(str(ex))
            
    def get_item_from_dynamodb(self, tableName, ticket_id):
        try:
            dynamodb_session = boto3.Session(
                aws_access_key_id=self.aws_access_key_id, 
                aws_secret_access_key=self.aws_secret_access_key, 
                region_name='us-east-1'
            )

            dynamodb = dynamodb_session.resource('dynamodb')
            table = dynamodb.Table(tableName)

            response = table.get_item(Key={'ticket_id': ticket_id})

            if 'Item' in response:
                print(f"Item retrieved successfully: {json.dumps(response['Item'], indent=4)}")
                self.app.logger.info(json.dumps(response['Item'], indent=4))
                return response['Item']
            else:
                print(f"No item found with ticket_id: {ticket_id}")
                self.app.logger.warning(f"No item found with ticket_id: {ticket_id}")
                return None
        except Exception as ex:
            self.app.log_exception(ex)
            print(f"An error occurred: {ex}")
            return None

    def get_items_from_dynamodb_by_date(self, tableName, date_str):
        try:
            dynamodb_session = boto3.Session(
                aws_access_key_id=self.aws_access_key_id, 
                aws_secret_access_key=self.aws_secret_access_key, 
                region_name='us-east-1'
            )

            # Initialize DynamoDB resource
            dynamodb = dynamodb_session.resource('dynamodb')
            table = dynamodb.Table(tableName)

            try:
                target_date = datetime.datetime.strptime(date_str, '%Y-%m')
            except ValueError:
                print(f"Invalid date format: {date_str}. Expected format: 'YYYY-MM'.")
                return None

            formatted_date = target_date.strftime('%Y-%m')

            response = table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('date').begins_with(formatted_date))

            if 'Items' in response and response['Items']:
                print(f"Items retrieved successfully: {json.dumps(response['Items'], indent=4)}")
                self.app.logger.info(json.dumps(response['Items'], indent=4))
                return response['Items']
            else:
                print(f"No items found before the date: {formatted_date}")
                self.app.logger.warning(f"No items found before the date: {formatted_date}")
                return []

        except Exception as ex:
            self.app.log_exception(ex)
            print(f"An error occurred: {ex}")
            return []
