import json
import uuid
from botocore import exceptions
from authenticate.validate_response import func_resp, api_resp
from databases.dbs import connect_to_dynamodb_resource
from config.config import DYNAMODB_OFFERS_PRODUCT_TABLE
from endpoints.translations_helper import connect_ids_with_translations


def get_all_offers(headers, fav):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_OFFERS_PRODUCT_TABLE)
    res = table.scan()
    if res.get('Items') is not None and len(res['Items']) > 0:
        status, msg, data = 200, "No Favorite offers", []
        if fav:
            results = []
            for offer_product in res['Items']:
                # print(offer_product)
                if offer_product.get('fav') is True:
                    results.append(offer_product)
                    status, msg, data = connect_ids_with_translations(headers, results)
        else:
            status, msg, data = connect_ids_with_translations(headers, res['Items'])
        return func_resp(msg=msg, data=data, status=status)
    else:
        return func_resp(msg='', data=[], status=200)


def get_offer_by_id(headers, offer_product_key):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_OFFERS_PRODUCT_TABLE)
    try:
        response = table.get_item(Key={'offer_product_key': offer_product_key})
    except:
        data = json.dumps({
            "offer_product_key": offer_product_key
        })
        print(f"Error: Failed to retrieve offer_product with data: {data}.")
        return func_resp(msg="Failed to retrieve offer_product.", data=[], status=400)

    # print(response.get('Item'))
    if response.get('Item') is None:
        return func_resp(msg=f"offer_product with offer_product_key:{offer_product_key} not found.", data=[], status=404)
    else:
        status, msg, data = connect_ids_with_translations(headers, [response['Item']])
        return func_resp(msg=msg, data=data, status=status)


def register_new_offer_product(offer_product):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_OFFERS_PRODUCT_TABLE)
    item = {
        'offer_product_key': str(uuid.uuid4()),
        'offer': offer_product.get('offer'),
        'product': offer_product.get('product'),
        'qountity': int(offer_product.get('qountity')),
        'x': str(offer_product.get('x')),
        'y': str(offer_product.get('y')),
        'z': str(offer_product.get('z')),
        'unit_amount': str(offer_product.get('unit_amount')),
        'offer_position': int(offer_product.get('offer_position')),
        'total_amount': str(float(offer_product.get('unit_amount')) * int(offer_product.get('qountity')))
    }
    try:
        table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(offer_product_key)'
        )
        return func_resp(msg="offer_product Registered", data=[], status=200)
    except exceptions.ParamValidationError as error:
        print('The parameters you provided are incorrect: {}'.format(error))
        return func_resp(msg="Registration not completed due to parameter validation.", data=[], status=400)

    except exceptions.ClientError as e:
        print(f"Failed to register offer_product with error: {str(e.response.get('Error'))}")
        msg = e.response.get('Error', {"Message": None}).get('Message')
        if msg is None:
            msg = "Failed to register offer_product."
        else:
            msg = "offer_product_key does not exist"
        return func_resp(msg=msg, data=[], status=400)

    except:
        print(f"Tried to store item: {item}")
        return func_resp(msg="Registration not completed.", data=[], status=400)


def delete_offer(offer_product_key):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)
    # print(DYNAMODB_USERS_TABLE)
    try:
        table = client.Table(DYNAMODB_OFFERS_PRODUCT_TABLE)
        response = table.delete_item(
            Key={
                'offer_product_key': offer_product_key
            }
        )
        # print(response)
        status_code = response['ResponseMetadata']['HTTPStatusCode']
        if status_code == 200:
            return func_resp(msg='offer_product Deleted.', data=[], status=200)
        else:
            return func_resp(msg=response['ResponseMetadata'], data=[], status=status_code)
    except:
        return func_resp(msg='Deletion Failed.', data=[], status=400)


