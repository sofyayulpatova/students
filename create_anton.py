from app.models import User
from app import db


u = User(name="Antony", username="anton", tutor=True)
u.set_password("1")
db.session.add(u)
db.session.commit()

