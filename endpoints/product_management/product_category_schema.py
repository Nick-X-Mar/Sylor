import json
import uuid
from passlib.hash import pbkdf2_sha256
from authenticate.auth import token_required
from authenticate.validate_response import func_resp, api_resp
from databases.dbs import connect_to_dynamodb_resource, connect_to_dynamodb
from config.config import DYNAMODB_CATEGORY_TABLE
from botocore.exceptions import ClientError
from endpoints.get_single_user import execute_get_user_by_username


def register_new_product(product):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_CATEGORY_TABLE)
    product_id = uuid.uuid4()
    item = {
        'translation_id': str(product_id),
        'product_name': product.get('product_name'),
        'product_name_id': product.get('product_name_id'),
        'img': product.get('img'),
        'typologies': product.get('typologies'),
        'specials': product.get('specials'),
    }
    for key, value in translations.items():
        item[key] = value
    # print(f"Item: {item}")
    try:
        table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(translation_id)'
        )
        return func_resp(msg="Translation Registered", data=[], status=200)
    except exceptions.ParamValidationError as error:
        print('The parameters you provided are incorrect: {}'.format(error))
        return func_resp(msg="Registration not completed.", data=[], status=400)
    except:
        return func_resp(msg="Registration not completed.", data=[], status=400)


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

    product_name = args.get('product_name')
    product_name_id = args.get('product_name_id')
    img = args.get('img')
    typologies = args.get('typologies')
    specials = args.get('specials')

    if all(item is None for item in [product_name, product_name_id, img, typologies, specials]):
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
def product_category_related_methods(event, context):
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
        body = event.get("body")
        status, msg, data = check_request_post(headers, body)
        if status == 200:
            status, msg, data = register_new_product(body)
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