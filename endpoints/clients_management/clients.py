import json
import uuid
from botocore import exceptions
from authenticate.validate_response import func_resp, api_resp
from databases.dbs import connect_to_dynamodb_resource
from config.config import DYNAMODB_CLIENTS_TABLE
from endpoints.translations_helper import connect_ids_with_translations


def get_all_clients(headers):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_CLIENTS_TABLE)
    res = table.scan()
    if res.get('Items') is not None and len(res['Items']) > 0:
        status, msg, data = connect_ids_with_translations(headers, res['Items'])
        return func_resp(msg=msg, data=data, status=status)
    else:
        return func_resp(msg='', data=[], status=200)


def get_client_by_id(headers, client_key):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_CLIENTS_TABLE)
    # print(client_key)
    try:
        response = table.get_item(Key={'client_key': client_key})
    except:
        data = json.dumps({
            "client_key": client_key
        })
        print(f"Error: Failed to retrieve client with data: {data}.")
        return func_resp(msg="Failed to retrieve client.", data=[], status=400)

    # print(response.get('Item'))
    if response.get('Item') is None:
        return func_resp(msg=f"Client with client_key:{client_key} not found.", data=[], status=404)
    else:
        return func_resp(msg='', data=response['Item'], status=200)


def register_new_client(body):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_CLIENTS_TABLE)

    item = {
        'client_key': str(uuid.uuid4()),
        'firstName': body.get('firstName'),
        'lastName': body.get('lastName'),
        'email': body.get('email'),
        'afm': body.get('afm'),
        'architect': body.get('architect'),
        'mobile': body.get('mobile'),
        'address': body.get('address'),
        'city': body.get('city'),
        'country': body.get('country')
    }

    try:
        table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(client_key)'
        )
        return func_resp(msg="Client Registered", data=[], status=200)
    except exceptions.ParamValidationError as error:
        print('The parameters you provided are incorrect: {}'.format(error))
        return func_resp(msg="Registration not completed due to parameter validation.", data=[], status=400)

    except exceptions.ClientError as e:
        print(f"Failed to register client with error: {str(e.response.get('Error'))}")
        msg = e.response.get('Error', {"Message": None}).get('Message')
        if msg is None:
            msg = "Failed to register client."
        else:
            msg = "client_key does not exist"
        return func_resp(msg=msg, data=[], status=400)

    except:
        print(f"Tried to store item: {item}")
        return func_resp(msg="Registration not completed.", data=[], status=400)


def update_client(client_key, body):
    upEx = "set "
    last = False
    attValues = {}
    if body.get('firstName') is not None:
        if last is True:
            upEx += ","
        upEx += " firstName = :firstName"
        attValues[":firstName"] = body.get('firstName')
        last = True
    if body.get('lastName') is not None:
        if last is True:
            upEx += ","
        upEx += " lastName = :lastName"
        attValues[":lastName"] = body.get('lastName')
        last = True
    if body.get('email') is not None:
        if last is True:
            upEx += ","
        upEx += " email = :email"
        attValues[":email"] = body.get('email')
    if body.get('architect') is not None:
        if last is True:
            upEx += ","
        upEx += " architect = :architect"
        attValues[":architect"] = body.get('architect')
    if body.get('mobile') is not None:
        if last is True:
            upEx += ","
        upEx += " mobile = :mobile"
        attValues[":mobile"] = body.get('mobile')
    if body.get('address') is not None:
        if last is True:
            upEx += ","
        upEx += " address = :address"
        attValues[":address"] = body.get('address')
    if body.get('city') is not None:
        if last is True:
            upEx += ","
        upEx += " city = :city"
        attValues[":city"] = body.get('city')
    if body.get('country') is not None:
        if last is True:
            upEx += ","
        upEx += " country = :country"
        attValues[":country"] = body.get('country')
    if body.get('afm') is not None:
        if last is True:
            upEx += ","
        upEx += " afm = :afm"
        attValues[":afm"] = body.get('afm')

    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    try:
        table = client.Table(DYNAMODB_CLIENTS_TABLE)
        # print(upEx)
        # print(attValues)
        response = table.update_item(
            Key={
                'client_key': str(client_key)
            },
            UpdateExpression=upEx,
            ExpressionAttributeValues=attValues
        )
        status_code = response['ResponseMetadata']['HTTPStatusCode']
        if status_code == 200:
            return func_resp(msg='Client Updated.', data=[], status=status_code)
        else:
            return func_resp(msg=response['ResponseMetadata'], data=[], status=status_code)
    except:
        print(f"Update Failed.")
        print(upEx)
        print(attValues)
        return func_resp(msg='Update Failed.', data=[], status=400)


