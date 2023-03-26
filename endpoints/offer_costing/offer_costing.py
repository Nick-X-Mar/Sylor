import json
import uuid
from botocore import exceptions
from authenticate.validate_response import func_resp, api_resp
from config import config
from databases.dbs import connect_to_dynamodb_resource
from config.config import DYNAMODB_OFFER_COSTING_TABLE, DYNAMODB_OFFERS_PRODUCT_TABLE
from endpoints.get_single_product import get_product_by_id, get_products_by_id_list
# from endpoints.translations_helper import connect_ids_with_translations
from boto3.dynamodb.conditions import Key, Attr

from endpoints.offers_management.offers import get_offer_by_id, update_offer
from endpoints.offers_product_management.offers_product import update_offer_product
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
        return func_resp(msg='', data=results[0], status=200)
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


def calculate_transportation_out(products):
    products_setup = []
    # temp_products = products.copy()
    # print("check")
    # print(products)
    temp_products = []
    for op in products:
        try:
            num = int(op.get('quantity'))
        except:
            num = 1
        for i in range(num):
            temp_products.append(op)
    # print(temp_products)
    i = 0
    max_init_w = 0
    while len(temp_products) > 0:
        i += 1
        prod = []
        max_x = max(temp_products, key=lambda item: float(item['x']))
        max_y = max(temp_products, key=lambda item: float(item['y']))
        # print(max_x)
        # print(max_y)
        # if max(float(max_x.get('x')), float(max_y.get('y'))) > float(config.MAX_WIDTH):
        if float(max_x.get('x')) > float(max_y.get('y')):
            max_w = float(max_x.get('x'))
            prod.append(max_x)
            temp_products.remove(max_x)
        else:
            max_w = float(max_y.get('y'))
            prod.append(max_y)
            temp_products.remove(max_y)
        if i == 1:
            max_init_w = max_w
        else:
            if len(temp_products) == 0:
                pass
            else:
                print(i)
                min_x = float(min(temp_products, key=lambda item: float(item['x'])).get('x'))
                min_y = float(min(temp_products, key=lambda item: float(item['y'])).get('y'))
                distance_left = max_init_w - max_w
                flag = True

                p_dist_left = 100000
                while distance_left > min(min_x, min_y) and flag is True:
                    print(f"Loop {i} p_min_dist: {distance_left} > {min(min_x, min_y)}")
                    current_prod = {}
                    for p in temp_products:
                        p_x = float(p.get('x'))
                        p_y = float(p.get('y'))
                        if p_x < p_y:
                            if distance_left >= p_x:
                                if distance_left - p_x < p_dist_left:
                                    p_dist_left = distance_left - p_x
                                    current_prod = p

                        else:
                            if distance_left >= p_y:
                                if distance_left - p_y < p_dist_left:
                                    p_dist_left = distance_left - p_y
                                    current_prod = p

                    if current_prod == {}:
                        flag = False
                    else:
                        temp_products.remove(current_prod)
                        prod.append(current_prod)

        products_setup.append(prod)
    print("Products Setup")
    print(products_setup)
    total_z = 0
    for row in products_setup:
        max_row_z = 0
        for p in row:
            if float(p.get('z')) > max_row_z:
                max_row_z = float(p.get('z'))
        total_z += max_row_z
    # print(total_z)
    return str(((max_init_w / 1000) * (total_z / 1000)) * float(config.PALETE_COST))


def combine_grouped_products(grouped_products):
    # print("aaaaa")
    # print(grouped_products)
    copy_dict = grouped_products.copy()
    for k, v in copy_dict.items():
        if k in config.PRODUCTS_CAT_YALO:
            if grouped_products.get("cat_yalo") is None:
                # print(grouped_products["cat_yalo"])
                grouped_products["cat_yalo"] = v
                print(grouped_products["cat_yalo"])
            else:
                print(grouped_products["cat_yalo"])
                grouped_products["cat_yalo"]["number_of_products"] = int(grouped_products["cat_yalo"]["number_of_products"]) + int(v["number_of_products"])
                grouped_products["cat_yalo"]["total_price"] = (float(grouped_products["cat_yalo"].get("total_price")) if grouped_products["cat_yalo"].get("total_price") is not None else 0) + float(v["total_price"]) if v.get("total_price") is not None else 0
                print(grouped_products["cat_yalo"])
        elif k in config.PRODUCTS_CAT_PATZ:
            if grouped_products.get("cat_patz") is None:
                grouped_products["cat_patz"] = v
            else:
                grouped_products["cat_patz"]["number_of_products"] = int(grouped_products["cat_patz"]["number_of_products"]) + int(v["number_of_products"])
                grouped_products["cat_patz"]["total_price"] = (float(grouped_products["cat_patz"].get("total_price")) if grouped_products["cat_patz"].get("total_price") is not None else 0) + float(v["total_price"]) if v.get("total_price") is not None else 0

        elif k in config.PRODUCTS_CAT_EJO:
            if grouped_products.get("cat_ejo") is None:
                grouped_products["cat_ejo"] = v
            else:
                grouped_products["cat_ejo"]["number_of_products"] = int(grouped_products["cat_ejo"]["number_of_products"]) + int(v["number_of_products"])
                grouped_products["cat_ejo"]["total_price"] = (float(grouped_products["cat_ejo"].get("total_price")) if grouped_products["cat_ejo"].get("total_price") is not None else 0) + float(v["total_price"]) if v.get("total_price") is not None else 0

        elif k in config.PRODUCTS_CAT_ROLO:
            if grouped_products.get("cat_rolo") is None:
                grouped_products["cat_rolo"] = v
            else:
                grouped_products["cat_rolo"]["number_of_products"] = int(grouped_products["cat_rolo"]["number_of_products"]) + int(v["number_of_products"])
                grouped_products["cat_rolo"]["total_price"] = (float(grouped_products["cat_rolo"].get("total_price")) if grouped_products["cat_rolo"].get("total_price") is not None else 0) + float(v["total_price"]) if v.get("total_price") is not None else 0
    return grouped_products


