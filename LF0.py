"""
Note: we need access to CloudWatch and Amazon Lex service for this
lambda function. To do that go to IAM > Create a role > add 
"CloudWatchFullAccess" and "AmazonLexFullAcess" to create a role.
Attach this role to this lambda function.

Note: Don't use Lambda Proxy integration while attaching lambda to API gateway
"""
import json
import boto3
import datetime


AMAZON_LEX_BOT = "RestaurantBot"
LEX_BOT_ALIAS = "testLF"
USER_ID = "test"
# used by the lex to specify which user is it communicating with


def post_on_lex(input_text="Hi", user_id=USER_ID):
    """
    Get the user input from the frontend as text and pass
    it to lex. Lex will generate a new response.

    it will return a json response: 
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lex-runtime.html
    """
    client = boto3.client('lex-runtime')
    lex_response = client.post_text(botName=AMAZON_LEX_BOT,
                                    botAlias=LEX_BOT_ALIAS,
                                    userId=user_id, inputText=input_text)
    message = lex_response['message']
    return message, user_id


def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def lambda_handler(event, context):
    '''Demonstrates a simple HTTP endpoint using API Gateway. You have full
    access to the request and response payload, including headers and
    status code.

    To scan a DynamoDB table, make a GET request with the TableName as a
    query string parameter. To put, update, or delete an item, make a POST,
    PUT, or DELETE request respectively, passing in the payload to the
    DynamoDB API as a JSON body.
    '''
    messages = event['messages']
    assert len(messages) == 1
    message = messages[0]
    user_id = message['unstructured']['id']
    text = message['unstructured']['text']
    # time = message['unstructured']['time']
    response_text, user_id = post_on_lex(str(text), str(user_id))
    time = datetime.datetime.now().isoformat()
    response = {"messages": [{"type": "message", "unstructured": {
        "id": str(user_id), "text": str(response_text), "timestamp": str(time)}}]}
    return response
