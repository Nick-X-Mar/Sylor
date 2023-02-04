import json
from authenticate.validate_response import func_resp
from databases.dbs import connect_to_dynamodb_resource
from config.config import DYNAMODB_PRODUCTS_TABLE
from endpoints.translations_helper import connect_ids_with_translations
# from boto3.dynamodb.conditions import Key, Attr
# import boto3


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
        return func_resp(msg=msg, data=data[0], status=status)


def get_products_by_id_list(headers, product_keys):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    product_keys = list(set(product_keys))
    table = client.Table(DYNAMODB_PRODUCTS_TABLE)
    batch_keys = {
        table.name: {
            'Keys': [
            ]
        }
    }

    try:
        product_keys=  ['df4c6b7c-506b-4d42-b387-b400bc3ed300', '329c7269-ea12-4956-bf5f-ee048cced063', '60fdd279-00bd-4039-9fe1-ebe27818736b', '53897163-5ebd-4bf8-9bfd-80774c651115', '10ade620-03a4-4fb7-84fc-841fb9fa765f', '6b95d488-234a-410f-a567-a9ac57d428fb']
        for key in product_keys:
            batch_keys.get(table.name).get('Keys').append({"product_key": key})
        # print(batch_keys)
        response = client.batch_get_item(RequestItems=batch_keys)
        # print(".....")
        print(response.get('Responses').get(table.name))
        return func_resp(msg="", data=response.get('Responses').get(table.name), status=200)
    except:
        print(f"Failed to get products with keys {product_keys}")
        return func_resp(msg="Failed to retrieve products.", data=[], status=400)

    # except:
    #     data = json.dumps({
    #         "product_key": product_key
    #     })
    #     print(f"Error: Failed to retrieve product with data: {data}.")
    #     return func_resp(msg="Failed to retrieve product.", data=[], status=400)
    #
    # # print(response.get('Item'))
    # if response.get('Item') is None:
    #     return func_resp(msg=f"Product with product_key:{product_key} not found.", data=[], status=404)
    # else:
    #     status, msg, data = connect_ids_with_translations(headers, [response['Item']])
    #     return func_resp(msg=msg, data=data[0], status=status)