# if __name__ == '__main__' :
#     combine_grouped_products({'553996cf-ec8a-43aa-840d-ebe366f964b0': {'number_of_products': '1', 'units_placement': '3.2', 'extra_time_needed': '0.0', 'total_time': '3.2'}, 'total_days_needed': 12.8, '0a4f6648-1831-44e5-902d-83b02e5be497': {'number_of_products': '2', 'units_placement': '6.4', 'extra_time_needed': '0.0', 'total_time': '6.4'}, 'a36de552-c85f-4c59-8b36-1614462c24fd': {'number_of_products': '2', 'units_placement': '0.0', 'extra_time_needed': '0.0', 'total_time': '0.0'}, '59210467-e38e-4f10-aae8-df41441c6e64': {'number_of_products': '1', 'units_placement': '3.2', 'extra_time_needed': '0.0', 'total_time': '3.2'}, 'transportation_out': '219.6', 'total_products': '6'})


def get_days_costing_for_offerproducts(headers, dynamodb, offer_id):
    # translations_table = dynamodb.Table(DYNAMODB_OFFERS_PRODUCT_TABLE)
    status, msg, translations = get_all_translations(headers)
    if status != 200:
        return "Error fetching translations"

    # print(f'offer_id {offer_id}')
    total_days_needed = 0
    grouped_products = {}
    total_products = 0
    offer_product_table = dynamodb.Table(DYNAMODB_OFFERS_PRODUCT_TABLE)
    results = offer_product_table.scan(FilterExpression=Attr('offer').eq(offer_id)).get('Items')
    # print(f"Len products {len(results)}")
    if results is not None and len(results) > 0:
        transportation_out = calculate_transportation_out(results)
        for offer_product in results:
            # print(f"offer_product: {offer_product}")

            status, msg, product = get_product_by_id(headers=headers, product_key=offer_product.get('product'),
                                                     translation=False, lang='el')
            # print(f'Init --> status: {status}')
            # print(f'Init --> product: {product}')
            if status == 200:
                # print(f"offer_product: {offer_product}")
                # print(f"product: {product}")
                if offer_product.get('quantity') is not None and offer_product.get('quantity') != 'None':
                    number_of_products_added = int(offer_product.get('quantity'))
                else:
                    number_of_products_added = 1
                total_products += number_of_products_added
                # print(f"offer_product.get('extra_costing_m2'): {offer_product.get('extra_costing_m2')}")
                if offer_product.get('extra_costing_m2') is not None and offer_product.get(
                        'extra_costing_m2') != 'None':
                    extra_time_needed = float(offer_product.get('extra_costing_m2')) * number_of_products_added
                else:
                    extra_time_needed = 0
                if product.get('placement_h') is not None and offer_product.get('placement_h') != 'None':
                    units_placement = float(product.get('placement_h')) * number_of_products_added
                else:
                    units_placement = 0
                total_days_needed += extra_time_needed + units_placement
                # if offer_product.get('product') == "a289f610-4b9e-45f6-9f87-f53f86b7ce3a":
                #     print("aaaaaa")
                #     print(grouped_products.get((product.get('product_name'))))

                if grouped_products.get((product.get('product_name'))) is None:
                    grouped_products[product.get('product_name')] = {
                        "number_of_products": str(number_of_products_added),
                        "units_placement": str(units_placement),
                        "extra_time_needed": str(extra_time_needed),
                        "total_time": str(float(extra_time_needed) + float(units_placement))
                    }
                else:
                    # if offer_product.get('product') == "a289f610-4b9e-45f6-9f87-f53f86b7ce3a":
                    #     print("22222")
                    #     print(int(grouped_products.get(product.get('product_name')).get('number_of_products')))
                    #     print(number_of_products_added)
                    #     print(str(int(grouped_products.get(product.get('product_name')).get('number_of_products')) + number_of_products_added))
                    #     print(grouped_products[product.get('product_name')])
                    grouped_products[product.get('product_name')] = {
                        "number_of_products": str(int(grouped_products.get(product.get('product_name')).get(
                            'number_of_products')) + number_of_products_added),
                        "units_placement": str(float(grouped_products.get(product.get('product_name')).get(
                            'units_placement')) + units_placement),
                        "extra_time_needed": str(float(grouped_products.get(product.get('product_name')).get(
                            'extra_time_needed')) + extra_time_needed),
                        "total_time": str(
                            float(grouped_products.get(product.get('product_name')).get('total_time')) + float(
                                extra_time_needed) + float(units_placement))
                    }
                    # print(grouped_products[product.get('product_name')])
                grouped_products['total_days_needed'] = total_days_needed
        grouped_products['transportation_out'] = str(transportation_out)
        grouped_products['total_products'] = str(total_products)
        return grouped_products
    return "Error with offer products table"


