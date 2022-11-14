import jwt
# from datetime import datetime, timedelta
from functools import wraps
# from flask import request, jsonify, make_response
from authenticate.validate_response import func_resp
from config import config
from endpoints.get_single_user import execute_get_user_by_username


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        jwt_header = config.JWT_HEADER
        if len(args) > 0:
            try:
                # print(args[0])
                token = args[0].get(jwt_header)
                # print(token)
            except:
                return func_resp(msg='Token is missing !!', data=[], status=401)
        # token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6Im5pa29zMSIsImV4cCI6MTY2NzQyNjQzOH0.T5t2ZXpzdyKU7T7sed-7prGMHVeHSSOUprKKwmgXzaE"
        if token is None:
            return func_resp(msg='Token is missing !!', data=[], status=401)

        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
            status, msg, data = execute_get_user_by_username(data.get('username'))
            if status != 200:
                return func_resp(msg='User not Found.', data=[], status=200)
        except:
            return func_resp(msg="Token is invalid!", data=[], status=401)
        # returns the current logged in users contex to the routes
        return f(*args, **kwargs)

    return decorated


# @token_required
# def test(a):
#     print(a)
#
#
# if __name__ == "__main__":
#     print(test("yy"))
