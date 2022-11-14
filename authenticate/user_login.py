import json
from datetime import datetime, timedelta
import jwt
from authenticate.validate_response import func_resp, api_resp
from config import config
from endpoints.users import execute_get_user_by_username
from passlib.hash import pbkdf2_sha256


def execute_login(username, password):
    print(username)
    status, msg, user_data = execute_get_user_by_username(username=username)
    if status == 200:
        # print(f"Given username: {username}, password: {password}, evaluation was: {pbkdf2_sha256.verify(password, user_data.get('password'))}")
        if pbkdf2_sha256.verify(password, user_data.get('password')) is False:
            return func_resp(msg='Wrong credentials', data=[], status=400)

        payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(seconds=config.JWT_EXP_DELTA_SECONDS)
        }
        jwt_token = jwt.encode(payload, config.JWT_SECRET, config.JWT_ALGORITHM)
        return func_resp(msg='', data={'token': jwt_token}, status=200)
    else:
        return func_resp(msg=msg, data=user_data, status=status)


def check_request(username, password):
    if username is None or username == "":
        return func_resp(msg="Username was not given.", data=None, status=400)

    if password is None or password == "":
        return func_resp(msg="Password was not given.", data=None, status=400)

    return func_resp(msg=None, data=None, status=200)


def loging_request_receiver(event, context):
    print(event)
    method = event.get("requestContext").get("http").get("method")
    if method == "POST":
        body = event.get("body")
        # print(body)
        if body is not None:
            body = json.loads(body)
        else:
            return api_resp(msg="Username/Pass were not given.", data=[], status=404)
        username = body.get('username')
        password = body.get('password')
        # print(username)
        # print(body)
        # print(password)
        status, msg, data = check_request(username, password)
        if status == 200:
            status, msg, data = execute_login(username, password)
        return api_resp(msg=msg, data=data, status=status)
    else:
        return api_resp(msg="Method not Allowed", data=[], status=404)


# if __name__ == "__main__":
#     print(execute_login(password="1232456", username="nikos3@gmail.com"))
