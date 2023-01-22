import json
import uuid
from passlib.hash import pbkdf2_sha256
from authenticate.auth import token_required
from botocore import exceptions
from authenticate.validate_response import func_resp, api_resp
from databases.dbs import connect_to_dynamodb_resource, connect_to_dynamodb
from config.config import DYNAMODB_PRODUCTS_TABLE, DYNAMODB_TRANSLATIONS_TABLE
from endpoints.get_single_user import execute_get_user_by_username
from endpoints.offers_product_management.offers_product import register_new_offer_product
from endpoints.translations_helper import connect_ids_with_translations
from endpoints.get_single_product import get_product_by_id


def get_all_products(headers, fav):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_PRODUCTS_TABLE)
    res = table.scan()
    if res.get('Items') is not None and len(res['Items']) > 0:
        status, msg, data = 200, "No Favorite Products", []
        if fav:
            results = []
            for product in res['Items']:
                # print(product)
                if product.get('fav') is True:
                    results.append(product)
                    status, msg, data = connect_ids_with_translations(headers, results)
        else:
            status, msg, data = connect_ids_with_translations(headers, res['Items'])
        return func_resp(msg=msg, data=data, status=status)
    else:
        return func_resp(msg='', data=[], status=200)


# def get_product_by_id(headers, product_key):
#     client, status = connect_to_dynamodb_resource()
#     if status != 200:
#         return func_resp(msg=client, data=[], status=status)
#
#     table = client.Table(DYNAMODB_PRODUCTS_TABLE)
#     # print(product_key)
#     try:
#         response = table.get_item(Key={'product_key': product_key})
#     except:
#         data = json.dumps({
#             "product_key": product_key
#         })
#         print(f"Error: Failed to retrieve product with data: {data}.")
#         return func_resp(msg="Failed to retrieve product.", data=[], status=400)
#
#     # print(response.get('Item'))
#     if response.get('Item') is None:
#         return func_resp(msg=f"Product with product_key:{product_key} not found.", data=[], status=404)
#     else:
#         status, msg, data = connect_ids_with_translations(headers, [response['Item']])
#         return func_resp(msg=msg, data=data[0], status=status)


def _create_product(headers, product):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status), None

    table = client.Table(DYNAMODB_PRODUCTS_TABLE)
    item = {
        'product_key': str(uuid.uuid4()),
        'product_name': product.get('product_name'),
        'img_url': product.get('img'),
        'typology': product.get('typology'),
        'typology_1': product.get('typology_1'),
        'typology_2': product.get('typology_2'),
        'typology_3': product.get('typology_3'),
        'typology_4': product.get('typology_4'),
        'typology_5': product.get('typology_5'),
        'typology_6': product.get('typology_6'),
        'fav': product.get('fav') if product.get('fav') is not None else False,
    }
    try:
        table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(product_key)'
        )
        product['product'] = item.get('product_key')
        return func_resp(msg="Product Registered", data=[], status=200), product

    except exceptions.ParamValidationError as error:
        print('The parameters you provided are incorrect: {}'.format(error))
        return func_resp(msg="Registration not completed due to parameter validation.", data=[], status=400), None

    except exceptions.ClientError as e:
        print(f"Failed to register product with error: {str(e.response.get('Error'))}")
        msg = e.response.get('Error', {"Message": None}).get('Message')
        if msg is None:
            msg = "Failed to register product."
        else:
            msg = "product_key does not exist"
        return func_resp(msg=msg, data=[], status=400), None

    except:
        print(f"Tried to store item: {item}")
        return func_resp(msg="Registration not completed.", data=[], status=400), None


def register_new_product(headers, product, replicas=1):
    # Not an existing product
    if product.get('product') is None:
        (status, msg, data), product = _create_product(headers, product)
        if status != 200:
            return func_resp(msg=msg, data=data, status=status)
    return register_new_offer_product(headers, product, replicas)


def delete_product(headers, product_key):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)
    # print(DYNAMODB_USERS_TABLE)
    try:
        table = client.Table(DYNAMODB_PRODUCTS_TABLE)
        response = table.delete_item(
            Key={
                'product_key': product_key
            }
        )
        # print(response)
        status_code = response['ResponseMetadata']['HTTPStatusCode']
        if status_code == 200:
            return func_resp(msg='Product Deleted.', data=[], status=200)
        else:
            return func_resp(msg=response['ResponseMetadata'], data=[], status=status_code)
    except:
        return func_resp(msg='Deletion Failed.', data=[], status=400)


