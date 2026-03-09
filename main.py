from fastapi import FastAPI
import uvicorn


app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/")
def read_root():
    return {"Post": "Message"}

@app.put("/")
def read_root():
    return {"Put": "Message"}

@app.delete("/")
def read_root():
    return {"Delete": "Message"}


def main():
    uvicorn.run("main:app", port=8000, host="0.0.0.0", reload= True)

if __name__ == "__main__":
    main()