def register_new_offer_costing(headers, args):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    grouped_products = get_days_costing_for_offerproducts(headers, client, str(args.get('offer')))
    # print(grouped_products)
    if isinstance(grouped_products, str):
        return func_resp(msg=grouped_products, data=[], status=400)

    table = client.Table(DYNAMODB_OFFER_COSTING_TABLE)

    # area = args.get("area").upper()
    # area_dist = 1
    # if area == "AREA_1":
    #     area_dist = config.AREA_1
    # elif area == "AREA_2":
    #     area_dist = config.AREA_2
    # elif area == "AREA_3":
    #     area_dist = config.AREA_3
    # elif area == "AREA_4":
    #     area_dist = config.AREA_4
    # elif area == "AREA_5":
    #     area_dist = config.AREA_5
    # str(format(float(float(area_dist) * int(args.get("people")) * float(config.WORK_HOUR_COST) + int(grouped_products.get('total_days_needed'))), '.2f'))
    item = {
        'offer_costing_id': str(uuid.uuid4()),
        'trip_amount': str(format(float(
            float(args.get("area")) * int(args.get("people")) * float(config.WORK_HOUR_COST) + float(
                grouped_products.get('total_days_needed')) * float(config.WORK_HOUR_COST)), '.2f')),
        'area': str(args.get("area")),
        'people': str(args.get("people")),
        'per_product_amount': str(
            format(float(config.PER_PRODUCT_COST) * float(grouped_products.get('total_products')), '.2f')),
        'offer': str(args.get('offer')),
        'transportation_out': str(format(float(grouped_products['transportation_out']), '.2f')),
        'grouped_products': json.dumps(grouped_products),
        'trip_amount_actual': str(0),
        'transportation_in_actual': str(0),
        'transportation_out_actual': str(0),
        'per_product_amount_actual': str(0),
    }
    try:
        table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(offer_costing_id)'
        )
        return func_resp(msg="offer_costing Registered", data={
            "offer_costing_id": item['offer_costing_id'],
            "trip_amount": item.get('trip_amount'),
            "per_product_amount": item.get('per_product_amount'),
            "transportation_out": item.get('transportation_out')
        }, status=200)
    except exceptions.ParamValidationError as error:
        print('The parameters you provided are incorrect: {}'.format(error))
        return func_resp(msg="Registration not completed.", data=[], status=400)
    except:
        return func_resp(msg="Registration not completed.", data=[], status=400)

    # return func_resp(msg="Registration not completed.", data=[], status=400)


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


