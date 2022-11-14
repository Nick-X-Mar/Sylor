import json


def api_resp(status, msg='', data=None):
    if data is None:
        data = []
    r = json.dumps({
        "message": msg,
        "data": data,
        "statusCode": status
    })
    return r


def func_resp(status, msg='', data=None):
    return status, msg, data
