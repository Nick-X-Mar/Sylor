import json
import uuid
from botocore import exceptions
from authenticate.validate_response import func_resp, api_resp
from databases.dbs import connect_to_dynamodb_resource
from config.config import DYNAMODB_OFFERS_TABLE
from endpoints.translations_helper import connect_ids_with_translations


def get_all_offers(headers):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_OFFERS_TABLE)
    res = table.scan()
    if res.get('Items') is not None and len(res['Items']) > 0:
        # status, msg, data = connect_ids_with_translations(headers, res['Items'])
        return func_resp(msg="", data=res['Items'], status=200)
    else:
        return func_resp(msg='', data=[], status=200)


def get_offer_by_id(headers, offer_key):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_OFFERS_TABLE)
    try:
        response = table.get_item(Key={'offer_key': offer_key})
    except:
        data = json.dumps({
            "offer_key": offer_key
        })
        print(f"Error: Failed to retrieve offer with data: {data}.")
        return func_resp(msg="Failed to retrieve offer.", data=[], status=400)

    # print(response.get('Item'))
    if response.get('Item') is None:
        return func_resp(msg=f"offer with offer_key:{offer_key} not found.", data=[], status=404)
    else:
        # status, msg, data = connect_ids_with_translations(headers, [response['Item']])
        return func_resp(msg="", data=response['Item'], status=200)


def register_new_offer(offer):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_OFFERS_TABLE)
    if offer.get('offer_id') is not None:
        initital_offer = '00000'
        try:
            offer_id = str(int(offer.get('offer_id')) + 1)
            offer_id = initital_offer[:-len(offer_id)] + offer_id
        except:
            offer_id = None
    else:
        offer_id = None

    item = {
        'offer_key': str(uuid.uuid4()),
        'offer_id': offer_id,
        'offer_date': offer.get('offer_date'),
        'customer': offer.get('customer'),
        'customer_name': offer.get('customer_name'),
        'offer_constructor': offer.get('offer_constructor'),
        'username': offer.get('username'),
        'charge': str(offer.get('charge')) if offer.get('charge') is not None and offer.get('fpa') != "" else str(0),
        'discount': str(offer.get('discount')) if offer.get('discount') is not None and offer.get('fpa') != "" else str(0),
        'offer_amount': str(offer.get('offer_amount')) if offer.get('offer_amount') is not None and offer.get('offer_amount') != "" else str(0),
        'fpa': str(offer.get('fpa')) if offer.get('fpa') is not None and offer.get('fpa') != "" else str(0),
        'offer_to': offer.get('offer_to'),
        'info_el': offer.get('info_el'),
        'info_en': offer.get('info_en'),
        'info_it': offer.get('info_it'),
        'offer_fpa_amount': str(0),
        'offer_discount_amount': str(0)
        # 'costs': offer.get('costs'),
        # 'charges': offer.get('charges'),
    }
    if offer.get('costs'):
        costs_desc = []
        costs_amount = []
        for cost in offer.get('costs'):
            costs_desc.append(cost.get('desc'))
            costs_amount.append(str(cost.get('value')))
        item["costs_desc"] = costs_desc
        item["costs_amount"] = costs_amount

    # print(item)
    # print(item["costs_amount"])
    if offer.get('charges'):
        charges_desc = []
        charges_amount = []
        for charge in offer.get('charges'):
            charges_desc.append(charge.get('desc'))
            charges_amount.append(str(charge.get('value')))
        item["charges_desc"] = charges_desc
        item["charges_amount"] = charges_amount

    try:
        table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(offer_key)'
        )
        return func_resp(msg="offer Registered", data={"offer_key": str(item["offer_key"])}, status=200)
    except exceptions.ParamValidationError as error:
        print('The parameters you provided are incorrect: {}'.format(error))
        return func_resp(msg="Registration not completed due to parameter validation.", data=[], status=400)

    except exceptions.ClientError as e:
        print(f"Failed to register offer with error: {str(e.response.get('Error'))}")
        msg = e.response.get('Error', {"Message": None}).get('Message')
        if msg is None:
            msg = "Failed to register offer."
        else:
            msg = "offer_key does not exist"
        return func_resp(msg=msg, data=[], status=400)

    except:
        print(f"Tried to store item: {item}")
        return func_resp(msg="Registration not completed.", data=[], status=400)