def combine_grouped_chars(grouped_chars):
    # CHARS_CAT_SITA = ["extra_yalo_2", "extra_patzoy_2"]
    # CHARS_CAT_MECH = ["extra_yalo_4", "extra_patzoy_3"]
    # CHARS_CAT_KAITIA = ["extra_yalo_8", "extra_patzoy_4"]
    # CHARS_CAT_TAMP = ["extra_yalo_9", "extra_patzoy_5"]
    # CHARS_CAT_COLOR = ["extra_yalo_10", "extra_patzoy_6"]
    # CHARS_CAT_WOOD = ["extra_yalo_11", "extra_patzoy_7"]

    copy_dict = grouped_chars.copy()
    for k, v in copy_dict.items():

        if k in config.CHARS_CAT_METAL_PARTS:
            if grouped_chars.get("cat_metal_parts") is None:
                grouped_chars["cat_metal_parts"] = v
                grouped_chars.pop(k)
            else:
                grouped_chars["cat_metal_parts"]["number_of_products"] = int(grouped_chars["cat_metal_parts"]["number_of_products"]) + int(v["number_of_products"])
                grouped_chars["cat_metal_parts"]["total_price"] = (float(grouped_chars["cat_metal_parts"].get("total_price")) if grouped_chars["cat_metal_parts"].get("total_price") is not None else 0) + float(v["total_price"]) if v.get("total_price") is not None else 0
                grouped_chars.pop(k)

        if k in config.CHARS_CAT_SITA:
            if grouped_chars.get("cat_sita") is None:
                grouped_chars["cat_sita"] = v
                grouped_chars.pop(k)
            else:
                grouped_chars["cat_sita"]["number_of_products"] = int(grouped_chars["cat_sita"]["number_of_products"]) + int(v["number_of_products"])
                grouped_chars["cat_sita"]["total_price"] = (float(grouped_chars["cat_sita"].get("total_price")) if grouped_chars["cat_sita"].get("total_price") is not None else 0) + float(v["total_price"]) if v.get("total_price") is not None else 0
                grouped_chars.pop(k)

        elif k in config.CHARS_CAT_MECH:
            if grouped_chars.get("cat_mech") is None:
                grouped_chars["cat_mech"] = v
                grouped_chars.pop(k)
            else:
                grouped_chars["cat_mech"]["number_of_products"] = int(grouped_chars["cat_mech"]["number_of_products"]) + int(v["number_of_products"])
                grouped_chars["cat_mech"]["total_price"] = (float(grouped_chars["cat_mech"].get("total_price")) if grouped_chars["cat_mech"].get("total_price") is not None else 0) + float(v["total_price"]) if v.get("total_price") is not None else 0
                grouped_chars.pop(k)

        elif k in config.CHARS_CAT_KAITIA:
            if grouped_chars.get("cat_kaitia") is None:
                grouped_chars["cat_kaitia"] = v
                grouped_chars.pop(k)
            else:
                grouped_chars["cat_kaitia"]["number_of_products"] = int(grouped_chars["cat_kaitia"]["number_of_products"]) + int(v["number_of_products"])
                grouped_chars["cat_kaitia"]["total_price"] = (float(grouped_chars["cat_kaitia"].get("total_price")) if grouped_chars["cat_kaitia"].get("total_price") is not None else 0) + float(v["total_price"]) if v.get("total_price") is not None else 0
                grouped_chars.pop(k)

        elif k in config.CHARS_CAT_TAMP:
            if grouped_chars.get("cat_tamp") is None:
                grouped_chars["cat_tamp"] = v
                grouped_chars.pop(k)
            else:
                grouped_chars["cat_tamp"]["number_of_products"] = int(grouped_chars["cat_tamp"]["number_of_products"]) + int(v["number_of_products"])
                grouped_chars["cat_tamp"]["total_price"] = (float(grouped_chars["cat_tamp"].get("total_price")) if grouped_chars["cat_tamp"].get("total_price") is not None else 0) + float(v["total_price"]) if v.get("total_price") is not None else 0
                grouped_chars.pop(k)

        elif k in config.CHARS_CAT_COLOR:
            if grouped_chars.get("cat_color") is None:
                grouped_chars["cat_color"] = v
                grouped_chars.pop(k)
            else:
                grouped_chars["cat_color"]["number_of_products"] = int(
                    grouped_chars["cat_color"]["number_of_products"]) + int(v["number_of_products"])
                grouped_chars["cat_color"]["total_price"] = (float(grouped_chars["cat_color"].get("total_price")) if \
                grouped_chars["cat_color"].get("total_price") is not None else 0) + float(v["total_price"]) if v.get(
                    "total_price") is not None else 0
                grouped_chars.pop(k)

        elif k in config.CHARS_CAT_WOOD:
            if grouped_chars.get("cat_wood") is None:
                grouped_chars["cat_wood"] = v
                grouped_chars.pop(k)
            else:
                grouped_chars["cat_wood"]["number_of_products"] = int(
                    grouped_chars["cat_wood"]["number_of_products"]) + int(v["number_of_products"])
                grouped_chars["cat_wood"]["total_price"] = (float(grouped_chars["cat_wood"].get("total_price")) if \
                    grouped_chars["cat_wood"].get("total_price") is not None else 0) + float(v["total_price"]) if v.get(
                    "total_price") is not None else 0
                grouped_chars.pop(k)

    return grouped_chars


