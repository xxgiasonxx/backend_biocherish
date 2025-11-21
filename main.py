if __name__ == "__main__":
    import uvicorn
    import argparse


    from app.main import bio_app
    uvicorn.run(bio_app, host="0.0.0.0", port=8080, reload=False)