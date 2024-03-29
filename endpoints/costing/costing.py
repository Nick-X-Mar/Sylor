import json
from authenticate.validate_response import func_resp, api_resp
from config import config


# @token_required
def get_all_extra_costings(headers):
    data = {
        "work_hour_cost": config.WORK_HOUR_COST,
        "per_product_cost": config.PER_PRODUCT_COST,
        "area_1": config.AREA_1,
        "area_2": config.AREA_2,
        "area_3": config.AREA_3,
        "area_4": config.AREA_4,
        "area_5": config.AREA_5,
        "palete_cost": config.PALETE_COST
    }
    return func_resp(msg="", data=data, status=200)


# @token_required
def register_new_costing(args):
    if args is not None:
        config.WORK_HOUR_COST = args.get("work_hour_cost") if not None else str(config.WORK_HOUR_COST)
        config.PER_PRODUCT_COST = args.get("per_product_cost") if not None else str(config.PER_PRODUCT_COST)
        config.AREA_1 = args.get("area_1") if not None else str(config.AREA_1)
        config.AREA_2 = args.get("area_2") if not None else str(config.AREA_2)
        config.AREA_3 = args.get("area_3") if not None else str(config.AREA_3)
        config.AREA_4 = args.get("area_4") if not None else str(config.AREA_4)
        config.AREA_5 = args.get("area_5") if not None else str(config.AREA_5)
        config.PALETE_COST = args.get("palete_cost") if not None else str(config.PALETE_COST)
        return func_resp(msg="Values updated", data=[], status=200)
    else:
        config.WORK_HOUR_COST = str(190 / 8)
        config.PER_PRODUCT_COST = "18"
        config.AREA_1 = "0"
        config.AREA_2 = "4"
        config.AREA_3 = "8"
        config.AREA_4 = "14"
        config.AREA_5 = "16"
        config.PALETE_COST = 150
    data = {
        "work_hour_cost": str(190 / 8),
        "per_product_cost": "18",
        "area_1": "0",
        "area_2": "4",
        "area_3": "8",
        "area_4": "14",
        "area_5": "16",
        "palete_cost": "150"
    }
    return func_resp(msg="Values reset", data=data, status=200)


# @token_required
def check_request_post(headers, body):
    if body is None:
        return func_resp(msg="Please complete all required fields.", data=[], status=400)

    try:
        body = json.loads(body)
    except:
        return func_resp(msg="Request body is not valid json", data=[], status=400)

    if not body or body is None:
        return func_resp(msg="Nothing send for insert.", data=[], status=400)

    # if not body.get("type"):
    #     return func_resp(msg="Please complete all required fields.", data=[], status=400)

    return func_resp(msg='', data=[], status=200)


# @token_required
def costing_related_methods(event, context):
    print(event)
    method = event.get("requestContext").get("http").get("method")
    # print(method)
    headers = event.get('headers')
    if method == "GET":
        status, msg, data = get_all_extra_costings(headers)
        return api_resp(msg=msg, data=data, status=status)

    if method == "POST":
        body = event.get("body")
        if body is not None:
            body = json.loads(body)
        status, msg, data = register_new_costing(body)
        return api_resp(msg=msg, data=data, status=status)

    else:
        return api_resp(msg="Not Allowed Method", data=[], status=400)

# if __name__ == "__main__":
#     check_request_post("a", "v")
