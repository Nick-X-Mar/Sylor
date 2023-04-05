PROFILE = 'prod-'
# AWS Tables
DYNAMODB_USERS_TABLE = PROFILE+'sylorUsersTable'
DYNAMODB_TRANSLATIONS_TABLE = PROFILE+'sylorTranslations'
DYNAMODB_PRODUCTS_TABLE = PROFILE+"sylorProducts"
DYNAMODB_CATEGORY_TABLE = PROFILE+"sylorProductCategorySchema"
DYNAMODB_SUBCATEGORY_TABLE = PROFILE+"sylorProductSubCategory"
DYNAMODB_PRODUCT_SPECIFICS_TABLE = PROFILE+"sylorProductSpecifics"
DYNAMODB_PRODUCT_GENERAL_SPECS_TABLE = PROFILE+"sylorProductGeneralSpecs"
DYNAMODB_CLIENTS_TABLE = PROFILE+"sylorClients"
DYNAMODB_OFFERS_TABLE = PROFILE+"sylorOffers"
DYNAMODB_OFFERS_PRODUCT_TABLE = PROFILE+"sylorOffersProduct"
DYNAMODB_EXTRA_COSTINGS_TABLE = PROFILE+"sylorExtraCostings"
DYNAMODB_OFFER_COSTING_TABLE = PROFILE+"sylorOfferCostings"

# JWT
JWT_SECRET = 'rover1-qualifier-unplowed-rebalance-wobble'
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_SECONDS = 86400
JWT_HEADER = 'x_access_token'

# Costing
WORK_HOUR_COST = str(190/8)
PER_PRODUCT_COST = "18"
AREA_1 = "0"
AREA_2 = "4"
AREA_3 = "8"
AREA_4 = "14"
AREA_5 = "16"
PALETE_COST = 150

PRODUCTS_CAT_YALO = ["553996cf-ec8a-43aa-840d-ebe366f964b0", "59210467-e38e-4f10-aae8-df41441c6e64"]
PRODUCTS_CAT_PATZ = ["239b5987-5964-42b5-b228-63765f5461df", "67d8d551-1404-432c-90fd-4fabc85efdbd"]
PRODUCTS_CAT_EJO = ["0a4f6648-1831-44e5-902d-83b02e5be497"]
PRODUCTS_CAT_ROLO = ["a36de552-c85f-4c59-8b36-1614462c24fd"]

CHARS_CAT_METAL_PARTS = ["extra_patzoy_1_1", "extra_patzoy_1_2"]
CHARS_CAT_SITA = ["extra_yalo_2", "extra_patzoy_2"]
CHARS_CAT_MECH = ["extra_yalo_4", "extra_patzoy_3"]
CHARS_CAT_KAITIA = ["extra_yalo_8", "extra_patzoy_4"]
CHARS_CAT_TAMP = ["extra_yalo_9", "extra_patzoy_5"]
CHARS_CAT_COLOR = ["extra_yalo_10", "extra_patzoy_6"]
CHARS_CAT_WOOD = ["extra_yalo_11", "extra_patzoy_7"]
