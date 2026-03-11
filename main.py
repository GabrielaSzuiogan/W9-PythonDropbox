from fastapi import FastAPI
import uvicorn
from api.routes import core_router

app = FastAPI()

app.include_router(core_router)

def main():
    uvicorn.run("main:app", port=8000, host="0.0.0.0", reload= True)

if __name__ == "__main__":
    main()
