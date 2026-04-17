from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Pokemon Card Price Tracker")


@app.get("/")
async def read_root():
	return {
		"app": "Pokemon Card Price Tracker",
		"status": "ok",
		"docs": "/docs",
		"search_endpoint": "/search",
	}


app.include_router(router)