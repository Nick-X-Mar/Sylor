import json
import uuid
from botocore import exceptions
from authenticate.validate_response import func_resp, api_resp
from databases.dbs import connect_to_dynamodb_resource
from config.config import DYNAMODB_OFFERS_PRODUCT_TABLE, DYNAMODB_EXTRA_COSTINGS_TABLE, DYNAMODB_PRODUCTS_TABLE
from endpoints.get_single_product import get_product_by_id, get_products_by_id_list
from endpoints.translations_helper import connect_ids_with_translations
from boto3.dynamodb.conditions import Key, Attr


def get_all_offers(headers, offer_id, lang):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_OFFERS_PRODUCT_TABLE)
    if offer_id is not None:
        res = table.scan(FilterExpression=Attr('offer').eq(offer_id))
    else:
        res = table.scan()
    results = res['Items']
    # print("Results")
    # print(results)

    if results is not None and len(results) > 0:
        product_keys = []
        for item in results:
            product_keys.append((item.get('product')))

        unique_product_keys = list(set(product_keys))
        actual_products = []
        for unique_product_key in unique_product_keys:
            print(f"get more info for product {unique_product_key} and lang is {lang}")
            status, msg, data = get_product_by_id(headers=headers, product_key=unique_product_key, translation=False, lang=lang)
            if status == 200:
                for product in results:
                    if product.get("product") == unique_product_key:
                        actual_products.append(dict(product, **data))

                # # append edw pali ena ena
                # status, msg, data = get_products_by_id_list(headers, product_keys)
                # # print(data)
                #
                # if status == 200:
                #     actual_products = []
                #     for unique_product in data:  # uniques
                #         # print(unique_product)
                #         uKey = unique_product.get("product_key")
                #         for product in results:
                #             if uKey == product.get("product"):
                #                 # print("in")
                #                 actual_products.append(dict(product, **unique_product))
                #

        status, msg, data = connect_ids_with_translations(headers, actual_products, lang)
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
        return func_resp(msg=msg, data=data[0], status=status)


def get_extra_costings(headers, dynamodb, p_id, m2):
    # table = dynamodb.Table(DYNAMODB_PRODUCTS_TABLE)
    # print(f"product_id: {p_id}")
    status, msg, data = get_product_by_id(headers=headers, product_key=p_id, translation=False, lang='el')
    # print(msg)
    # print(m2)
    if status == 200:
        # print(f"data.get('product_name'): {data.get('product_name')}")
        # print(f"data.get('typology'): {data.get('typology')}")
        table = dynamodb.Table(DYNAMODB_EXTRA_COSTINGS_TABLE)
        results = table.scan(FilterExpression=(Attr('productId').eq(data.get('product_name')) and Attr('typologyId').eq(data.get('typology')) and Attr('typology_1').eq(data.get('typology_1'))))
        # print(results)
        results = results.get('Items')
        charge = 0
        charge_limit = 1000
        if results is not None and len(results) > 0:
            for res in results:
                # print(res)
                # print(m2 < float(res.get('m2_limit')))
                if m2 < float(res.get('m2_limit')):
                    # print(f'm2_limit: {res.get("m2_limit")} < charge_limit: {charge_limit}  ')
                    # print(float(res.get('m2_limit')) < charge_limit)
                    if float(res.get('m2_limit')) <= charge_limit:
                        charge_limit = float(res.get('m2_limit'))
                        charge = float(res.get('extra_cost'))
                        # print(charge)
        return charge
    else:
        return False


