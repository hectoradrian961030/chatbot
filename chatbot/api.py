from fastapi import Request, FastAPI

app = FastAPI()

@app.post("/", tags=["Root"])
async def read_root(request: Request):
  print(request.body())
  return { 
    "message": "Welcome to my notes application, use the /docs route to proceed"
   }