from app import create_app
import logging
from logging.handlers import SMTPHandler

app = create_app()
from app import db

@app.shell_context_processor
def make_shell_context():
    return {'db': db}


if __name__ == "__main__":
    app.run("127.0.0.1", debug=True)