def register_new_offer_product(headers, offer_product, replicas=1):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    # todo: With the given product name(productId --> name) get of extra costings
    # find the extra costings for the placement for these typologies and add it to placement_h
    extra_cost = 0
    if offer_product.get('x') is not None and offer_product.get('y') is not None:
        extra_cost = get_extra_costings(headers, client, offer_product.get('product'), (float(offer_product.get('x')) * float(offer_product.get('y'))))
        print(extra_cost)
        if extra_cost is False:
            return func_resp(msg="Error during fetching", data=[], status=400)

    table = client.Table(DYNAMODB_OFFERS_PRODUCT_TABLE)
    item = {
        'extra_costing_m2': str(extra_cost),
        # 'offer_product_key': str(uuid.uuid4()),
        'offer': str(offer_product.get('offer')) if offer_product.get('offer') is not None else str(0),
        'product': str(offer_product.get('product')),
        'quantity': str(offer_product.get('quantity')) if offer_product.get('quantity') is not None else str(1),
        'x': str(offer_product.get('x')) if offer_product.get('x') is not None else str(0),
        'y': str(offer_product.get('y')) if offer_product.get('y') is not None else str(0),
        'z': str(offer_product.get('z')) if offer_product.get('z') is not None else str(0),
        # "set_time": str(offer_product.get("set_time")),
        'unit_amount': str(offer_product.get('unit_amount')) if offer_product.get('unit_amount') is not None else str(0),
        'offer_product_code': str(offer_product.get('offer_product_code')) if offer_product.get('offer_product_code') is not None else ""
    }
    if offer_product.get('unit_amount') is not None and offer_product.get('quantity') is not None:
        v = float(offer_product.get('unit_amount')) * int(offer_product.get('quantity'))
        item['total_amount'] = str(format(v, '.2f'))

    for iteration in range(replicas):
        item['offer_product_key'] = str(uuid.uuid4())
        try:
            table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(offer_product_key)'
            )

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

    return func_resp(msg="offer_product Registered", data=[], status=200)


def delete_offer(headers, offer_product_key):
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


