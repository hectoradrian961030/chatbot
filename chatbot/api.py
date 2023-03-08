from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from databases import Database
from geopy.geocoders import Nominatim
from sentinelsat import SentinelAPI
from shapely.geometry import Point
from datetime import datetime, date, timedelta
import json


database = Database("sqlite:///chatbot.db")
from fastapi import Request, FastAPI

COPERNICUS_HUB_URL = 'https://apihub.copernicus.eu/apihub'
COPERNICUS_USER = 'hcastellanos'
COPERNICUS_PASSWORD = 'sentinel1q2w3e4r'

app = FastAPI()

@app.on_event("startup")
async def database_connect():
    await database.connect()


@app.on_event("shutdown")
async def database_disconnect():
    await database.disconnect()

async def get_or_create_chat(chat_id, location = 'None', type = 'None', last = False, interval = 'None'):
    query = f"SELECT * FROM sessions WHERE id = :session_id"

    values = {"session_id": chat_id}

    result = await database.fetch_all(query=query, values=values)

    if not result:
        query = "INSERT INTO sessions (id, location, type, last, interval) VALUES (:id, :location, :type, :last, :interval)"
        values = {"id": chat_id, "location": location, "type": type, "last": last, "interval": interval}
        result = await database.execute(query=query, values=values)
    return chat_id

async def generate_response(chat_id):
    query = f"SELECT * FROM sessions WHERE id = :chat_id"

    values = {"chat_id": chat_id}

    result = await database.fetch_one(query=query, values=values)

    chat_id, location, img_type, is_interval, str_interval = result

    geolocator = Nominatim(user_agent="sentinel-bot-vpcs")
    location = geolocator.geocode(location)

    latitude = location.latitude
    longitude = location.longitude

    api = SentinelAPI(COPERNICUS_USER, COPERNICUS_PASSWORD,
                      COPERNICUS_HUB_URL)

    point = Point((latitude, longitude))

    if img_type == 'optica':
        platformname = 'Sentinel-2'
        producttype = 'S2MSI2A'
    else:
        platformname = 'Sentinel-1'
        producttype = 'SLC'

    if is_interval:
        date_format = '%Y-%m-%dT%H:%M:%S%z'

        start_date = datetime.strptime(str_interval.split('#')[0], date_format)
        end_date = datetime.strptime(str_interval.split('#')[1], date_format)

        start_date = start_date.strftime("%Y%m%d")
        end_date = end_date.strftime("%Y%m%d")
    else:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        start_date = start_date.strftime("%Y%m%d")
        end_date = end_date.strftime("%Y%m%d")

    products = api.query(point.wkt,
                         date=(start_date, end_date),
                         platformname=platformname, producttype=producttype)

    products_df = api.to_dataframe(products)
    products_df_sorted = products_df.sort_values(['beginposition'], ascending=[False])

    if is_interval:
        result = json.dumps(list(products_df_sorted['summary']))
    else:
        result = json.dumps(list(products_df_sorted.iloc[[0]]['summary']))
    return result

@app.post("/", tags=["Root"])
async def read_root(request: Request):
    data = await request.json()

    chat_id = data['originalDetectIntentRequest']['payload']['data']['chat']['id']
    intent = data['queryResult']['intent']['displayName']

    try:
        location = data['queryResult']['parameters']['location']['city']
    except:
        location = 'None'

    # OPTICA O RADAR
    if intent in ["interval_images_no_interval - custom-2", 
                  "interval_images_no_interval - custom",
                  "interval_images_yes - custom-2",
                  "interval_images_yes - custom",
                  "last_image_location - custom-2",
                  "last_image_location - custom"]:
        # OPTICA
        if intent in ["interval_images_no_interval - custom",
                  "interval_images_yes - custom",
                  "last_image_location - custom"]:
            type = 'optica'
        # RADAR
        else:
            type = 'radar'

        query = f"UPDATE sessions SET type = :new_type_value WHERE id = :row_id"
        values = {"new_type_value": type, "row_id": chat_id}


        await database.execute(query=query, values=values)

        response = await generate_response(chat_id)
        return JSONResponse(content={'fulfillmentText': response})

    elif intent in ["interval_images"]:
        chat_id = await get_or_create_chat(chat_id=chat_id, location=location, type='None', last=False, interval='None')
    elif intent in ["last_image"]:
        chat_id = await get_or_create_chat(chat_id=chat_id, location=location, type='None', last=True, interval='None')
    elif intent in ["last_image_location"]:
        query = f"UPDATE sessions SET location = :new_location_value WHERE id = :row_id"
        values = {"new_location_value": location, "row_id": chat_id}
        await database.execute(query=query, values=values)
    elif intent in ["interval_images_yes",
                    "interval_images_no"]:
        # INTERVALO
        if intent == "interval_images_yes":
            last = False
        # ULTIMA
        else:
            last = True
        query = f"UPDATE sessions SET last = :new_last_value WHERE id = :row_id"
        values = {"new_last_value": last, "row_id": chat_id}
        await database.execute(query=query, values=values)
    elif intent in ["interval_images_no_interval"]:
        interval = data['queryResult']['parameters']['date']
        date_a = interval[0]
        date_b = interval[1]
        str_interval = str(date_a) + '#' + str(date_b)
        query = f"UPDATE sessions SET interval = :new_interval_value WHERE id = :row_id"
        values = {"new_interval_value": str_interval, "row_id": chat_id}
        await database.execute(query=query, values=values)

    

    