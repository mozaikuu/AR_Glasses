"""Start the HTTP gateway server."""
import uvicorn
from config.settings import API_HOST, API_PORT

if __name__ == "__main__":
    uvicorn.run(
        "server.gateway:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level="info"
    )

