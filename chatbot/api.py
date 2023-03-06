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

@app.post("/", tags=["Root"])
async def read_root(request: Request):
    data = await request.json()
    print(data)
    print(request)

    session = data['session'].split('/')[-1]
    query_text = data['queryResult']['queryText']
    intent = data['queryResult']['intent']['displayName']

    if intent in ["interval_images_no_interval - custom-2", 
                  "interval_images_no_interval - custom",
                  "interval_images_yes - custom-2",
                  "interval_images_yes - custom",
                  "last_image_location - custom-2",
                  "last_image_location - custom"]:
        pass
    elif intent in ["interval_images"]:
        location = data['queryResult']['parameters']['location']['city']
        query = "INSERT INTO sessions (id, location, type, last) VALUES (:id, :location, :type, :last)"
        values = {"id": session, "location": location, "type": 'None', "last": False}
        await database.execute(query=query, values=values)
    elif intent in ["last_image"]:
        query = "INSERT INTO sessions (id, location, type, last) VALUES (:id, :location, :type, :last)"
        values = {"id": session, "location": "None", "type": 'None', "last": True}
        await database.execute(query=query, values=values)

    