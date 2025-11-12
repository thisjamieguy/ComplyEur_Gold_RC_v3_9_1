import os
from app.__init__auth__ import create_app
app = create_app()


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", os.getenv("FLASK_RUN_PORT", "5001")))
    app.run(host=host, port=port, debug=False)

