import json
from passlib.hash import pbkdf2_sha256
from authenticate.auth import token_required
from authenticate.validate_response import func_resp, api_resp
from databases.dbs import connect_to_dynamodb_resource, connect_to_dynamodb
from config.config import DYNAMODB_USERS_TABLE
from botocore.exceptions import ClientError
from endpoints.get_single_user import execute_get_user_by_username

# def execute_get_user_by_username(username):
#     client, status = connect_to_dynamodb_resource()
#     if status != 200:
#         return func_resp(msg=client, data=[], status=status)
#
#     table = client.Table(DYNAMODB_USERS_TABLE)
#     response = table.get_item(
#         TableName=DYNAMODB_USERS_TABLE,
#         Key={
#             'username': str(username),
#         })
#
#     if response.get('Item') is None:
#         print(f"User with username: '{username}' not found.")
#         return func_resp(msg="User not found.", data=[], status=404)
#     else:
#         # print("User data returned.")
#         return func_resp(msg='', data=response['Item'], status=200)


@token_required
def get_all_users(headers):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_USERS_TABLE)
    res = table.scan()
    if res.get('Items') is not None and len(res['Items']) > 0:
        return func_resp(msg='', data=res['Items'], status=200)
    else:
        return func_resp(msg='', data=[], status=200)


def secure_user_pass(pwd):
    hash = pbkdf2_sha256.hash(pwd, rounds=20000, salt_size=16)
    return hash


def register_new_user(args):
    # title = args.get('title')
    # user_role = args.get('user_role')
    firstName = args.get('firstName')
    lastName = args.get('lastName')
    username = args.get('username')
    password = args.get('password')
    hash_password = secure_user_pass(password)

    client, status = connect_to_dynamodb()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    try:
        client.put_item(
            TableName=DYNAMODB_USERS_TABLE,
            Item={
                # 'member_id': {'S': member_id},
                'firstName': {'S': firstName},
                'lastName': {'S': lastName},
                'username': {'S': username},
                'password': {'S': str(hash_password)}
            },
            ConditionExpression='attribute_not_exists(username)'
        )
        return func_resp(msg="User Registered", data=[], status=200)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print(f"Error: Username: {username}, already exists.")
            return func_resp(msg="Username already exists", data=[], status=e.response['ResponseMetadata']['HTTPStatusCode'])
        return func_resp(msg="Registration not completed.", data=[], status=400)
    except:
        data = json.dumps({
            "firstName": firstName,
            "lastName": lastName,
            "username": username
        })
        print(f"Error: Failed to register user with data: {data}.")
        return func_resp(msg="Registration not completed.", data=[], status=400)


def delete_user(username):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)
    # print(DYNAMODB_USERS_TABLE)
    try:
        table = client.Table(DYNAMODB_USERS_TABLE)
        response = table.delete_item(
            Key={
                'username': str(username)
            }
        )
        # print(response)
        status_code = response['ResponseMetadata']['HTTPStatusCode']
        if status_code == 200:
            return func_resp(msg='User Deleted.', data=[], status=200)
        else:
            return func_resp(msg=response['ResponseMetadata'], data=[], status=status_code)
    except:
        return func_resp(msg='Deletion Failed.', data=[], status=400)


def update_user(old_username, body):
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
    if body.get('password') is not None:
        if last is True:
            upEx += ","
        upEx += " password = :password"
        attValues[":password"] = str(secure_user_pass(body.get('password')))

    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    try:
        table = client.Table(DYNAMODB_USERS_TABLE)
        # print(upEx)
        # print(attValues)
        response = table.update_item(
            Key={
                'username': str(old_username)
            },
            UpdateExpression=upEx,
            ExpressionAttributeValues=attValues
        )
        status_code = response['ResponseMetadata']['HTTPStatusCode']
        if status_code == 200:
            return func_resp(msg='User Updated.', data=[], status=status_code)
        else:
            return func_resp(msg=response['ResponseMetadata'], data=[], status=status_code)
    except:
        print(f"Update Failed.")
        print(upEx)
        print(attValues)
        return func_resp(msg='Update Failed.', data=[], status=400)


@token_required
def check_request_post(headers, args):
    if args is None:
        return func_resp(msg="Please complete all required fields.", data=[], status=400)

    args = json.loads(args)

    firstName = args.get('firstName')
    lastName = args.get('lastName')
    username = args.get('username')
    password = args.get('password')

    # print(title, username)
    if username is None or username == "":
        return func_resp(msg="Username was not given.", data=[], status=400)

    if password is None or password == "":
        return func_resp(msg="Password was not given.", data=[], status=400)

    if any(item is None for item in [firstName, lastName, username, password]):
        return func_resp(msg='Please complete all required fields.', data=[], status=400)

    return func_resp(msg="", data=[], status=200)


@token_required
def check_request_delete(headers, username):
    if username is None or username == "":
        return func_resp(msg="username was not given.", data=[], status=400)
    return func_resp(msg="", data=[], status=200)


@token_required
def check_request_put(headers, old_username, body):
    if body is None:
        return func_resp(msg="Nothing send for update.", data=[], status=400)

    body = json.loads(body)
    if old_username is None or old_username == "":
        return func_resp(msg="Username was not given.", data=[], status=400)

    firstName = body.get('firstName')
    lastName = body.get('lastName')
    # username = body.get('username')  # Cannot change Username without member_id
    password = body.get('password')

    if all(item is None for item in [firstName, lastName, password]):
        return func_resp(msg='Please complete at least one field.', data=[], status=400)

    # status, msg, data = execute_get_user_by_username(username=old_username)
    # if status == 200:
    return func_resp(msg='', data=[], status=200)

    # return func_resp(msg=msg, data=data, status=status)


@token_required
def get_user_username(headers, username):
    return execute_get_user_by_username(username)


# @token_required
def user_related_methods(event, context):
    print(event)
    method = event.get("requestContext").get("http").get("method")
    # print(method)
    headers = event.get('headers')
    if method == "GET":
        if event.get("rawPath") == '/users/username':
            username = event.get("queryStringParameters", {'username': None}).get("username")
            if username is not None and username != "":
                # print(get_user_username(username))
                status, msg, data = get_user_username(headers, username)
                return api_resp(msg=msg, data=data, status=status)
            return api_resp(msg="Username not specified", data=[], status=400)
        status, msg, data = get_all_users(headers)
        return api_resp(msg=msg, data=data, status=status)

    elif method == "POST":
        body = event.get("body")
        status, msg, data = check_request_post(headers, body)
        if status == 200:
            body = json.loads(body)
            status, msg, data = register_new_user(body)
        return api_resp(msg=msg, data=data, status=status)

    elif method == "PUT":
        username = event.get("queryStringParameters", {'username': None}).get("username")
        body = event.get("body")
        status, msg, data = check_request_put(headers, username, body)
        if status == 200:
            body = json.loads(body)
            status, msg, data = update_user(username, body)
        return api_resp(msg=msg, data=data, status=status)

    elif method == "DELETE":
        username = event.get("queryStringParameters", {'username': None}).get("username")
        status, msg, data = check_request_delete(headers, username)
        if status == 200:
            status, msg, data = delete_user(username)
        return api_resp(msg=msg, data=data, status=status)

    else:
        return api_resp(msg="Not Allowed Method", data=[], status=400)
