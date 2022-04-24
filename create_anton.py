from app import create_app
from app import db
from app.models import User
app = create_app()

with app.app_context():
    u = User(name="Antony", username="anton", tutor=True)
    u.set_password("1")
    db.session.add(u)
    db.session.commit()