def update_product(headers, product_key, body):
    status, msg, data = get_product_by_id(headers, product_key)
    if data.get('fav') is True or data.get('fav') == "true":
        return func_resp(msg='Cannot update favorites.', data=[], status=400)

    upEx = "set "
    last = False
    attValues = {}
    if body.get('product_name') is not None:
        if last is True:
            upEx += ","
        upEx += " product_name = :product_name"
        attValues[":product_name"] = body.get('product_name')
        last = True
    if body.get('img') is not None:
        if last is True:
            upEx += ","
        upEx += " img = :img"
        attValues[":img"] = body.get('img')
        last = True
    if body.get('typology') is not None:
        if last is True:
            upEx += ","
        upEx += " typology = :typology"
        attValues[":typology"] = body.get('typology')
        last = True
    if body.get('typology_1') is not None:
        if last is True:
            upEx += ","
        upEx += " typology_1 = :typology_1"
        attValues[":typology_1"] = body.get('typology_1')
        last = True
    if body.get('typology_2') is not None:
        if last is True:
            upEx += ","
        upEx += " typology_2 = :typology_2"
        attValues[":typology_2"] = body.get('typology_2')
        last = True
    if body.get('typology_3') is not None:
        if last is True:
            upEx += ","
        upEx += " typology_3 = :typology_3"
        attValues[":typology_3"] = body.get('typology_3')
        last = True
    if body.get('typology_4') is not None:
        if last is True:
            upEx += ","
        upEx += " typology_4 = :typology_4"
        attValues[":typology_4"] = body.get('typology_4')
        last = True
    if body.get('typology_5') is not None:
        if last is True:
            upEx += ","
        upEx += " typology_5 = :typology_5"
        attValues[":typology_5"] = body.get('typology_5')
        last = True
    if body.get('typology_6') is not None:
        if last is True:
            upEx += ","
        upEx += " typology_6 = :typology_6"
        attValues[":typology_6"] = body.get('typology_6')

    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    try:
        table = client.Table(DYNAMODB_PRODUCTS_TABLE)
        response = table.update_item(
            Key={
                'product_key': product_key
            },
            UpdateExpression=upEx,
            ExpressionAttributeValues=attValues
        )
        status_code = response['ResponseMetadata']['HTTPStatusCode']
        if status_code == 200:
            return func_resp(msg='Product Updated.', data=[], status=status_code)
        else:
            return func_resp(msg=response['ResponseMetadata'], data=[], status=status_code)
    except:
        print(f"Update Failed.")
        print(upEx)
        print(attValues)
        return func_resp(msg='Update Failed.', data=[], status=400)


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

    offer = args.get('offer')

    if all(item is None for item in [offer]):
        return func_resp(msg='Offer is a required field.', data=[], status=400)

    return func_resp(msg="", data=[], status=200)


# @token_required
def check_request_delete(headers, product_key):
    if product_key is None or product_key == "":
        return func_resp(msg="product_key was not given.", data=[], status=400)
    return func_resp(msg="", data=[], status=200)


# @token_required
def check_request_put(headers, product_key, args):
    if args is None:
        return func_resp(msg="Please complete all required fields.", data=[], status=400)
    try:
        args = json.loads(args)
    except:
        return func_resp(msg="Request body is not valid json", data=[], status=400)

    if args is None:
        return func_resp(msg="Nothing send for update.", data=[], status=400)

    if product_key is None or product_key == "":
        return func_resp(msg="product_key was not given.", data=[], status=400)

    product_name = args.get('product_name')
    img = args.get('img')
    typology = args.get('typology')
    typology_1 = args.get('typology_1')
    typology_2 = args.get('typology_2')
    typology_3 = args.get('typology_3')
    typology_4 = args.get('typology_4')
    typology_5 = args.get('typology_5')
    typology_6 = args.get('typology_6')

    if all(item is None for item in [product_name, img, typology, typology_1, typology_2, typology_5, typology_3, typology_4, typology_6]):
        return func_resp(msg='Please complete all required fields.', data=[], status=400)

    # if args.get('fav') is True or args.get('fav') == "true":
    #     return func_resp(msg='Cannot update a favorite product', data=[], status=400)

    return func_resp(msg="", data=[], status=200)


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
        fav = event.get("queryStringParameters", {'fav': None}).get("fav")
        status, msg, data = get_all_products(headers, fav)
        return api_resp(msg=msg, data=data, status=status)

    if method == "POST":
        body = event.get("body")
        status, msg, data = check_request_post(headers, body)
        if status == 200:
            body = json.loads(body)
            replicas = event.get("queryStringParameters", {'replicas': None}).get("replicas")
            if replicas is not None:
                try:
                    replicas = int(replicas)
                except:
                    pass
            status, msg, data = register_new_product(headers, body, replicas)
        return api_resp(msg=msg, data=data, status=status)

    elif method == "PUT":
        product_key = event.get("queryStringParameters", {'product_key': None}).get("product_key")
        body = event.get("body")
        status, msg, data = check_request_put(headers, product_key, body)
        if status == 200:
            body = json.loads(body)
            status, msg, data = update_product(headers, product_key, body)
        return api_resp(msg=msg, data=data, status=status)

    elif method == "DELETE":
        product_key = event.get("queryStringParameters", {'product_key': None}).get("product_key")
        status, msg, data = check_request_delete(headers, product_key)
        if status == 200:
            status, msg, data = delete_product(headers, product_key)
        return api_resp(msg=msg, data=data, status=status)

    else:
        return api_resp(msg="Not Allowed Method", data=[], status=400)


# if __name__ == "__main__":
#     check_request_post("a", "v")