def update_offer(offer_product_key, body):
    upEx = "set "
    last = False
    attValues = {}
    if body.get('offer_name') is not None:
        if last is True:
            upEx += ","
        upEx += " offer_name = :offer_name"
        attValues[":offer_name"] = body.get('offer_name')
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
        table = client.Table(DYNAMODB_OFFERS_PRODUCT_TABLE)
        response = table.update_item(
            Key={
                'offer_product_key': offer_product_key
            },
            UpdateExpression=upEx,
            ExpressionAttributeValues=attValues
        )
        status_code = response['ResponseMetadata']['HTTPStatusCode']
        if status_code == 200:
            return func_resp(msg='offer_product Updated.', data=[], status=status_code)
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

    return func_resp(msg="", data=[], status=200)


# @token_required
def check_request_delete(headers, offer_product_key):
    if offer_product_key is None or offer_product_key == "":
        return func_resp(msg="offer_product_key was not given.", data=[], status=400)
    return func_resp(msg="", data=[], status=200)


# @token_required
def check_request_put(headers, offer_product_key, args):
    if args is None:
        return func_resp(msg="Please complete all required fields.", data=[], status=400)
    try:
        args = json.loads(args)
    except:
        return func_resp(msg="Request body is not valid json", data=[], status=400)

    if args is None:
        return func_resp(msg="Nothing send for update.", data=[], status=400)

    if offer_product_key is None or offer_product_key == "":
        return func_resp(msg="offer_product_key was not given.", data=[], status=400)

    offer_name = args.get('offer_name')
    img = args.get('img')
    typology = args.get('typology')
    typology_1 = args.get('typology_1')
    typology_2 = args.get('typology_2')
    typology_3 = args.get('typology_3')
    typology_4 = args.get('typology_4')
    typology_5 = args.get('typology_5')
    typology_6 = args.get('typology_6')

    if all(item is None for item in [offer_name, img, typology, typology_1, typology_2, typology_5, typology_3, typology_4, typology_6]):
        return func_resp(msg='Please complete all required fields.', data=[], status=400)

    return func_resp(msg="", data=[], status=200)


# @token_required
def offers_product_related_methods(event, context):
    print(event)
    method = event.get("requestContext").get("http").get("method")
    # print(method)
    headers = event.get('headers')
    if method == "GET":
        if event.get("rawPath") == '/offers/id':
            offer_product_key = event.get("queryStringParameters", {'offer_product_key': None}).get("offer_product_key")
            if offer_product_key is not None and offer_product_key != "":
                status, msg, data = get_offer_by_id(headers, offer_product_key)
                return api_resp(msg=msg, data=data, status=status)
            return api_resp(msg="offer_product_key not specified", data=[], status=400)
        fav = event.get("queryStringParameters", {'fav': None}).get("fav")
        status, msg, data = get_all_offers(headers, fav)
        return api_resp(msg=msg, data=data, status=status)

    if method == "POST":
        body = event.get("body")
        status, msg, data = check_request_post(headers, body)
        if status == 200:
            body = json.loads(body)
            status, msg, data = register_new_offer_product(body)
        return api_resp(msg=msg, data=data, status=status)

    elif method == "PUT":
        offer_product_key = event.get("queryStringParameters", {'offer_product_key': None}).get("offer_product_key")
        body = event.get("body")
        status, msg, data = check_request_put(headers, offer_product_key, body)
        if status == 200:
            body = json.loads(body)
            status, msg, data = update_offer(offer_product_key, body)
        return api_resp(msg=msg, data=data, status=status)

    elif method == "DELETE":
        offer_product_key = event.get("queryStringParameters", {'offer_product_key': None}).get("offer_product_key")
        status, msg, data = check_request_delete(headers, offer_product_key)
        if status == 200:
            status, msg, data = delete_offer(offer_product_key)
        return api_resp(msg=msg, data=data, status=status)

    else:
        return api_resp(msg="Not Allowed Method", data=[], status=400)


# if __name__ == "__main__":
#     check_request_post("a", "v")