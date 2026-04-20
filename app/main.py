from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Pokemon Card Price Tracker")

app.include_router(router)

# Add a root endpoint for GET /
@app.get("/")
async def root():
	return {"message": "Welcome to the Pokemon Card Price Tracker API!"}