def delete_offer(offer_key):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)
    # print(DYNAMODB_USERS_TABLE)
    try:
        table = client.Table(DYNAMODB_OFFERS_TABLE)
        response = table.delete_item(
            Key={
                'offer_key': offer_key
            }
        )
        # print(response)
        status_code = response['ResponseMetadata']['HTTPStatusCode']
        if status_code == 200:
            return func_resp(msg='offer Deleted.', data=[], status=200)
        else:
            return func_resp(msg=response['ResponseMetadata'], data=[], status=status_code)
    except:
        return func_resp(msg='Deletion Failed.', data=[], status=400)


def update_offer(offer_key, body):
    upEx = "set "
    last = False
    attValues = {}

    if body.get('offer_products_chars_amount') is not None:
        if last is True:
            upEx += ","
        upEx += " offer_products_chars_amount = :offer_products_chars_amount"
        attValues[":offer_products_chars_amount"] = str(body.get('offer_products_chars_amount'))
        last = True
    if body.get('offer_fpa_amount') is not None:
        if last is True:
            upEx += ","
        upEx += " offer_fpa_amount = :offer_fpa_amount"
        attValues[":offer_fpa_amount"] = str(body.get('offer_fpa_amount'))
        last = True
    if body.get('offer_discount_amount') is not None:
        if last is True:
            upEx += ","
        upEx += " offer_discount_amount = :offer_discount_amount"
        attValues[":offer_discount_amount"] = str(body.get('offer_discount_amount'))
        last = True
    if body.get('offer_id') is not None:
        if last is True:
            upEx += ","
        upEx += " offer_id = :offer_id"
        attValues[":offer_id"] = str(body.get('offer_id'))
        last = True
    if body.get('offer_date') is not None:
        if last is True:
            upEx += ","
        upEx += " offer_date = :offer_date"
        attValues[":offer_date"] = body.get('offer_date')
        last = True
    if body.get('customer') is not None:
        if last is True:
            upEx += ","
        upEx += " customer = :customer"
        attValues[":customer"] = body.get('customer')
        last = True
    if body.get('customer_name') is not None:
        if last is True:
            upEx += ","
        upEx += " customer_name = :customer_name"
        attValues[":customer_name"] = body.get('customer_name')
        last = True
    if body.get('offer_constructor') is not None:
        if last is True:
            upEx += ","
        upEx += " offer_constructor = :offer_constructor"
        attValues[":offer_constructor"] = body.get('offer_constructor')
        last = True
    if body.get('username') is not None:
        if last is True:
            upEx += ","
        upEx += " username = :username"
        attValues[":username"] = body.get('username')
        last = True
    if body.get('charge') is not None:
        if last is True:
            upEx += ","
        upEx += " charge = :charge"
        attValues[":charge"] = str(body.get('charge'))
        last = True
    if body.get('discount') is not None:
        if last is True:
            upEx += ","
        upEx += " discount = :discount"
        attValues[":discount"] = str(body.get('discount'))
        last = True
    if body.get('offer_amount') is not None:
        if last is True:
            upEx += ","
        upEx += " offer_amount = :offer_amount"
        attValues[":offer_amount"] = str(body.get('offer_amount'))
        last = True
    if body.get('fpa') is not None:
        if last is True:
            upEx += ","
        upEx += " fpa = :fpa"
        attValues[":fpa"] = str(body.get('fpa'))
        last = True
    if body.get('offer_to') is not None:
        # print(body.get('to'))
        if last is True:
            upEx += ","
        upEx += " offer_to = :offer_to"
        attValues[":offer_to"] = body.get('offer_to')
        last = True
        # print(upEx)
        # print(attValues)
    if body.get('info_el') is not None:
        if last is True:
            upEx += ","
        upEx += " info_el = :info_el"
        attValues[":info_el"] = body.get('info_el')
        last = True
    if body.get('info_en') is not None:
        if last is True:
            upEx += ","
        upEx += " info_en = :info_en"
        attValues[":info_en"] = body.get('info_en')
        last = True
    if body.get('info_it') is not None:
        if last is True:
            upEx += ","
        upEx += " info_it = :info_it"
        attValues[":info_it"] = body.get('info_it')
        last = True
    if body.get('costs') is not None:
        costs_desc = []
        costs_amount = []
        for cost in body.get('costs'):
            costs_desc.append(cost.get('desc'))
            costs_amount.append(str(cost.get('value')))
        if last is True:
            upEx += ","
        upEx += " costs_desc = :costs_desc"
        attValues[":costs_desc"] = costs_desc
        upEx += ","
        upEx += " costs_amount = :costs_amount"
        attValues[":costs_amount"] = costs_amount
        last = True
    if body.get('charges') is not None:
        charges_desc = []
        charges_amount = []
        for charge in body.get('charges'):
            charges_desc.append(charge.get('desc'))
            charges_amount.append(str(charge.get('value')))
        if last is True:
            upEx += ","
        upEx += " charges_desc = :charges_desc"
        attValues[":charges_desc"] = charges_desc
        upEx += ","
        upEx += " charges_amount = :charges_amount"
        attValues[":charges_amount"] = charges_amount
        last = True

    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    try:
        table = client.Table(DYNAMODB_OFFERS_TABLE)
        response = table.update_item(
            Key={
                'offer_key': offer_key
            },
            UpdateExpression=upEx,
            ExpressionAttributeValues=attValues
        )
        status_code = response['ResponseMetadata']['HTTPStatusCode']
        if status_code == 200:
            return func_resp(msg='offer Updated.', data=[], status=status_code)
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
def check_request_delete(headers, offer_key):
    if offer_key is None or offer_key == "":
        return func_resp(msg="offer_key was not given.", data=[], status=400)
    return func_resp(msg="", data=[], status=200)


