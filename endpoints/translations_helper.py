from authenticate.validate_response import func_resp
from config.config import DYNAMODB_TRANSLATIONS_TABLE
from databases.dbs import connect_to_dynamodb_resource


# Todo: Return Jsons and not only names. When a product is created we need to know the ids of the chosen fields.
def traverse_items(item, list_of_translation_ids, list_of_translation_names):
    friendly_items = []
    temp = {}
    for k, v in item.items():
        if isinstance(v, dict):
            v = traverse_items(v, list_of_translation_ids, list_of_translation_names)
        elif isinstance(v, list):
            inner_list = []
            for inner_k in v:
                if inner_k in list_of_translation_ids:
                    inner_list.append({
                        "id": inner_k,
                        "value": list_of_translation_names[list_of_translation_ids.index(inner_k)]
                    })
            v = inner_list
        if isinstance(v, str):
            if v in list_of_translation_ids:
                v = {
                        "id": v,
                        "value": list_of_translation_names[list_of_translation_ids.index(v)]
                    }
        if k in list_of_translation_ids:
            k = list_of_translation_names[list_of_translation_ids.index(k)]
        if k[-3:] == "_id":
            k = k[:-3]
        temp[k] = v
    friendly_items.append(temp)
    return friendly_items


def connect_ids_with_translations(headers, products, lang='el'):
    client, status = connect_to_dynamodb_resource()
    if status != 200:
        return func_resp(msg=client, data=[], status=status)

    # Get All translations with 1 request
    table = client.Table(DYNAMODB_TRANSLATIONS_TABLE)
    res = table.scan()
    if res.get('Items') is not None and len(res['Items']) > 0:
        translations = res['Items']
    else:
        return func_resp(msg='Translations table does not exist', data=[], status=200)

    # Maintain only translation of the language that is needed
    list_of_translation_ids = []
    list_of_translation_names = []
    for t in translations:
        for k, v in t.items():
            if k == 'translation_id':
                list_of_translation_ids.append(v)
                if lang in t.keys():
                    list_of_translation_names.append(t[lang])
                else:
                    list_of_translation_names.append("missing")

    # Convert all name_ids to names
    friendly_products = []
    for product in products:
        friendly_products.extend(traverse_items(product, list_of_translation_ids, list_of_translation_names))
    return func_resp(msg='', data=friendly_products, status=200)
