import json
import uuid
from botocore import exceptions
from authenticate.validate_response import func_resp, api_resp
from config import config
from databases.dbs import connect_to_dynamodb_resource
from config.config import DYNAMODB_OFFER_COSTING_TABLE, DYNAMODB_OFFERS_PRODUCT_TABLE, DYNAMODB_TRANSLATIONS_TABLE
from endpoints.get_single_product import get_product_by_id, get_products_by_id_list
from endpoints.translations_helper import connect_ids_with_translations
from boto3.dynamodb.conditions import Key, Attr

from endpoints.translations_management.translations import get_all_translations


def get_offer_costing_by_offer(headers, offer_id):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_OFFER_COSTING_TABLE)
    if offer_id is not None:
        res = table.scan(FilterExpression=Attr('offer').eq(offer_id))
    else:
        res = table.scan()
    results = res['Items']
    if results is not None and len(results) > 0:
        return func_resp(msg='', data=results, status=200)
    else:
        return func_resp(msg='', data=[], status=200)


def get_offer_costing_by_id(headers, offer_costing_id):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_OFFER_COSTING_TABLE)
    try:
        response = table.get_item(Key={'offer_costing_id': offer_costing_id})
    except:
        data = json.dumps({
            "offer_costing_id": offer_costing_id
        })
        print(f"Error: Failed to retrieve offer_product with data: {data}.")
        return func_resp(msg="Failed to retrieve offer_product.", data=[], status=400)

    # print(response.get('Item'))
    if response.get('Item') is None:
        return func_resp(msg=f"offer_product with offer_costing_id:{offer_costing_id} not found.", data=[],
                         status=404)
    else:
        return func_resp(msg="", data=response['Item'], status=200)


def get_days_costing_for_offerproducts(headers, dynamodb, offer_id):
    # translations_table = dynamodb.Table(DYNAMODB_OFFERS_PRODUCT_TABLE)
    status, msg, translations = get_all_translations(headers)
    if status != 200:
        return "Error fetching translations"

    print(f'offer_id {offer_id}')
    total_days_needed = 0
    grouped_products = {}
    offer_product_table = dynamodb.Table(DYNAMODB_OFFERS_PRODUCT_TABLE)
    results = offer_product_table.scan(FilterExpression=Attr('offer').eq(offer_id)).get('Items')
    if results is not None and len(results) > 0:
        for offer_product in results:
            # print(f"offer_product: {offer_product}")
            status, msg, product = get_product_by_id(headers=headers, product_key=offer_product.get('product'), translation=False, lang='el')
            # print(f'status: {status}')
            # print(f'product: {product}')
            if status == 200:
                print(f"offer_product: {offer_product}")
                print(f"product: {product}")
                if offer_product.get('quantity') is not None and offer_product.get('quantity') != 'None':
                    number_of_products_added = int(offer_product.get('quantity'))
                else:
                    number_of_products_added = 1

                # print(f"offer_product.get('extra_costing_m2'): {offer_product.get('extra_costing_m2')}")
                if offer_product.get('extra_costing_m2') is not None and offer_product.get('extra_costing_m2') != 'None':
                    extra_time_needed = float(offer_product.get('extra_costing_m2')) * number_of_products_added
                else:
                    extra_time_needed = 0
                if product.get('placement_h') is not None and offer_product.get('placement_h') != 'None':
                    units_placement = int(product.get('placement_h')) * number_of_products_added
                else:
                    units_placement = 0
                total_days_needed += extra_time_needed + units_placement
                if grouped_products.get((product.get('product_name'))) is None:
                    grouped_products[product.get('product_name')] = {
                        "number_of_products": str(number_of_products_added),
                        "units_placement": str(units_placement),
                        "extra_time_needed": str(extra_time_needed),
                        "total_time": str(int(extra_time_needed) + int(units_placement))
                    }
                else:
                    grouped_products[product.get('product_name')] = {
                        "number_of_products": str(int(grouped_products.get(product.get('product_name')).get('number_of_products')) + number_of_products_added),
                        "units_placement": str(int(grouped_products.get(product.get('product_name')).get('units_placement')) + units_placement),
                        "extra_time_needed": str(int(grouped_products.get(product.get('product_name')).get('extra_time_needed')) + extra_time_needed),
                        "total_time": str(int(grouped_products.get(product.get('product_name')).get('total_time')) + int(extra_time_needed) + int(units_placement))
                    }
                grouped_products['total_days_needed'] = total_days_needed
                return grouped_products
    return "Error with offer products table"


