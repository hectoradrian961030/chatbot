from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from databases import Database

database = Database("sqlite:///test.db")
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
    data = request.json()
    print(data)
    print(request)

    session = data['session']
    query_text = data['queryResult']['queryText']
    action = data['queryResult']['action']

    if action in ["interval_images.interval_images-no.interval_images_no-custom.interval_images_no_interval-custom-2", 
                  "interval_images.interval_images-no.interval_images_no-custom.interval_images_no_interval-custom",
                  "interval_images.interval_images-yes.interval_images_yes-custom-2",
                  "interval_images.interval_images-yes.interval_images_yes-custom",
                  "last_image.last_image-custom.last_image_location-custom-2",
                  "last_image.last_image-custom.last_image_location-custom"]:
        pass
    else:
        query = "INSERT INTO sessions (id, location, type) VALUES (:id, :location, :type)"
        values = {"id": session.split('/')[-1], "location": query_text, "type": 'None'}
        await database.execute(query=query, values=values)

    