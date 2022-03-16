from app.models import User, Profile
from app import db

'''
u = User(name="Antony", username="anton", tutor=True)
u.set_password("1")
db.session.add(u)
db.session.commit()
'''

p = Profile(name="Юлп Софьев")
db.session.add(p)
db.session.commit()