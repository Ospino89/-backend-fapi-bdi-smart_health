# app/main.py

from fastapi import FastAPI
from .routers import auth, user
from .database.database import Base, engine
#from mangum import Mangum



Base.metadata.create_all(bind=engine)

app = FastAPI(title="SmartHealth API - Sprint 1")

app.include_router(auth.router)
app.include_router(user.router)


@app.get("/")
def root():
    return {"message": "¡API funcionando correctamente!"}

#handler = Mangum(app)



