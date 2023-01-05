from authenticate.validate_response import func_resp
from config.config import DYNAMODB_USERS_TABLE
from databases.dbs import connect_to_dynamodb_resource


def execute_get_user_by_username(username):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    table = client.Table(DYNAMODB_USERS_TABLE)
    response = table.get_item(
        Key={
            'username': str(username),
        })

    if response.get('Item') is None:
        print(f"User with username: '{username}' not found.")
        return func_resp(msg="User not found.", data=[], status=404)
    else:
        # print("User data returned.")
        return func_resp(msg='', data=response['Item'], status=200)
