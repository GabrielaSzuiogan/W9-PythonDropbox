from fastapi import FastAPI
import uvicorn


app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

def main():
    uvicorn.run("main:app", port=8000, host="0.0.0.0", reload= True)

if __name__ == "__main__":
    main()
