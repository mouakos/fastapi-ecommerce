"""Run the FastAPI application using Uvicorn."""

import uvicorn

if __name__ == "__main__":
    # Disable uvicorn logs completely

    uvicorn.run(
        "app.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_config=None,  # Disable uvicorn's default logging config
        access_log=False,  # Disable access logs
    )