def register_new_offer_costing(headers, args):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)


    # + sum of product topothetisi
    # + sum of extra costings per product

    # (2) offer_products --> get products
    # product / dimensions gia ta extras
    grouped_products = get_days_costing_for_offerproducts(headers, client, str(args.get('offer')))
    print(grouped_products)
    if isinstance(grouped_products, str):
        return func_resp(msg=grouped_products, data=[], status=400)

    table = client.Table(DYNAMODB_OFFER_COSTING_TABLE)

    area = args.get("area").upper()
    area_dist = 1
    if area == "AREA_1":
        area_dist = config.AREA_1
    elif area == "AREA_2":
        area_dist = config.AREA_2
    elif area == "AREA_3":
        area_dist = config.AREA_3
    elif area == "AREA_4":
        area_dist = config.AREA_4
    elif area == "AREA_5":
        area_dist = config.AREA_5

    item = {
        'offer_costing_id': str(uuid.uuid4()),
        'trip_amount': str(float(area_dist) * int(args.get("people")) * float(config.WORK_HOUR_COST) + int(grouped_products.get('total_days_needed'))),
        'area': str(area_dist),
        'people': str(args.get("people")),
        'per_product_amount': str(config.PER_PRODUCT_COST),
        'offer': str(args.get('offer'))
    }
    try:
        table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(offer_costing_id)'
        )
        return func_resp(msg="offer_costing Registered", data={
            "offer_costing_id": item['offer_costing_id'],
            "trip_amount": item.get('trip_amount'),
            "per_product_amount": config.PER_PRODUCT_COST
        }, status=200)
    except exceptions.ParamValidationError as error:
        print('The parameters you provided are incorrect: {}'.format(error))
        return func_resp(msg="Registration not completed.", data=[], status=400)
    except:
        return func_resp(msg="Registration not completed.", data=[], status=400)


def delete_offer(headers, offer_costing_id):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)
    # print(DYNAMODB_USERS_TABLE)
    try:
        table = client.Table(DYNAMODB_OFFER_COSTING_TABLE)
        response = table.delete_item(
            Key={
                'offer_costing_id': offer_costing_id
            }
        )
        # print(response)
        status_code = response['ResponseMetadata']['HTTPStatusCode']
        if status_code == 200:
            return func_resp(msg='offer_costing_id Deleted.', data=[], status=200)
        else:
            return func_resp(msg=response['ResponseMetadata'], data=[], status=status_code)
    except:
        return func_resp(msg='Deletion Failed.', data=[], status=400)


def update_offer_costing_id(headers, offer_costing_id, body):
    upEx = "set "
    last = False
    attValues = {}
    if body.get('offer') is not None and body.get('offer') != "":
        if last is True:
            upEx += ","
        upEx += " offer = :offer"
        attValues[":offer"] = str(body.get('offer'))
        last = True
    if body.get('trip_amount') is not None and body.get('trip_amount') != "":
        if last is True:
            upEx += ","
        upEx += " trip_amount = :trip_amount"
        attValues[":trip_amount"] = str(body.get('trip_amount'))
        last = True
    if body.get('per_product_amount') is not None and body.get('per_product_amount') != "":
        if last is True:
            upEx += ","
        upEx += " per_product_amount = :per_product_amount"
        attValues[":per_product_amount"] = str(body.get('per_product_amount'))
        last = True
    if body.get('transportation_out') is not None and body.get('transportation_out') != "":
        if last is True:
            upEx += ","
        upEx += " transportation_out = :transportation_out"
        attValues[":transportation_out"] = str(body.get('transportation_out'))
        last = True
    if body.get('transportation_in') is not None and body.get('transportation_in') != "":
        if last is True:
            upEx += ","
        upEx += " transportation_in = :transportation_in"
        attValues[":transportation_in"] = str(body.get('transportation_in'))
        last = True
    if body.get('epimetrisi') is not None and body.get('epimetrisi') != "":
        if last is True:
            upEx += ","
        upEx += " epimetrisi = :epimetrisi"
        attValues[":epimetrisi"] = str(body.get('epimetrisi'))
        last = True
    if body.get('crew_cost') is not None and body.get('crew_cost') != "":
        if last is True:
            upEx += ","
        upEx += " crew_cost = :crew_cost"
        attValues[":crew_cost"] = str(body.get('crew_cost'))
        last = True
    if body.get('extra_cost') is not None and body.get('extra_cost') != "":
        if last is True:
            upEx += ","
        upEx += " extra_cost = :extra_cost"
        attValues[":extra_cost"] = str(body.get('extra_cost'))
        last = True
    if body.get('trip_amount_list') is not None and body.get('trip_amount_list') != "":
        if last is True:
            upEx += ","
        upEx += " trip_amount_list = :trip_amount_list"
        attValues[":trip_amount_list"] = (body.get('trip_amount_list'))
        last = True
    if body.get('per_product_amount') is not None and body.get('per_product_amount') != "":
        if last is True:
            upEx += ","
        upEx += " per_product_amount = :per_product_amount"
        attValues[":per_product_amount"] = (body.get('per_product_amount'))
        last = True
    if body.get('transportation_out_list') is not None and body.get('transportation_out_list') != "":
        if last is True:
            upEx += ","
        upEx += " transportation_out_list = :transportation_out_list"
        attValues[":transportation_out_list"] = (body.get('transportation_out_list'))
        last = True
    if body.get('transportation_in_list') is not None and body.get('transportation_in_list') != "":
        if last is True:
            upEx += ","
        upEx += " transportation_in_list = :transportation_in_list"
        attValues[":transportation_in_list"] = (body.get('transportation_in_list'))
        last = True
    if body.get('epimetrisi_list') is not None and body.get('epimetrisi_list') != "":
        if last is True:
            upEx += ","
        upEx += " epimetrisi_list = :epimetrisi_list"
        attValues[":epimetrisi_list"] = (body.get('epimetrisi_list'))
        last = True
    if body.get('crew_cost_list') is not None and body.get('crew_cost_list') != "":
        if last is True:
            upEx += ","
        upEx += " crew_cost_list = :crew_cost_list"
        attValues[":crew_cost_list"] = (body.get('crew_cost_list'))
        last = True
    if body.get('extra_cost_list') is not None and body.get('extra_cost_list') != "":
        if last is True:
            upEx += ","
        upEx += " extra_cost_list = :extra_cost_list"
        attValues[":extra_cost_list"] = (body.get('extra_cost_list'))
        # last = True

    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    try:
        table = client.Table(DYNAMODB_OFFER_COSTING_TABLE)
        response = table.update_item(
            Key={
                'offer_costing_id': str(offer_costing_id)
            },
            UpdateExpression=upEx,
            ExpressionAttributeValues=attValues
        )
        status_code = response['ResponseMetadata']['HTTPStatusCode']
        if status_code == 200:
            return func_resp(msg='offer_costing Updated.', data=[], status=status_code)
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
    people = args.get('people')
    area = args.get('area')
    if all(item is None for item in [offer, area, people]):
        return func_resp(msg='Please complete all required fields.', data=[], status=400)

    return func_resp(msg="", data=[], status=200)