def affect_products_with_offer_costing_charges(headers, dynamodb, offer, grouped_products, body):
    status, msg, offer_data = get_offer_by_id(headers, offer)
    if status != 200:
        return func_resp(msg=msg, data=[], status=status)

    offer_amount = 0
    charges_am = offer_data.get('charges_amount') if offer_data.get('charges_amount') is not None else [0]
    costs_am = offer_data.get('costs_amount') if offer_data.get('costs_amount') is not None else [0]
    total_charge_cost_amount = 0
    for i in charges_am:
        try:
            i = float(i)
        except:
            i = 0
        total_charge_cost_amount = total_charge_cost_amount + i

    for i in costs_am:
        try:
            i = float(i)
        except:
            i = 0
        total_charge_cost_amount = total_charge_cost_amount + i

    charge = 1 + float(offer_data.get("charge")) / 100 if offer_data.get("charge") is not None and offer_data.get(
        "charge") != "None" else 1.00

    charges_lists = [
        "crew_cost_list",
        "epimetrisi_list",
        "extra_cost_list",
        "per_product_amount_list",
        "transportation_in_list",
        "transportation_out_list",
        "trip_amount_list"
    ]
    lists = {}
    offer_product_charges = {}
    offer_product_old_charges = {}
    offer_product_old_total_amount = {}
    offer_product_old_unit_amount = {}
    offer_product_quantity = {}
    for cl in charges_lists:
        total_prods = 0
        if body.get(cl) is None or body.get(cl) == []:
            lists[cl] = 0
        else:
            # print(body.get(cl))
            for product_name in body.get(cl):
                if grouped_products.get(product_name) is not None:
                    total_prods += int(
                        grouped_products.get(product_name).get('number_of_products')) if grouped_products.get(
                        product_name).get('number_of_products') is not None else 0
            lists[cl] = total_prods
    print("Lists")
    print(lists)
    offer_product_table = dynamodb.Table(DYNAMODB_OFFERS_PRODUCT_TABLE)
    results = offer_product_table.scan(FilterExpression=Attr('offer').eq(offer)).get('Items')
    # print(f"Len products {len(results)}")
    grouped_chars = {
        "extra_patzoy_1_1": {
            "number_of_products": 0,
            "total_price": "0.00"
        },
        "extra_patzoy_1_2": {
            "number_of_products": 0,
            "total_price": "0.00"
        },
        "extra_patzoy_2": {
            "number_of_products": 0,
            "total_price": "0.00"
        },
        "extra_patzoy_3": {
            "number_of_products": 0,
            "total_price": "0.00"
        },
        "extra_patzoy_4": {
            "number_of_products": 0,
            "total_price": "0.00"
        },
        "extra_patzoy_5": {
            "number_of_products": 0,
            "total_price": "0.00"
        },
        "extra_patzoy_6": {
            "number_of_products": 0,
            "total_price": "0.00"
        },
        "extra_patzoy_7": {
            "number_of_products": 0,
            "total_price": "0.00"
        },
        "extra_yalo_1": {
            "number_of_products": 0,
            "total_price": "0.00"
        },
        "extra_yalo_2": {
            "number_of_products": 0,
            "total_price": "0.00"
        },
        "extra_yalo_3": {
            "number_of_products": 0,
            "total_price": "0.00"
        },
        "extra_yalo_4": {
            "number_of_products": 0,
            "total_price": "0.00"
        },
        "extra_yalo_5": {
            "number_of_products": 0,
            "total_price": "0.00"
        },
        "extra_yalo_6": {
            "number_of_products": 0,
            "total_price": "0.00"
        },
        "extra_yalo_7": {
            "number_of_products": 0,
            "total_price": "0.00"
        },
        "extra_yalo_8": {
            "number_of_products": 0,
            "total_price": "0.00"
        },
        "extra_yalo_9": {
            "number_of_products": 0,
            "total_price": "0.00"
        },
        "extra_yalo_10": {
            "number_of_products": 0,
            "total_price": "0.00"
        },
        "extra_yalo_11": {
            "number_of_products": 0,
            "total_price": "0.00"
        },
        "extra_yalo_12": {
            "number_of_products": 0,
            "total_price": "0.00"
        }
    }
    offer_products_chars_amount = 0
    offer_product_body = {}
    if results is not None and len(results) > 0:
        for offer_product in results:
            last_charge_percentage = float(offer_product.get("last_charge")) if offer_product.get(
                "last_charge") is not None else 1.00
            print(f"offer_product.get('last_charge'): {offer_product.get('last_charge')}")
            print(f"last_charge_percentage: {last_charge_percentage}")
            print(f"charge: {charge}")
            offer_product_body["last_charge"] = charge
            items = int(offer_product.get("quantity")) if offer_product.get("quantity") is not None else 1
            if offer_product.get("extra_patzoy_1_1_amount") is not None and offer_product.get("extra_patzoy_1_1") is not None and offer_product.get(f"extra_patzoy_1_1") != "":
                try:
                    am = (float(offer_product.get("extra_patzoy_1_1_amount")) / last_charge_percentage) * charge
                    offer_products_chars_amount += am * items
                    grouped_chars["extra_patzoy_1_1"]["total_price"] = str(float(grouped_chars["extra_patzoy_1_1"]["total_price"] if grouped_chars["extra_patzoy_1_1"]["total_price"] is not None else 0) + am * items)
                    grouped_chars["extra_patzoy_1_1"]["number_of_products"] = int(grouped_chars["extra_patzoy_1_1"]["number_of_products"]) + items
                    offer_product_body["extra_patzoy_1_1_amount"] = am
                    offer_product_body["extra_patzoy_1_1"] = offer_product.get("extra_patzoy_1_1")
                except Exception as e:
                    print(e)

            if offer_product.get("extra_patzoy_1_2_amount") is not None and offer_product.get("extra_patzoy_1_2") is not None and offer_product.get(f"extra_patzoy_1_2") != "":
                try:
                    am = (float(offer_product.get("extra_patzoy_1_2_amount")) / last_charge_percentage) * charge
                    offer_products_chars_amount += am * items
                    grouped_chars["extra_patzoy_1_2"]["total_price"] = str(float(grouped_chars["extra_patzoy_1_2"]["total_price"] if grouped_chars["extra_patzoy_1_2"]["total_price"] is not None else 0) + am * items)
                    grouped_chars["extra_patzoy_1_2"]["number_of_products"] = int(grouped_chars["extra_patzoy_1_2"]["number_of_products"]) + items
                    offer_product_body["extra_patzoy_1_2_amount"] = am
                    offer_product_body["extra_patzoy_1_2"] = offer_product.get("extra_patzoy_1_2")
                except Exception as e:
                    print(e)

            for i in range(12):  # 0 11
                try:
                    am = float((float(offer_product.get(f"extra_yalo_{i + 1}_amount")) / last_charge_percentage) * charge)
                    offer_products_chars_amount += am * items
                    if grouped_chars.get(f"extra_yalo_{i + 1}") is not None and (offer_product.get(f"extra_yalo_{i + 1}") is not None and offer_product.get(f"extra_yalo_{i + 1}") != ""):
                        grouped_chars[f"extra_yalo_{i + 1}"]["total_price"] = str(float(grouped_chars[f"extra_yalo_{i + 1}"]["total_price"] if grouped_chars[f"extra_yalo_{i + 1}"]["total_price"] is not None else 0) + am * items)
                        grouped_chars[f"extra_yalo_{i + 1}"]["number_of_products"] = int(grouped_chars[f"extra_yalo_{i + 1}"]["number_of_products"]) + items
                        offer_product_body[f"extra_yalo_{i + 1}_amount"] = am
                        offer_product_body[f"extra_yalo_{i + 1}"] = offer_product.get(f"extra_yalo_{i + 1}")

                    if grouped_chars.get(f"extra_patzoy_{i + 1}") is not None and offer_product.get(f"extra_patzoy_{i + 1}") is not None and offer_product.get(f"extra_patzoy_{i + 1}") != "":
                        am = float((float(offer_product.get(f"extra_patzoy_{i + 1}_amount")) / last_charge_percentage) * charge)
                        offer_products_chars_amount += am * items
                        grouped_chars[f"extra_patzoy_{i + 1}"]["total_price"] = str(float(grouped_chars[f"extra_patzoy_{i + 1}"]["total_price"] if grouped_chars[f"extra_patzoy_{i + 1}"]["total_price"] is not None else 0) + am * items)
                        grouped_chars[f"extra_patzoy_{i + 1}"]["number_of_products"] = int(grouped_chars[f"extra_patzoy_{i + 1}"]["number_of_products"]) + items
                        offer_product_body[f"extra_patzoy_{i + 1}_amount"] = am
                        offer_product_body[f"extra_patzoy_{i + 1}"] = offer_product.get(f"extra_patzoy_{i + 1}")
                except Exception as e:
                    print(e)

            status1, msg1, data1 = update_offer_product(headers, offer_product.get('offer_product_key'), offer_product_body)
            if status1 != 200:
                return func_resp(msg=msg1, data=[], status=status1)

            status, msg, product = get_product_by_id(headers=headers, product_key=offer_product.get('product'),
                                                     translation=False, lang='el')
            print(product.get('product_name'))
            print(status)
            print(msg)
            if status == 200:
                extra_charged_product_found = False
                for cl in charges_lists:
                    # print(f"cl: {cl}")
                    # print(body.get(cl))
                    if body.get(cl) is not None and isinstance(body.get(cl), list):
                        # print("in")
                        # if product.get('product_name') == "a36de552-c85f-4c59-8b36-1614462c24fd":
                        #     print("aaaa")
                        #     print(body.get(cl))
                        #     print(product.get('product_name') in body.get(cl))
                        if product.get('product_name') in body.get(cl):
                            extra_charged_product_found = True
                            print(
                                f"Product {product.get('product_name')} in {cl} is {product.get('product_name') in body.get(cl)}")
                            print(f"{cl} cost is : {body.get(cl[:-5])}")
                            print(f"Splitting among {lists[cl]} products")
                            print(
                                f"check if value exists {offer_product_charges.get(offer_product.get('offer_product_key'))}")
                            if offer_product_charges.get(offer_product.get('offer_product_key')) is None:
                                val = 0
                            else:
                                val = float(offer_product_charges.get(offer_product.get('offer_product_key')))
                            print(f"body.get(cl[:-5]): {body.get(cl[:-5])}")
                            print(f":lists.get(cl) {lists.get(cl)}")
                            print(f"body.get(cl[:-5] + '_actual': {body.get(cl[:-5] + '_actual')}")
                            offer_product_charges[offer_product.get('offer_product_key')] = str(
                                val + float(body.get(cl[:-5])) / lists.get(cl)) if body.get(
                                cl[:-5]) is not None and lists.get(cl) is not None else 0
                            if body.get(cl[:-5] + "_actual") is not None and body.get(
                                    cl[:-5] + "_actual") != 0 and body.get(cl[:-5] + "_actual") != "0":
                                offer_product_charges[offer_product.get('offer_product_key')] = str(
                                    val + float(body.get(cl[:-5] + "_actual")) / lists.get(cl)) if body.get(
                                    cl[:-5] + "_actual") is not None and lists.get(cl) is not None else 0
                            offer_product_old_charges[offer_product.get('offer_product_key')] = offer_product.get(
                                'extra_splitted_cost') if offer_product.get(
                                'extra_splitted_cost') is not None and offer_product.get(
                                'extra_splitted_cost') != "None" else 0
                            offer_product_old_total_amount[offer_product.get('offer_product_key')] = offer_product.get(
                                'total_amount') if offer_product.get('total_amount') is not None and offer_product.get(
                                'total_amount') != "None" else 0
                            offer_product_old_unit_amount[offer_product.get('offer_product_key')] = offer_product.get(
                                'unit_amount') if offer_product.get('unit_amount') is not None and offer_product.get(
                                'unit_amount') != "None" else 0
                            offer_product_quantity[offer_product.get('offer_product_key')] = offer_product.get(
                                'quantity') if offer_product.get('quantity') is not None and offer_product.get(
                                'quantity') != "None" else 0
                            print(
                                f"for each product + {offer_product_charges[offer_product.get('offer_product_key')]} euros")

                            if product.get('product_name') in grouped_products:
                                total_u_amount = (float(
                                    offer_product_old_unit_amount.get(offer_product.get('offer_product_key'))) + float(
                                    offer_product_charges[offer_product.get('offer_product_key')])) * charge
                                total_amount = str(format(float(offer_product.get('quantity')) * total_u_amount,
                                                          '.2f')) if offer_product.get('quantity') is not None else str(
                                    format(float(total_u_amount), '.2f'))
                                if grouped_products[product.get('product_name')].get("total_price") is None:
                                    grouped_products[product.get('product_name')]["total_price"] = total_amount
                                else:
                                    grouped_products[product.get('product_name')]["total_price"] = str(format(
                                        float(grouped_products[product.get('product_name')]["total_price"]) + float(
                                            total_amount), '.2f'))
                # print(f"offer_product: {offer_product}")
                print(f"producta: {product}")
                print(grouped_products[product.get('product_name')])
                if extra_charged_product_found is False:
                    unit_am = offer_product.get('unit_amount') if offer_product.get(
                        'unit_amount') is not None and offer_product.get('unit_amount') != "None" else 0
                    total_u_amount = int(unit_am) * charge
                    total_amount = str(
                        format(float(offer_product.get('quantity')) * total_u_amount, '.2f')) if offer_product.get(
                        'quantity') is not None else str(format(float(total_u_amount), '.2f'))
                    if grouped_products[product.get('product_name')].get("total_price") is None:
                        grouped_products[product.get('product_name')]["total_price"] = total_amount
                        grouped_products[product.get('product_name')]["extra_charged"] = False
                    else:
                        grouped_products[product.get('product_name')]["extra_charged"] = False
                        grouped_products[product.get('product_name')]["total_price"] = str(format(
                            float(grouped_products[product.get('product_name')]["total_price"]) + float(total_amount),
                            '.2f'))

                    body1 = {
                        "total_unit_amount": str(format(total_u_amount, '.2f')),
                        "extra_splitted_cost": str(0),
                        "total_amount": str(total_amount)
                    }
                    offer_amount += float(total_amount)
                    print(f"Sending body with no charging {body1}")
                    status1, msg1, data1 = update_offer_product(headers, offer_product.get('offer_product_key'), body1)
                    if status1 != 200:
                        return func_resp(msg=msg1, data=[], status=status1)
    #
    # print(offer_product_charges)
    # print("grouped_products...")
    # print(grouped_products)
    #
    # print("grouped_chars aaaaaaa")
    grouped_chars = combine_grouped_chars(grouped_chars)
    print(grouped_chars)

    # Save sto offer product new field extra_splitted_cost   += total_amount

    # Get offer charge

    # grouped_product_amount = {}
    # translation: {}
    for offer_p, v in offer_product_charges.items():
        # upEx = "set "
        # last = False
        # attValues = {}
        print(
            f"old total amount for product: {offer_p} was {offer_product_old_total_amount.get(offer_p)} and the extra was {offer_product_old_charges.get(offer_p)} now we add {v}")
        total_u_amount = (float(offer_product_old_unit_amount.get(offer_p)) + float(v)) * charge
        total_amount = format(float(offer_product_quantity.get(offer_p)) * total_u_amount, '.2f')
        offer_amount += float(total_amount)
        # if offer_product_old_charges.get(offer_p) != v:
        # print("in")
        body = {
            "total_unit_amount": str(format(total_u_amount, '.2f')),
            "extra_splitted_cost": str(v),
            "total_amount": str(total_amount)
        }
        print(f"Sending body {body}")
        status, msg, data = update_offer_product(headers, offer_p, body)
        if status != 200:
            return func_resp(msg=msg, data=[], status=status)

    print(
        f"offer_amount: {offer_amount} + total_charge_cost_amount: {total_charge_cost_amount} + offer_products_chars_amount: {offer_products_chars_amount} = {offer_amount + total_charge_cost_amount + offer_products_chars_amount}")
    offer_amount += total_charge_cost_amount + offer_products_chars_amount
    offer_fpa_percentage = 1 + float(offer_data.get("fpa")) / 100 if offer_data.get(
        "fpa") is not None and offer_data.get("fpa") != "None" else 1.00
    offer_discount_percentage = 1 - float(offer_data.get("discount")) / 100 if offer_data.get(
        "discount") is not None and offer_data.get("discount") != "None" else 1.00
    offer_discount_amount = offer_amount * offer_discount_percentage
    body = {
        "offer_amount": str(format(offer_amount, '.2f')),
        "offer_discount_amount": str(format(offer_discount_amount, '.2f')),
        "offer_fpa_amount": str(format(offer_discount_amount * offer_fpa_percentage, '.2f')),
        "offer_products_chars_amount": str(format(float(offer_products_chars_amount), '.2f'))
    }
    print(body)
    status, msg, data = update_offer(offer, body)
    if status != 200:
        return func_resp(msg=msg, data=[], status=status)

    grouped_products.update(grouped_chars)
    # grouped_products["chars"] = grouped_chars
    return func_resp(msg="", data=grouped_products, status=200)