def delete_client(client_key):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)
    # print(DYNAMODB_USERS_TABLE)
    try:
        table = client.Table(DYNAMODB_CLIENTS_TABLE)
        response = table.delete_item(
            Key={
                'client_key': str(client_key)
            }
        )
        # print(response)
        status_code = response['ResponseMetadata']['HTTPStatusCode']
        if status_code == 200:
            return func_resp(msg='Client Deleted.', data=[], status=200)
        else:
            return func_resp(msg=response['ResponseMetadata'], data=[], status=status_code)
    except:
        return func_resp(msg='Deletion Failed.', data=[], status=400)


# @token_required
def check_request_post(headers, args):
    if args is None:
        return func_resp(msg="Please complete all required fields.", data=[], status=400)

    try:
        args = json.loads(args)
    except:
        return func_resp(msg="Request body is not valid json", data=[], status=400)

    if not args or args is None:
        return func_resp(msg="Nothing send for insert.", data=[], status=400)

    lastName = args.get('lastName')
    if all(item is None for item in [lastName]):
        return func_resp(msg='Please complete all required fields.', data=[], status=400)

    return func_resp(msg="", data=[], status=200)


# @token_required
def check_request_delete(headers, client_key):
    if client_key is None or client_key == "":
        return func_resp(msg="client_key was not given.", data=[], status=400)
    return func_resp(msg="", data=[], status=200)


# @token_required
def check_request_put(headers, client_key, body):
    if body is None:
        return func_resp(msg="Nothing send for update.", data=[], status=400)

    if client_key is None or client_key == "":
        return func_resp(msg="Client_key was not given.", data=[], status=400)

    firstName = body.get('firstName')
    lastName = body.get('lastName')
    email = body.get('email')
    afm = body.get('afm')
    architect = body.get('architect')
    mobile = body.get('mobile')
    address = body.get('address')
    city = body.get('city')
    country = body.get('country')

    if all(item is None for item in [firstName, lastName, email, afm, architect, mobile, address, city, country]):
        return func_resp(msg='Please complete at least one field.', data=[], status=400)

    return func_resp(msg='', data=[], status=200)

    # return func_resp(msg=msg, data=data, status=status)


# @token_required
def client_related_methods(event, context):
    print(event)
    method = event.get("requestContext").get("http").get("method")
    # print(method)
    headers = event.get('headers')
    if method == "GET":
        if event.get("rawPath") == '/clients/id':
            client_key = event.get("queryStringParameters", {'client_key': None}).get("client_key")
            if client_key is not None and client_key != "":
                status, msg, data = get_client_by_id(headers, client_key)
                return api_resp(msg=msg, data=data, status=status)
            return api_resp(msg="Client_key not specified", data=[], status=400)
        status, msg, data = get_all_clients(headers)
        return api_resp(msg=msg, data=data, status=status)

    if method == "POST":
        body = event.get("body")
        status, msg, data = check_request_post(headers, body)
        if status == 200:
            body = json.loads(body)
            status, msg, data = register_new_client(body)
        return api_resp(msg=msg, data=data, status=status)

    elif method == "PUT":
        client_key = event.get("queryStringParameters", {'client_key': None}).get("client_key")
        body = json.loads(event.get("body"))
        status, msg, data = check_request_put(headers, client_key, body)
        if status == 200:
            status, msg, data = update_client(client_key, body)
        return api_resp(msg=msg, data=data, status=status)

    elif method == "DELETE":
        client_key = event.get("queryStringParameters", {'client_key': None}).get("client_key")
        status, msg, data = check_request_delete(headers, client_key)
        if status == 200:
            status, msg, data = delete_client(client_key)
        return api_resp(msg=msg, data=data, status=status)

    else:
        return api_resp(msg="Not Allowed Method", data=[], status=400)


# if __name__ == "__main__":
#     check_request_post("a", "v")