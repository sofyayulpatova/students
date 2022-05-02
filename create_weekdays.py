from app import create_app
from app import db
from app.models import Weekday
app = create_app()

with app.app_context():
    weekday = Weekday(name="monday")
    db.session.add(weekday)
    weekday = Weekday(name="tuesday")
    db.session.add(weekday)
    weekday = Weekday(name="wednesday")
    db.session.add(weekday)
    weekday = Weekday(name="thursday")
    db.session.add(weekday)
    weekday = Weekday(name="friday")
    db.session.add(weekday)
    weekday = Weekday(name="saturday")
    db.session.add(weekday)
    weekday = Weekday(name="sunday")
    db.session.add(weekday)
    db.session.commit()