def update_offer_product(headers, offer_product_key, body):
    total_char_amount = float(0)
    chars_affected = False
    quantity = None
    upEx = "set "
    last = False
    attValues = {}
    if body.get('total_unit_amount') is not None and body.get('total_unit_amount') != "":
        if last is True:
            upEx += ","
        upEx += " total_unit_amount = :total_unit_amount"
        attValues[":total_unit_amount"] = str(body.get('total_unit_amount'))
        last = True
    if body.get('extra_splitted_cost') is not None:
        if last is True:
            upEx += ","
        upEx += " extra_splitted_cost = :extra_splitted_cost"
        attValues[":extra_splitted_cost"] = str(body.get('extra_splitted_cost'))
        last = True
    if body.get('unit_amount') is not None and body.get('quantity') is not None:
        if last is True:
            upEx += ","
        upEx += " total_amount = :total_amount"
        v = float(body.get('unit_amount')) * int(body.get('quantity'))
        attValues[":total_amount"] = str(format(v, '.2f'))
        last = True
    if body.get('total_amount') is not None:
        if last is True:
            upEx += ","
        upEx += " total_amount = :total_amount"
        attValues[":total_amount"] = str(body.get('total_amount'))
        last = True
    if body.get('product') is not None:
        if last is True:
            upEx += ","
        upEx += " product = :product"
        attValues[":product"] = str(body.get('product'))
        last = True
    if body.get('quantity') is not None:
        if last is True:
            upEx += ","
        upEx += " quantity = :quantity"
        attValues[":quantity"] = str(body.get('quantity'))
        last = True
    else:
        status, msg, data = get_offer_by_id(headers=headers, offer_product_key=offer_product_key)
        if status == 200:
            quantity = data.get('quantity')
    if body.get('x') is not None:
        if last is True:
            upEx += ","
        upEx += " x = :x"
        attValues[":x"] = str(body.get('x'))
        last = True
    if body.get('y') is not None:
        if last is True:
            upEx += ","
        upEx += " y = :y"
        attValues[":y"] = str(body.get('y'))
        last = True
    if body.get('z') is not None:
        if last is True:
            upEx += ","
        upEx += " z = :z"
        attValues[":z"] = str(body.get('z'))
        last = True
    if body.get('unit_amount') is not None:
        if last is True:
            upEx += ","
        upEx += " unit_amount = :unit_amount"
        attValues[":unit_amount"] = str(body.get('unit_amount'))
        last = True
    if body.get('set_time') is not None:
        if last is True:
            upEx += ","
        upEx += " set_time = :set_time"
        attValues[":set_time"] = str(body.get('set_time'))
        last = True
    if body.get('offer_product_code') is not None:
        if last is True:
            upEx += ","
        upEx += " offer_product_code = :offer_product_code"
        attValues[":offer_product_code"] = str(body.get('offer_product_code'))
        last = True

    if body.get('extra_yalo_1') is not None:
        print(body.get('extra_yalo_1'))
        if last is True:
            upEx += ","
        upEx += " extra_yalo_1 = :extra_yalo_1"
        attValues[":extra_yalo_1"] = str(body.get('extra_yalo_1'))
        last = True
        if body.get('extra_yalo_1_amount') is not None:
            if last is True:
                upEx += ","
            upEx += " extra_yalo_1_amount = :extra_yalo_1_amount"
            if body.get('extra_yalo_1') != "":
                chars_affected = True
                total_char_amount += float(body.get('extra_yalo_1_amount'))
                attValues[":extra_yalo_1_amount"] = str(format(float(body.get('extra_yalo_1_amount')), '.2f'))
            else:
                attValues[":extra_yalo_1_amount"] = str(0)
            last = True
    if body.get('extra_yalo_2') is not None:
        if last is True:
            upEx += ","
        upEx += " extra_yalo_2 = :extra_yalo_2"
        attValues[":extra_yalo_2"] = str(body.get('extra_yalo_2'))
        last = True
        if body.get('extra_yalo_2_amount') is not None:
            if last is True:
                upEx += ","
            upEx += " extra_yalo_2_amount = :extra_yalo_2_amount"
            if body.get('extra_yalo_2') != "":
                chars_affected = True
                total_char_amount += float(body.get('extra_yalo_2_amount'))
                attValues[":extra_yalo_2_amount"] = str(format(float(body.get('extra_yalo_2_amount')), '.2f'))
            else:
                attValues[":extra_yalo_2_amount"] = str(0)
            last = True
    if body.get('extra_yalo_3') is not None:
        if last is True:
            upEx += ","
        upEx += " extra_yalo_3 = :extra_yalo_3"
        attValues[":extra_yalo_3"] = str(body.get('extra_yalo_3'))
        last = True
        if body.get('extra_yalo_3_amount') is not None:
            if last is True:
                upEx += ","
            upEx += " extra_yalo_3_amount = :extra_yalo_3_amount"
            if body.get('extra_yalo_3') != "":
                chars_affected = True
                total_char_amount += float(body.get('extra_yalo_3_amount'))
                attValues[":extra_yalo_3_amount"] = str(format(float(body.get('extra_yalo_3_amount')), '.2f'))
            else:
                attValues[":extra_yalo_3_amount"] = str(0)
            last = True
    if body.get('extra_yalo_4') is not None:
        if last is True:
            upEx += ","
        upEx += " extra_yalo_4 = :extra_yalo_4"
        attValues[":extra_yalo_4"] = str(body.get('extra_yalo_4'))
        last = True
        if body.get('extra_yalo_4_amount') is not None:
            if last is True:
                upEx += ","
            upEx += " extra_yalo_4_amount = :extra_yalo_4_amount"
            if body.get('extra_yalo_4') != "":
                chars_affected = True
                total_char_amount += float(body.get('extra_yalo_4_amount'))
                attValues[":extra_yalo_4_amount"] = str(format(float(body.get('extra_yalo_4_amount')), '.2f'))
            else:
                attValues[":extra_yalo_4_amount"] = str(0)
            last = True
    if body.get('extra_yalo_5') is not None:
        if last is True:
            upEx += ","
        upEx += " extra_yalo_5 = :extra_yalo_5"
        attValues[":extra_yalo_5"] = str(body.get('extra_yalo_5'))
        last = True
        if body.get('extra_yalo_5_amount') is not None:
            if last is True:
                upEx += ","
            upEx += " extra_yalo_5_amount = :extra_yalo_5_amount"
            if body.get('extra_yalo_5') != "":
                chars_affected = True
                total_char_amount += float(body.get('extra_yalo_5_amount'))
                attValues[":extra_yalo_5_amount"] = str(format(float(body.get('extra_yalo_5_amount')), '.2f'))
            else:
                attValues[":extra_yalo_5_amount"] = str(0)
            last = True
    if body.get('extra_yalo_6') is not None:
        if last is True:
            upEx += ","
        upEx += " extra_yalo_6 = :extra_yalo_6"
        attValues[":extra_yalo_6"] = str(body.get('extra_yalo_6'))
        last = True
        if body.get('extra_yalo_6_amount') is not None:
            if last is True:
                upEx += ","
            upEx += " extra_yalo_6_amount = :extra_yalo_6_amount"
            if body.get('extra_yalo_6') != "":
                chars_affected = True
                total_char_amount += float(body.get('extra_yalo_6_amount'))
                attValues[":extra_yalo_6_amount"] = str(format(float(body.get('extra_yalo_6_amount')), '.2f'))
            else:
                attValues[":extra_yalo_6_amount"] = str(0)
            last = True
    if body.get('extra_yalo_7') is not None:
        if last is True:
            upEx += ","
        upEx += " extra_yalo_7 = :extra_yalo_7"
        attValues[":extra_yalo_7"] = str(body.get('extra_yalo_7'))
        last = True
        if body.get('extra_yalo_7_amount') is not None:
            if last is True:
                upEx += ","
            upEx += " extra_yalo_7_amount = :extra_yalo_7_amount"
            if body.get('extra_yalo_7') != "":
                chars_affected = True
                total_char_amount += float(body.get('extra_yalo_7_amount'))
                attValues[":extra_yalo_7_amount"] = str(format(float(body.get('extra_yalo_7_amount')), '.2f'))
            else:
                attValues[":extra_yalo_7_amount"] = str(0)
            last = True
    if body.get('extra_yalo_8') is not None:
        if last is True:
            upEx += ","
        upEx += " extra_yalo_8 = :extra_yalo_8"
        attValues[":extra_yalo_8"] = str(body.get('extra_yalo_8'))
        last = True
        if body.get('extra_yalo_8_amount') is not None:
            if last is True:
                upEx += ","
            upEx += " extra_yalo_8_amount = :extra_yalo_8_amount"
            if body.get('extra_yalo_8') != "":
                chars_affected = True
                total_char_amount += float(body.get('extra_yalo_8_amount'))
                attValues[":extra_yalo_8_amount"] = str(format(float(body.get('extra_yalo_8_amount')), '.2f'))
            else:
                attValues[":extra_yalo_8_amount"] = str(0)
            last = True
    if body.get('extra_yalo_9') is not None:
        if last is True:
            upEx += ","
        upEx += " extra_yalo_9 = :extra_yalo_9"
        attValues[":extra_yalo_9"] = str(body.get('extra_yalo_9'))
        last = True
        if body.get('extra_yalo_9_amount') is not None:
            if last is True:
                upEx += ","
            upEx += " extra_yalo_9_amount = :extra_yalo_9_amount"
            if body.get('extra_yalo_9') != "":
                chars_affected = True
                total_char_amount += float(body.get('extra_yalo_9_amount'))
                attValues[":extra_yalo_9_amount"] = str(format(float(body.get('extra_yalo_9_amount')), '.2f'))
            else:
                attValues[":extra_yalo_9_amount"] = str(0)
            last = True
    if body.get('extra_yalo_10') is not None:
        if last is True:
            upEx += ","
        upEx += " extra_yalo_10 = :extra_yalo_10"
        attValues[":extra_yalo_10"] = str(body.get('extra_yalo_10'))
        last = True
        if body.get('extra_yalo_10_amount') is not None:
            if last is True:
                upEx += ","
            upEx += " extra_yalo_10_amount = :extra_yalo_10_amount"
            if body.get('extra_yalo_10') != "":
                chars_affected = True
                total_char_amount += float(body.get('extra_yalo_10_amount'))
                attValues[":extra_yalo_10_amount"] = str(format(float(body.get('extra_yalo_10_amount')), '.2f'))
            else:
                attValues[":extra_yalo_10_amount"] = str(0)
            last = True
    if body.get('extra_yalo_11') is not None:
        if last is True:
            upEx += ","
        upEx += " extra_yalo_11 = :extra_yalo_11"
        attValues[":extra_yalo_11"] = str(body.get('extra_yalo_11'))
        last = True
        if body.get('extra_yalo_11_amount') is not None:
            if last is True:
                upEx += ","
            upEx += " extra_yalo_11_amount = :extra_yalo_11_amount"
            if body.get('extra_yalo_11') != "":
                chars_affected = True
                total_char_amount += float(body.get('extra_yalo_11_amount'))
                attValues[":extra_yalo_11_amount"] = str(format(float(body.get('extra_yalo_11_amount')), '.2f'))
            else:
                attValues[":extra_yalo_11_amount"] = str(0)
            last = True
    if body.get('extra_yalo_12') is not None:
        if last is True:
            upEx += ","
        upEx += " extra_yalo_12 = :extra_yalo_12"
        attValues[":extra_yalo_12"] = str(body.get('extra_yalo_12'))
        last = True
        if body.get('extra_yalo_12_amount') is not None:
            if last is True:
                upEx += ","
            upEx += " extra_yalo_12_amount = :extra_yalo_12_amount"
            if body.get('extra_yalo_12') != "":
                chars_affected = True
                total_char_amount += float(body.get('extra_yalo_12_amount'))
                attValues[":extra_yalo_12_amount"] = str(format(float(body.get('extra_yalo_12_amount')), '.2f'))
            else:
                attValues[":extra_yalo_12_amount"] = str(0)
            last = True
    if body.get('extra_patzoy_1_1') is not None:
        if last is True:
            upEx += ","
        upEx += " extra_patzoy_1_1 = :extra_patzoy_1_1"
        attValues[":extra_patzoy_1_1"] = str(body.get('extra_patzoy_1_1'))
        last = True
        if body.get('extra_patzoy_1_1_amount') is not None:
            if last is True:
                upEx += ","
            upEx += " extra_patzoy_1_1_amount = :extra_patzoy_1_1_amount"
            if body.get('extra_patzoy_1_1') != "":
                chars_affected = True
                total_char_amount += float(body.get('extra_patzoy_1_1_amount'))
                attValues[":extra_patzoy_1_1_amount"] = str(format(float(body.get('extra_patzoy_1_1_amount')), '.2f'))
            else:
                attValues[":extra_patzoy_1_1_amount"] = str(0)
            last = True
    if body.get('extra_patzoy_1_2') is not None:
        if last is True:
            upEx += ","
        upEx += " extra_patzoy_1_2 = :extra_patzoy_1_2"
        attValues[":extra_patzoy_1_2"] = str(body.get('extra_patzoy_1_2'))
        last = True
        if body.get('extra_patzoy_1_2_amount') is not None:
            if last is True:
                upEx += ","
            upEx += " extra_patzoy_1_2_amount = :extra_patzoy_1_2_amount"
            if body.get('extra_patzoy_1_2') != "":
                chars_affected = True
                total_char_amount += float(body.get('extra_patzoy_1_2_amount'))
                attValues[":extra_patzoy_1_2_amount"] = str(format(float(body.get('extra_patzoy_1_2_amount')), '.2f'))
            else:
                attValues[":extra_patzoy_1_2_amount"] = str(0)
            last = True
    if body.get('extra_patzoy_2') is not None:
        if last is True:
            upEx += ","
        upEx += " extra_patzoy_2 = :extra_patzoy_2"
        attValues[":extra_patzoy_2"] = str(body.get('extra_patzoy_2'))
        last = True
        if body.get('extra_patzoy_2_amount') is not None:
            if last is True:
                upEx += ","
            upEx += " extra_patzoy_2_amount = :extra_patzoy_2_amount"
            if body.get('extra_patzoy_2') != "":
                chars_affected = True
                total_char_amount += float(body.get('extra_patzoy_2_amount'))
                attValues[":extra_patzoy_2_amount"] = str(format(float(body.get('extra_patzoy_2_amount')), '.2f'))
            else:
                attValues[":extra_patzoy_2_amount"] = str(0)
            last = True
    if body.get('extra_patzoy_3') is not None:
        if last is True:
            upEx += ","
        upEx += " extra_patzoy_3 = :extra_patzoy_3"
        attValues[":extra_patzoy_3"] = str(body.get('extra_patzoy_3'))
        last = True
        if body.get('extra_patzoy_3_amount') is not None:
            if last is True:
                upEx += ","
            upEx += " extra_patzoy_3_amount = :extra_patzoy_3_amount"
            if body.get('extra_patzoy_3') != "":
                chars_affected = True
                total_char_amount += float(body.get('extra_patzoy_3_amount'))
                attValues[":extra_patzoy_3_amount"] = str(format(float(body.get('extra_patzoy_3_amount')), '.2f'))
            else:
                attValues[":extra_patzoy_3_amount"] = str(0)
            last = True
    if body.get('extra_patzoy_4') is not None:
        if last is True:
            upEx += ","
        upEx += " extra_patzoy_4 = :extra_patzoy_4"
        attValues[":extra_patzoy_4"] = str(body.get('extra_patzoy_4'))
        last = True
        if body.get('extra_patzoy_4_amount') is not None:
            if last is True:
                upEx += ","
            upEx += " extra_patzoy_4_amount = :extra_patzoy_4_amount"
            if body.get('extra_patzoy_4') != "":
                chars_affected = True
                total_char_amount += float(body.get('extra_patzoy_4_amount'))
                attValues[":extra_patzoy_4_amount"] = str(format(float(body.get('extra_patzoy_4_amount')), '.2f'))
            else:
                attValues[":extra_patzoy_4_amount"] = str(0)
            last = True
    if body.get('extra_patzoy_5') is not None:
        if last is True:
            upEx += ","
        upEx += " extra_patzoy_5 = :extra_patzoy_5"
        attValues[":extra_patzoy_5"] = str(body.get('extra_patzoy_5'))
        last = True
        if body.get('extra_patzoy_5_amount') is not None:
            if last is True:
                upEx += ","
            upEx += " extra_patzoy_5_amount = :extra_patzoy_5_amount"
            if body.get('extra_patzoy_5') != "":
                chars_affected = True
                total_char_amount += float(body.get('extra_patzoy_5_amount'))
                attValues[":extra_patzoy_5_amount"] = str(format(float(body.get('extra_patzoy_5_amount')), '.2f'))
            else:
                attValues[":extra_patzoy_5_amount"] = str(0)
            last = True
    if body.get('extra_patzoy_6') is not None:
        if last is True:
            upEx += ","
        upEx += " extra_patzoy_6 = :extra_patzoy_6"
        attValues[":extra_patzoy_6"] = str(body.get('extra_patzoy_6'))
        last = True
        if body.get('extra_patzoy_6_amount') is not None:
            if last is True:
                upEx += ","
            upEx += " extra_patzoy_6_amount = :extra_patzoy_6_amount"
            if body.get('extra_patzoy_6') != "":
                chars_affected = True
                total_char_amount += float(body.get('extra_patzoy_6_amount'))
                attValues[":extra_patzoy_6_amount"] = str(format(float(body.get('extra_patzoy_6_amount')), '.2f'))
            else:
                attValues[":extra_patzoy_6_amount"] = str(0)
            last = True
    if body.get('extra_patzoy_7') is not None:
        if last is True:
            upEx += ","
        upEx += " extra_patzoy_7 = :extra_patzoy_7"
        attValues[":extra_patzoy_7"] = str(body.get('extra_patzoy_7'))
        last = True
        if body.get('extra_patzoy_7_amount') is not None:
            if last is True:
                upEx += ","
            upEx += " extra_patzoy_7_amount = :extra_patzoy_7_amount"
            if body.get('extra_patzoy_7') != "":
                chars_affected = True
                total_char_amount += float(body.get('extra_patzoy_7_amount'))
                attValues[":extra_patzoy_7_amount"] = str(format(float(body.get('extra_patzoy_7_amount')), '.2f'))
            else:
                attValues[":extra_patzoy_7_amount"] = str(0)
            last = True

    if chars_affected:
        if last is True:
            upEx += ","
        upEx += " total_char_amount = :total_char_amount"
        if quantity is not None:
            attValues[":total_char_amount"] = str(format(float(total_char_amount) * int(quantity), '.2f'))
        else:
            attValues[":total_char_amount"] = str(total_char_amount)
        last = True

    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    if body.get('x') is not None and body.get('x') != "None" and body.get('y') is not None and body.get('y') != "None":
        extra_cost = get_extra_costings(headers, client, body.get('product'), (float(body.get('x')) * float(body.get('y'))))
        # print(f"extra_cost: {extra_cost}")
        if extra_cost is False:
            return func_resp(msg="Error during fetching", data=[], status=400)

        # if body.get('extra_costing_m2') is not None:
        if last is True:
            upEx += ","
        upEx += " extra_costing_m2 = :extra_costing_m2"
        attValues[":extra_costing_m2"] = str(extra_cost)
            # last = True

    try:
        table = client.Table(DYNAMODB_OFFERS_PRODUCT_TABLE)
        response = table.update_item(
            Key={
                'offer_product_key': str(offer_product_key)
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

    product = args.get('product')
    print(product)
    if all(item is None for item in [product]):
        return func_resp(msg='Offer is a required field.', data=[], status=400)

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
def offers_product_related_methods(event, context):
    print(event)
    method = event.get("requestContext").get("http").get("method")
    # print(method)
    headers = event.get('headers')
    if method == "GET":
        if event.get("rawPath") == '/offers_product/id':
            offer_product_key = event.get("queryStringParameters", {'offer_product_key': None}).get("offer_product_key")
            if offer_product_key is not None and offer_product_key != "":
                status, msg, data = get_offer_by_id(headers, offer_product_key)
                return api_resp(msg=msg, data=data, status=status)
            return api_resp(msg="offer_product_key not specified", data=[], status=400)

        offer_id = event.get("queryStringParameters", {'offer_id': None}).get("offer_id")
        lang = event.get("queryStringParameters", {'lang': None}).get("lang")
        print(f"lang: {lang}")
        status, msg, data = get_all_offers(headers, offer_id, lang)
        print(data)
        return api_resp(msg=msg, data=data, status=status)

    if method == "POST":
        body = event.get("body")
        status, msg, data = check_request_post(headers, body)
        if status == 200:
            body = json.loads(body)
            status, msg, data = register_new_offer_product(headers, body)
        return api_resp(msg=msg, data=data, status=status)

    elif method == "PUT":
        offer_product_key = event.get("queryStringParameters", {'offer_product_key': None}).get("offer_product_key")
        body = event.get("body")
        status, msg, data = check_request_put(headers, offer_product_key, body)
        if status == 200:
            body = json.loads(body)
            status, msg, data = update_offer_product(headers, offer_product_key, body)
        return api_resp(msg=msg, data=data, status=status)

    elif method == "DELETE":
        offer_product_key = event.get("queryStringParameters", {'offer_product_key': None}).get("offer_product_key")
        status, msg, data = check_request_delete(headers, offer_product_key)
        if status == 200:
            status, msg, data = delete_offer(headers, offer_product_key)
        return api_resp(msg=msg, data=data, status=status)

    else:
        return api_resp(msg="Not Allowed Method", data=[], status=400)


# if __name__ == "__main__":
#     check_request_post("a", "v")
