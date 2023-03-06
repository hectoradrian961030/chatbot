from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from databases import Database

database = Database("sqlite:///chatbot.db")
from fastapi import Request, FastAPI

app = FastAPI()

@app.on_event("startup")
async def database_connect():
    await database.connect()


@app.on_event("shutdown")
async def database_disconnect():
    await database.disconnect()

async def get_or_create_chat(chat_id, location = 'None', type = 'None', last = False):
    # Define the SQL query to get the session
    query = f"SELECT * FROM sessions WHERE id = :session_id"

    # Define the parameters for the query
    values = {"session_id": chat_id}

    # Execute the query and get the results
    result = await database.fetch_all(query=query, values=values)

    if not result:
        query = "INSERT INTO sessions (id, location, type, last) VALUES (:id, :location, :type, :last)"
        values = {"id": chat_id, "location": location, "type": type, "last": last}
        result = await database.execute(query=query, values=values)

    print("RESULT", chat_id)

    return chat_id

@app.post("/", tags=["Root"])
async def read_root(request: Request):
    data = await request.json()
    print(data)
    print(request)

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
        print("AAAAAAAA")
        # OPTICA
        if intent in ["interval_images_no_interval - custom",
                  "interval_images_yes - custom",
                  "last_image_location - custom"]:
            print("BBBBBBBB")
            type = 'optica'
        # RADAR
        else:
            print("CCCCCCCC")
            type = 'radar'

        query = f"UPDATE sessions SET type = :new_type_value WHERE id = :row_id"
        values = {"new_type_value": type, "row_id": chat_id}
        await database.execute(query=query, values=values)

    # GET OR CREATE BY SESSION OR CHATID
    elif intent in ["interval_images"]:
        print("DDDDDDDD")
        chat_id = await get_or_create_chat(chat_id=chat_id, location=location, type='None', last=False)
    elif intent in ["last_image"]:
        print("EEEEEEEE")
        chat_id = await get_or_create_chat(chat_id=chat_id, location=location, type='None', last=True)
    elif intent in ["interval_images_yes",
                    "interval_images_no"]:
        print("FFFFFFFF")
        # INTERVALO
        if intent == "interval_images_yes":
            print("GGGGGGGG")
            last = False
        # ULTIMA
        else:
            print("HHHHHHHH")
            last = True

        query = f"UPDATE sessions SET last = :new_last_value WHERE id = :row_id"
        values = {"new_last_value": last, "row_id": chat_id}
        await database.execute(query=query, values=values)
    

    