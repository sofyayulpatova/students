from app import app
import logging
from logging.handlers import SMTPHandler

app.run(debug=True)


if __name__ == "__main__":
    app.run("127.0.0.1:5000")
