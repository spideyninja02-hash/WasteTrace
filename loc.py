from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Device Location API")

class Location(BaseModel):
    latitude: float
    longitude: float

@app.post("/send-location", response_model=Location)
async def receive_location(location: Location):
    """
    Receives device GPS coordinates from the client and returns them as JSON.
    """
    return location
