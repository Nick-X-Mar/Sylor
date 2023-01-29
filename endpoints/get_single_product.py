import json
from authenticate.validate_response import func_resp
from databases.dbs import connect_to_dynamodb_resource
from config.config import DYNAMODB_PRODUCTS_TABLE
from endpoints.translations_helper import connect_ids_with_translations


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
