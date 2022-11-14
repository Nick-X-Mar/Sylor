import json
from passlib.hash import pbkdf2_sha256
from authenticate.auth import token_required
from authenticate.validate_response import func_resp, api_resp
from databases.dbs import connect_to_dynamodb_resource, connect_to_dynamodb
from config.config import DYNAMODB_USERS_TABLE
from botocore.exceptions import ClientError
from endpoints.get_single_user import execute_get_user_by_username


# @token_required
def check_request_post(headers, args):
    product_specific_name = args.get('product_specific_name')
    product_specific_enum_value_ids = args.get('product_specific_enum_value_ids')

    if not product_specific_enum_value_ids:
        return func_resp(msg='Please complete all required fields.', data=[], status=400)

    if product_specific_name is None:
        return func_resp(msg='Please complete all required fields.', data=[], status=400)

    return func_resp(msg="", data=[], status=200)


# @token_required
def check_request_delete(headers, username):
    if username is None or username == "":
        return func_resp(msg="username was not given.", data=[], status=400)
    return func_resp(msg="", data=[], status=200)


# @token_required
def check_request_put(headers, old_username, body):
    if body is None:
        return func_resp(msg="Nothing send for update.", data=[], status=400)

    if old_username is None or old_username == "":
        return func_resp(msg="Username was not given.", data=[], status=400)

    firstName = body.get('firstName')
    lastName = body.get('lastName')
    # username = body.get('username')  # Cannot change Username without member_id
    password = body.get('password')

    if all(item is None for item in [firstName, lastName, password]):
        return func_resp(msg='Please complete at least one field.', data=[], status=400)

    status, msg, data = execute_get_user_by_username(username=old_username)
    if status == 200:
        return func_resp(msg='', data=[], status=200)

    return func_resp(msg=msg, data=data, status=status)


# @token_required
def product_specific_related_methods(event, context):
    print(event)
    method = event.get("requestContext").get("http").get("method")
    # print(method)
    headers = event.get('headers')
    # if method == "GET":
    #     if event.get("rawPath") == '/users/username':
    #         username = event.get("queryStringParameters", {'username': None}).get("username")
    #         if username is not None and username != "":
    #             # print(get_user_username(username))
    #             status, msg, data = get_user_username(headers, username)
    #             return api_resp(msg=msg, data=data, status=status)
    #         return api_resp(msg="Username not specified", data=[], status=400)
    #     status, msg, data = get_all_users(headers)
    #     return api_resp(msg=msg, data=data, status=status)

    if method == "POST":
        body = json.loads(event.get("body"))
        status, msg, data = check_request_post(headers, body)
        # if status == 200:
        #     status, msg, data = register_new_user(body)
        return api_resp(msg=msg, data=data, status=status)

    # elif method == "PUT":
    #     username = event.get("queryStringParameters", {'username': None}).get("username")
    #     body = json.loads(event.get("body"))
    #     status, msg, data = check_request_put(headers, username, body)
    #     if status == 200:
    #         status, msg, data = update_user(username, body)
    #     return api_resp(msg=msg, data=data, status=status)
    #
    # elif method == "DELETE":
    #     username = event.get("queryStringParameters", {'username': None}).get("username")
    #     status, msg, data = check_request_delete(headers, username)
    #     if status == 200:
    #         status, msg, data = delete_user(username)
    #     return api_resp(msg=msg, data=data, status=status)

    else:
        return api_resp(msg="Not Allowed Method", data=[], status=400)


# if __name__ == "__main__":
#     check_request_post("a", "v")