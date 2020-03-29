"""
python 3.6
This sample demonstrates an implementation of the Lex Code Hook Interface
in order to serve a sample bot which manages reservations for hotel rooms and car rentals.
Bot, Intent, and Slot models which are compatible with this sample can be found in the Lex Console
as part of the 'BookTrip' template.

For instructions on how to set up and test this bot, as well as additional samples,
visit the Lex Getting Started documentation http://docs.aws.amazon.com/lex/latest/dg/getting-started.html.
"""
import boto3
import json
import datetime
import time
import os
import dateutil.parser
import logging


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
SQS = boto3.client("sqs")
QUEUE_URL = 'ADD SQS QUEUE URL HERE'


def getQueueURL():
    """Retrieve the URL for the configured queue name"""
    q = SQS.get_queue_url(QueueName='RestaurantRequest').get(QUEUE_URL)
    logger.debug("Queue URL is %s", QUEUE_URL)
    return q


def record(data):
    """The lambda handler"""
    logger.debug("Recording with data %s", data)
    try:
        logger.debug("Recording %s", data)
        u = getQueueURL()
        logging.debug("Got queue URL %s", u)
        resp = SQS.send_message(QueueUrl=QUEUE_URL, MessageBody=data)
        logger.debug("Send result: %s", resp)
    except Exception as e:
        raise Exception("Could not record link! %s" % e)

# --- Helpers that build all of the responses ---


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def confirm_intent(session_attributes, intent_name, slots, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': intent_name,
            'slots': slots,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


# --- Helper Functions ---


def safe_int(n):
    """
    Safely convert n value to int.
    """
    if n is not None:
        return int(n)
    return n


def try_ex(func):
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary.

    Note that this function would have negative impact on performance.
    """

    try:
        return func()
    except KeyError:
        return None


""" --- Functions that control the bot's behavior --- """


def book_restaurant(intent_request):
    """
    Performs dialog management and fulfillment for booking a restaurant.

    Beyond fulfillment, the implementation for this intent demonstrates the following:
    1) Use of elicitSlot in slot validation and re-prompting
    2) Use of sessionAttributes to pass information that can be used to guide conversation
    """

    location = try_ex(
        lambda: intent_request['currentIntent']['slots']['Location'])
    food = try_ex(lambda: intent_request['currentIntent']['slots']['Food'])
    num_people = try_ex(
        lambda: intent_request['currentIntent']['slots']['NumberOfPeople'])
    time = try_ex(lambda: intent_request['currentIntent']['slots']['Time'])
    phone = try_ex(
        lambda: intent_request['currentIntent']['slots']['PhoneNumber'])

    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {
    }

    # Load confirmation history and track the current reservation.
    reservation = json.dumps({
        'PhoneNumber': phone,
        'Location': location,
        'Food': food,
        'NumberOfPeople': num_people,
        'Time': time
    })

    session_attributes['currentReservation'] = reservation

    # Booking the hotel.  In a real application, this would likely involve a call to a backend service.
    logger.debug('book_restaurant under={}'.format(reservation))
    record(reservation)

    try_ex(lambda: session_attributes.pop('currentReservationPrice'))
    try_ex(lambda: session_attributes.pop('currentReservation'))
    session_attributes['lastConfirmedReservation'] = reservation

    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'Thanks, we are processing your requests.'
        }
    )


# --- Intents ---


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(
        intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningSuggestionsIntent':
        return book_restaurant(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


# --- Main handler ---


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
