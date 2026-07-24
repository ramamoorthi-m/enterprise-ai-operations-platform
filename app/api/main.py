from fastapi import FastAPI
app=FastAPI(
    title="Enterprise AI Operations Platform",
    version="0.1.0",
)

@app.get("/")
def root():
    return {
        "message":"Enterprise AI Operations Platform is running!"
    }