def update_offer_costing_id(headers, offer_costing_id, body):
    upEx = "set "
    last = False
    attValues = {}

    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    if body.get('trip_amount_actual') is not None:
        if last is True:
            upEx += ","
        upEx += " trip_amount_actual = :trip_amount_actual"
        if body.get('trip_amount_actual') == "":
            attValues[":trip_amount_actual"] = str(0)
        else:
            attValues[":trip_amount_actual"] = str(body.get('trip_amount_actual'))
        last = True
    if body.get('transportation_out_actual') is not None:
        if last is True:
            upEx += ","
        upEx += " transportation_out_actual = :transportation_out_actual"
        if body.get('transportation_out_actual') == "":
            attValues[":transportation_out_actual"] = str(0)
        else:
            attValues[":transportation_out_actual"] = str(body.get('transportation_out_actual'))
        last = True
    if body.get('per_product_amount_actual') is not None:
        if last is True:
            upEx += ","
        upEx += " per_product_amount_actual = :per_product_amount_actual"
        if body.get('per_product_amount_actual') == "":
            attValues[":per_product_amount_actual"] = str(0)
        else:
            attValues[":per_product_amount_actual"] = str(body.get('per_product_amount_actual'))
        last = True
    grouped_products = get_days_costing_for_offerproducts(headers, client, str(body.get('offer')))

    print(grouped_products)
    if isinstance(grouped_products, str):
        return func_resp(msg=grouped_products, data=[], status=400)

    status, msg, grouped_products = affect_products_with_offer_costing_charges(headers, client, str(body.get('offer')),
                                                                               grouped_products, body)
    if status != 200:
        return func_resp(msg=msg, data=[], status=400)

    combine_grouped_products(grouped_products)

    if last is True:
        upEx += ","
    upEx += " grouped_products = :grouped_products"
    attValues[":grouped_products"] = json.dumps(grouped_products)
    last = True
    # return ""
    if body.get('people') is not None and body.get('people') != "" and body.get('area') is not None and body.get(
            'area') != "":
        if last is True:
            upEx += ","
        upEx += " people = :people"
        attValues[":people"] = str(body.get('people'))
        last = True

        upEx += ","
        upEx += " area = :area"
        attValues[":area"] = str(body.get('area'))

        upEx += ","
        upEx += " trip_amount = :trip_amount"
        attValues[":trip_amount"] = str(format(float(
            float(body.get("area")) * int(body.get("people")) * float(config.WORK_HOUR_COST) + float(
                grouped_products.get('total_days_needed')) * float(config.WORK_HOUR_COST)), '.2f'))

        # 'per_product_amount': str(format(float(config.PER_PRODUCT_COST) * float(grouped_products.get('total_products')), '.2f'))

    if body.get('offer') is not None and body.get('offer') != "":
        if last is True:
            upEx += ","
        upEx += " offer = :offer"
        attValues[":offer"] = str(body.get('offer'))
        last = True
    if (body.get('trip_amount') is not None and body.get('trip_amount') != "") and (
            body.get('people') is None or body.get('people') == "") and (
            body.get('area') is None or body.get('area') == ""):
        if last is True:
            upEx += ","
        upEx += " trip_amount = :trip_amount"
        attValues[":trip_amount"] = str(body.get('trip_amount'))
        last = True
    # if body.get('per_product_amount') is not None and body.get('per_product_amount') != "":
    if last is True:
        upEx += ","
    upEx += " per_product_amount = :per_product_amount"
    attValues[":per_product_amount"] = str(
        format(float(config.PER_PRODUCT_COST) * float(grouped_products.get('total_products')), '.2f'))
    # last = True
    # # if body.get('transportation_out') is not None and body.get('transportation_out') != "":
    # if last is True:
    upEx += ","
    upEx += " transportation_out = :transportation_out"
    attValues[":transportation_out"] = str(format(float(grouped_products['transportation_out']), '.2f'))
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
    if body.get('per_product_amount_list') is not None and body.get('per_product_amount_list') != "":
        if last is True:
            upEx += ","
        upEx += " per_product_amount_list = :per_product_amount_list"
        attValues[":per_product_amount_list"] = (body.get('per_product_amount_list'))
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
            return func_resp(msg='offer_costing Updated.', data={}, status=status_code)
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
