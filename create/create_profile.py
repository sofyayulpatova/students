from app import create_app
from app import db
from app.models import Profile
app = create_app()

with app.app_context():
    profile = Profile(name="Math tutor")
    db.session.add(profile)
    db.session.commit()
