import json
import uuid
from botocore import exceptions
from authenticate.validate_response import func_resp, api_resp
from config.config import DYNAMODB_EXTRA_COSTINGS_TABLE
from databases.dbs import connect_to_dynamodb_resource
from boto3.dynamodb.conditions import Key, Attr, And


def get_all_extra_costings(headers):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_EXTRA_COSTINGS_TABLE)
    res = table.scan()
    if res.get('Items') is not None and len(res['Items']) > 0:
        return func_resp(msg='', data=res['Items'], status=200)
    else:
        return func_resp(msg='', data=[], status=200)


def get_costing_by_id(headers, extra_costing_id):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_EXTRA_COSTINGS_TABLE)
    try:
        response = table.get_item(
            Key={'extra_costing_id': extra_costing_id})

        if response.get('Item') is None:
            return func_resp(msg="costing not found.", data=[], status=404)
        else:
            return func_resp(msg="costing data returned.", data=response['Item'], status=200)
    except:
        data = json.dumps({
            "extra_costing_id": extra_costing_id
        })
        print(f"Error: Failed to retrieve costing with data: {data}.")
        return func_resp(msg="Failed to retrieve costing.", data=[], status=400)


def get_costing_by_type(headers, translation_id):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_EXTRA_COSTINGS_TABLE)
    if translation_id is not None:
        resp = table.scan(FilterExpression=Attr('translation_id').eq(translation_id))
    else:
        resp = table.scan()
    results = resp['Items']
    if results is not None and len(results) > 0:
        return func_resp(msg='', data=results, status=200)
    else:
        return func_resp(msg='', data=[], status=200)


def register_new_costing(extra_costings):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_EXTRA_COSTINGS_TABLE)
    extra_costing_id = uuid.uuid4()
    item = {'extra_costing_id': str(extra_costing_id)}
    for key, value in extra_costings.items():
        item[key] = value
    # print(f"Item: {item}")
    try:
        table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(extra_costing_id)'
        )
        return func_resp(msg="Costing Registered", data=[], status=200)
    except exceptions.ParamValidationError as error:
        print('The parameters you provided are incorrect: {}'.format(error))
        return func_resp(msg="Registration not completed.", data=[], status=400)
    except:
        return func_resp(msg="Registration not completed.", data=[], status=400)


def update_costing(extra_costing_id, extra_costings):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_EXTRA_COSTINGS_TABLE)
    item = {'extra_costing_id': str(extra_costing_id)}
    for key, value in extra_costings.items():
        item[key] = value
    try:
        table.put_item(
            Item=item,
            ConditionExpression='attribute_exists(extra_costing_id)'
        )
        return func_resp(msg="costing updated.", data=[], status=200)

    except exceptions.ClientError as e:
        print(f"Failed to update costing with error: {str(e.response.get('Error'))}")
        msg = e.response.get('Error', {"Message": None}).get('Message')
        if msg is None:
            msg = "Failed to update costing."
        else:
            msg = "extra_costing_id does not exist"
        return func_resp(msg=msg, data=[], status=400)

    except:
        data = json.dumps(item)
        print(f"Error: Failed to update costing with data: {data}.")
        return func_resp(msg="Failed to update costing.", data=[], status=400)


def delete_costing(extra_costing_id):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    try:
        table = client.Table(DYNAMODB_EXTRA_COSTINGS_TABLE)
        response = table.delete_item(
            Key={
                'extra_costing_id': extra_costing_id
            }
        )
        status_code = response['ResponseMetadata']['HTTPStatusCode']
        if status_code == 200:
            return func_resp(msg='costing Deleted.', data=[], status=200)
        else:
            return func_resp(msg=response['ResponseMetadata'], data=[], status=status_code)
    except:
        return func_resp(msg='Deletion Failed.', data=[], status=400)


# @token_required
def check_request_post(headers, body):
    if body is None:
        return func_resp(msg="Please complete all required fields.", data=[], status=400)

    try:
        body = json.loads(body)
    except:
        return func_resp(msg="Request body is not valid json", data=[], status=400)

    if not body or body is None:
        return func_resp(msg="Nothing send for insert.", data=[], status=400)

    # if not body.get("type"):
    #     return func_resp(msg="Please complete all required fields.", data=[], status=400)

    return func_resp(msg='', data=[], status=200)


# @token_required
def check_request_delete(headers, extra_costing_id):
    if extra_costing_id is None or extra_costing_id == "":
        return func_resp(msg="extra_costing_id was not given.", data=[], status=400)
    return func_resp(msg="", data=[], status=200)


# @token_required
def check_request_put(headers, extra_costing_id, body):
    if body is None:
        return func_resp(msg="Please complete all required fields.", data=[], status=400)

    if extra_costing_id is None or extra_costing_id == "":
        return func_resp(msg="extra_costing_id was not given.", data=[], status=400)

    try:
        body = json.loads(body)
    except:
        return func_resp(msg="Request body is not valid json", data=[], status=400)

    if not body or body is None:
        return func_resp(msg="Nothing send for update.", data=[], status=400)

    # status, msg, data = get_costing_by_id(headers=headers, extra_costing_id=extra_costing_id)
    # if status == 200:
    return func_resp(msg='', data=[], status=200)

    # return func_resp(msg=msg, data=data, status=status)


# @token_required
def extra_costings_related_methods(event, context):
    print(event)
    method = event.get("requestContext").get("http").get("method")
    # print(method)
    headers = event.get('headers')
    if method == "GET":
        if event.get("rawPath") == '/extra_costings/id':
            extra_costing_id = event.get("queryStringParameters", {'extra_costing_id': None}).get("extra_costing_id")
            if extra_costing_id is not None and extra_costing_id != "":
                # print(get_user_username(username))
                status, msg, data = get_costing_by_id(headers, extra_costing_id)
                return api_resp(msg=msg, data=data, status=status)
            return api_resp(msg="extra_costing_id not specified", data=[], status=400)
        elif event.get("rawPath") == '/extra_costings/translation_id':
            translation_id = event.get("queryStringParameters", {'translation_id': None}).get("translation_id")
            if translation_id is not None and translation_id != "":
                # print(get_user_username(username))
                status, msg, data = get_costing_by_type(headers, translation_id)
                return api_resp(msg=msg, data=data, status=status)
            return api_resp(msg="costing_type not specified", data=[], status=400)
        status, msg, data = get_all_extra_costings(headers)
        return api_resp(msg=msg, data=data, status=status)

    if method == "POST":
        body = event.get("body")
        status, msg, data = check_request_post(headers, body)
        if status == 200:
            body = json.loads(body)
            status, msg, data = register_new_costing(body)
        return api_resp(msg=msg, data=data, status=status)

    elif method == "PUT":
        extra_costing_id = event.get("queryStringParameters", {'extra_costing_id': None}).get("extra_costing_id")
        body = event.get("body")
        status, msg, data = check_request_put(headers, extra_costing_id, body)
        if status == 200:
            body = json.loads(body)
            status, msg, data = update_costing(extra_costing_id, body)
        return api_resp(msg=msg, data=data, status=status)
    #
    elif method == "DELETE":
        extra_costing_id = event.get("queryStringParameters", {'extra_costing_id': None}).get("extra_costing_id")
        status, msg, data = check_request_delete(headers, extra_costing_id)
        if status == 200:
            status, msg, data = delete_costing(extra_costing_id)
        return api_resp(msg=msg, data=data, status=status)

    else:
        return api_resp(msg="Not Allowed Method", data=[], status=400)

# if __name__ == "__main__":
#     check_request_post("a", "v")