# @token_required
def check_request_delete(headers, offer_costing_id):
    if offer_costing_id is None or offer_costing_id == "":
        return func_resp(msg="offer_costing_id was not given.", data=[], status=400)
    return func_resp(msg="", data=[], status=200)


# @token_required
def check_request_put(headers, offer_costing_id, args):
    if args is None:
        return func_resp(msg="Please complete all required fields.", data=[], status=400)
    try:
        args = json.loads(args)
    except:
        return func_resp(msg="Request body is not valid json", data=[], status=400)

    if args is None:
        return func_resp(msg="Nothing send for update.", data=[], status=400)

    if offer_costing_id is None or offer_costing_id == "":
        return func_resp(msg="offer_costing_id was not given.", data=[], status=400)

    return func_resp(msg="", data=[], status=200)


# @token_required
def offer_costing_related_methods(event, context):
    print(event)
    method = event.get("requestContext").get("http").get("method")
    headers = event.get('headers')
    if method == "GET":
        if event.get("rawPath") == '/offer_costing/id':
            offer_costing_id = event.get("queryStringParameters", {'offer_costing_id': None}).get("offer_costing_id")
            if offer_costing_id is not None and offer_costing_id != "":
                status, msg, data = get_offer_costing_by_id(headers, offer_costing_id)
                return api_resp(msg=msg, data=data, status=status)
            return api_resp(msg="offer_costing_id not specified", data=[], status=400)
        if event.get("rawPath") == '/offer_costing/offer_id':
            offer_id = event.get("queryStringParameters", {'offer_id': None}).get("offer_id")
            if offer_id is not None and offer_id != "":
                status, msg, data = get_offer_costing_by_offer(headers, offer_id)
                return api_resp(msg=msg, data=data, status=status)
            return api_resp(msg="offer_id not specified", data=[], status=400)

    if method == "POST":
        body = event.get("body")
        status, msg, data = check_request_post(headers, body)
        if status == 200:
            body = json.loads(body)
            status, msg, data = register_new_offer_costing(headers, body)
        return api_resp(msg=msg, data=data, status=status)

    elif method == "PUT":
        offer_costing_id = event.get("queryStringParameters", {'offer_costing_id': None}).get("offer_costing_id")
        body = event.get("body")
        status, msg, data = check_request_put(headers, offer_costing_id, body)
        if status == 200:
            body = json.loads(body)
            status, msg, data = update_offer_costing_id(headers, offer_costing_id, body)
        return api_resp(msg=msg, data=data, status=status)

    elif method == "DELETE":
        offer_costing_id = event.get("queryStringParameters", {'offer_costing_id': None}).get("offer_costing_id")
        status, msg, data = check_request_delete(headers, offer_costing_id)
        if status == 200:
            status, msg, data = delete_offer(headers, offer_costing_id)
        return api_resp(msg=msg, data=data, status=status)

    else:
        return api_resp(msg="Not Allowed Method", data=[], status=400)

