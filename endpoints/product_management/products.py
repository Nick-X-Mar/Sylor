import json
import uuid
from passlib.hash import pbkdf2_sha256
from authenticate.auth import token_required
from botocore import exceptions
from authenticate.validate_response import func_resp, api_resp
from databases.dbs import connect_to_dynamodb_resource, connect_to_dynamodb
from config.config import DYNAMODB_PRODUCTS_TABLE, DYNAMODB_TRANSLATIONS_TABLE
from endpoints.get_single_user import execute_get_user_by_username
from endpoints.translations_helper import connect_ids_with_translations


# def connect_ids_with_translations(headers, products, lang='el'):
#     client, status = connect_to_dynamodb_resource()
#     if status != 200:
#         return func_resp(msg=client, data=[], status=status)
#
#     table = client.Table(DYNAMODB_TRANSLATIONS_TABLE)
#
#     res = table.scan()
#     if res.get('Items') is not None and len(res['Items']) > 0:
#         translations = res['Items']
#     else:
#         return func_resp(msg='Translations table does not exist', data=[], status=200)
#
#     list_of_translation_ids = []
#     list_of_translation_names = []
#     for t in translations:
#         for k, v in t.items():
#             if k == 'translation_id':
#                 list_of_translation_ids.append(v)
#                 if lang in t.keys():
#                     list_of_translation_names.append(t[lang])
#                 else:
#                     list_of_translation_names.append("missing")
#
#     friendly_products = []
#     for product in products:
#         temp = {}
#         for k, v in product.items():
#             if k in list_of_translation_ids:
#                 k = list_of_translation_names[list_of_translation_ids.index(k)]
#             if v in list_of_translation_ids:
#                 v = list_of_translation_names[list_of_translation_ids.index(v)]
#             if k[-3:] == "_id":
#                 k = k[:-3]
#             temp[k] = v
#         friendly_products.append(temp)
#     return func_resp(msg='', data=friendly_products, status=200)


def get_all_products(headers):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_PRODUCTS_TABLE)
    res = table.scan()
    if res.get('Items') is not None and len(res['Items']) > 0:
        status, msg, data = connect_ids_with_translations(headers, res['Items'])
        return func_resp(msg=msg, data=data, status=status)
    else:
        return func_resp(msg='', data=[], status=200)


def get_product_by_id(headers, product_key):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_PRODUCTS_TABLE)
    # print(product_key)
    try:
        response = table.get_item(Key={'product_key': product_key})
    except:
        data = json.dumps({
            "product_key": product_key
        })
        print(f"Error: Failed to retrieve product with data: {data}.")
        return func_resp(msg="Failed to retrieve product.", data=[], status=400)

    # print(response.get('Item'))
    if response.get('Item') is None:
        return func_resp(msg=f"Product with product_key:{product_key} not found.", data=[], status=404)
    else:
        status, msg, data = connect_ids_with_translations(headers, [response['Item']])
        return func_resp(msg=msg, data=data, status=status)


def register_new_product(product):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_PRODUCTS_TABLE)

    # typologies = json.loads(str(product.get('typologies')).replace("'", '"'))
    # typologies = product.get('typologies')
    # specials = json.loads(str(product.product.get('specials')).replace("'", '"'))
    # typos = {}
    # for typology in typologies:
    # for key, value in typologies.items():
    #     typos[key] = value

    item = {
        'product_key': str(uuid.uuid4()),
        'product_name_id': product.get('product_name_id'),
        'img_url': product.get('img'),
        'typology_id': product.get('typology_id')
    }

    specials = product.get('specials')
    for sp in specials:
        item[sp.get('special_title_id')] = sp.get('special_id')

    try:
        table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(product_key)'
        )
        return func_resp(msg="Product Registered", data=[], status=200)
    except exceptions.ParamValidationError as error:
        print('The parameters you provided are incorrect: {}'.format(error))
        return func_resp(msg="Registration not completed due to parameter validation.", data=[], status=400)

    except exceptions.ClientError as e:
        print(f"Failed to register product with error: {str(e.response.get('Error'))}")
        msg = e.response.get('Error', {"Message": None}).get('Message')
        if msg is None:
            msg = "Failed to register product."
        else:
            msg = "product_key does not exist"
        return func_resp(msg=msg, data=[], status=400)

    except:
        print(f"Tried to store item: {item}")
        return func_resp(msg="Registration not completed.", data=[], status=400)


# @token_required
def check_request_post(headers, args):
    if args is None:
        return func_resp(msg="Please complete all required fields.", data=[], status=400)
    try:
        args = json.loads(args)
    except:
        return func_resp(msg="Request body is not valid json", data=[], status=400)
    print(args)
    # print(type(args))
    # print(args.get('product_name'))
    # args['product_name'] = args.get('product_name')
    # print(args)
    if not args or args is None:
        return func_resp(msg="Nothing send for insert.", data=[], status=400)

    product_name = args.get('product_name')
    product_name_id = args.get('product_name_id')
    img = args.get('img')
    typology_id = args.get('typology_id')
    typology_name = args.get('typology_name')
    specials = args.get('specials')

    if all(item is None for item in [product_name, product_name_id, img, typology_id, typology_name, specials]):
        return func_resp(msg='Please complete all required fields.', data=[], status=400)

    # try:
    #     print(type(args.get('typologies')))
    #     typologies = json.loads(str(args.get('typologies')).replace("'", '"'))
    #     specials = json.loads(str(args.get('specials')).replace("'", '"'))
    # except:
    #     return func_resp(msg="Request body is not valid json", data=[], status=400)

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
def product_related_methods(event, context):
    print(event)
    method = event.get("requestContext").get("http").get("method")
    # print(method)
    headers = event.get('headers')
    if method == "GET":
        if event.get("rawPath") == '/products/id':
            product_key = event.get("queryStringParameters", {'product_key': None}).get("product_key")
            if product_key is not None and product_key != "":
                status, msg, data = get_product_by_id(headers, product_key)
                return api_resp(msg=msg, data=data, status=status)
            return api_resp(msg="Product_key not specified", data=[], status=400)
        status, msg, data = get_all_products(headers)
        return api_resp(msg=msg, data=data, status=status)

    if method == "POST":
        body = event.get("body")
        status, msg, data = check_request_post(headers, body)
        if status == 200:
            body = json.loads(body)
            status, msg, data = register_new_product(body)
        return api_resp(msg=msg, data=data, status=status)

    # elif method == "PUT":
    #     product_key = event.get("queryStringParameters", {'product_key': None}).get("product_key")
    #     body = json.loads(event.get("body"))
    #     status, msg, data = check_request_put(headers, username, body)
    #     if status == 200:
    #         status, msg, data = update_user(username, body)
    #     return api_resp(msg=msg, data=data, status=status)
    #
    # elif method == "DELETE":
    #     product_key = event.get("queryStringParameters", {'product_key': None}).get("product_key")
    #     status, msg, data = check_request_delete(headers, username)
    #     if status == 200:
    #         status, msg, data = delete_user(username)
    #     return api_resp(msg=msg, data=data, status=status)

    else:
        return api_resp(msg="Not Allowed Method", data=[], status=400)


# if __name__ == "__main__":
#     check_request_post("a", "v")