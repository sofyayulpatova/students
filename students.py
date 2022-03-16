from app import create_app, db
import logging
from logging.handlers import SMTPHandler

app = create_app()
if __name__ == "__main__":
    app.run("127.0.0.1", debug=True)
