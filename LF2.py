"""
polls the SQS, gets the message from SQS and sends a 
random restaurant using the information to SNS which 
sends the email
"""
import json
import boto3
from aws_requests_auth.aws_auth import AWSRequestsAuth
import requests
# from keys import *

TABLENAME = 'YelpRestaurants'
ELASTIC_SEARCH_URL = "ADD ELASTIC SEARCH URL HERE"

session = boto3.session.Session()
credentials = session.get_credentials().get_frozen_credentials()
es_host = 'ADD es_host here'
awsauth = AWSRequestsAuth(
    aws_access_key=credentials.access_key,
    aws_secret_access_key=credentials.secret_key,
    aws_token=credentials.token,
    aws_host=es_host,
    aws_region=session.region_name,
    aws_service='es'
)


def get_sns_client():
    client = boto3.client('sns')
    return client


def send_sns_message(message, client, phone_number="DEFAULT PHONE NUMBER HERE"):
    """
    sends a message to a phone number
    message: string
    client: boto3 client for sns
    phone_number: should be E.164 format as shown in default
    """
    if not phone_number.startswith('+'):
        phone_number = '+1'+phone_number
    client.publish(Message=message, PhoneNumber=phone_number)


def get_restaurant_ids(URL, cuisine):
    """
    return the restaurant ids having the 
    same cuisine as desired 
    """
    URL = URL + str(cuisine)
    response = requests.get(URL, auth=awsauth).content
    data = json.loads(response)
    hits = data["hits"]["hits"]
    id_list = []
    for result in hits:
        _id = result["_source"]["id"]
        id_list.append(_id)
    return id_list


def retrieve_from_dynamodb(ids, table_name):
    """
    Given a list of ids, retrieve the restuarant information of those ids
    """
    resource = boto3.resource('dynamodb')
    table = resource.Table(table_name)
    restuarnt_information = []
    for _id in ids:
        response = table.get_item(Key={'id': str(_id)})
        if 'Item' in response:
            restuarnt_information.append(response['Item'])
    return restuarnt_information


def lambda_handler(event, context):

    def get_message(restaurant_information):
        message = ''
        for i, restuarnt in enumerate(restaurant_information[:3]):
            d = dict(restuarnt)
            address = d['address1']
            name = d['name']
            message = message + f' {i+1}. {name}, located at {address}'
        message = message + '.'
        return message

    sns = get_sns_client()

    for record in event['Records']:
        body = json.loads(record['body'])
        phone_number = body['PhoneNumber']
        cuisine = body['Food']
        number_of_people = body['NumberOfPeople']
        time = body['Time']

        message = f'Hello! Here are my {cuisine} restaurant suggestions for {number_of_people}, for today at {time}.'
        # get the ids of the restaurant
        ids = get_restaurant_ids(ELASTIC_SEARCH_URL, cuisine)
        restaurant_information = retrieve_from_dynamodb(ids, TABLENAME)
        message = message + get_message(restaurant_information)

        send_sns_message(message, sns, phone_number)
