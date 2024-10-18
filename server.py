
# Imports
import uvicorn
from fastapi import FastAPI
from db import get_daily

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "test"}
    

@app.get("/today")
async def today():
    response = get_daily()
    if response is None:
        return {"message": "Failed to retrieve daily menu."}
    else:
        return response.to_json(orient='index')

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)