# @token_required
def check_request_put(headers, offer_key, args):
    if args is None:
        return func_resp(msg="Please complete all required fields.", data=[], status=400)
    try:
        args = json.loads(args)
    except:
        return func_resp(msg="Request body is not valid json", data=[], status=400)

    if args is None:
        return func_resp(msg="Nothing send for update.", data=[], status=400)

    if offer_key is None or offer_key == "":
        return func_resp(msg="offer_key was not given.", data=[], status=400)

    # offer_name = args.get('offer_name')
    # img = args.get('img')
    # typology = args.get('typology')
    # typology_1 = args.get('typology_1')
    # typology_2 = args.get('typology_2')
    # typology_3 = args.get('typology_3')
    # typology_4 = args.get('typology_4')
    # typology_5 = args.get('typology_5')
    # typology_6 = args.get('typology_6')
    #
    # if all(item is None for item in [offer_name, img, typology, typology_1, typology_2, typology_5, typology_3, typology_4, typology_6]):
    #     return func_resp(msg='Please complete all required fields.', data=[], status=400)

    return func_resp(msg="", data=[], status=200)


# @token_required
def offer_related_methods(event, context):
    print(event)
    method = event.get("requestContext").get("http").get("method")
    # print(method)
    headers = event.get('headers')
    if method == "GET":
        if event.get("rawPath") == '/offers/id':
            offer_key = event.get("queryStringParameters", {'offer_key': None}).get("offer_key")
            if offer_key is not None and offer_key != "":
                status, msg, data = get_offer_by_id(headers, offer_key)
                return api_resp(msg=msg, data=data, status=status)
            return api_resp(msg="offer_key not specified", data=[], status=400)
        status, msg, data = get_all_offers(headers)
        return api_resp(msg=msg, data=data, status=status)

    if method == "POST":
        body = event.get("body")
        status, msg, data = check_request_post(headers, body)
        if status == 200:
            body = json.loads(body)
            status, msg, data = register_new_offer(body)
        return api_resp(msg=msg, data=data, status=status)

    elif method == "PUT":
        offer_key = event.get("queryStringParameters", {'offer_key': None}).get("offer_key")
        body = event.get("body")
        status, msg, data = check_request_put(headers, offer_key, body)
        if status == 200:
            body = json.loads(body)
            status, msg, data = update_offer(offer_key, body)
        return api_resp(msg=msg, data=data, status=status)

    elif method == "DELETE":
        offer_key = event.get("queryStringParameters", {'offer_key': None}).get("offer_key")
        status, msg, data = check_request_delete(headers, offer_key)
        if status == 200:
            status, msg, data = delete_offer(offer_key)
        return api_resp(msg=msg, data=data, status=status)

    else:
        return api_resp(msg="Not Allowed Method", data=[], status=400)


# if __name__ == "__main__":
#     check_request_post("a", "v")