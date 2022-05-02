from flask import current_app

from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

lu = db.Table('lu',
              db.Column('user', db.Integer(), db.ForeignKey('user.id')),
              db.Column('lesson', db.Integer(), db.ForeignKey('lesson.id'))
              )

up = db.Table('up',
              db.Column('user', db.Integer(), db.ForeignKey('user.id')),
              db.Column('program', db.Integer(), db.ForeignKey('program.id'))
              )


class User(UserMixin, db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    program = db.relationship('Program', secondary=up, backref='user')
    password_hash = db.Column(db.String(255))
    description = db.Column(db.String(255))
    phone_number = db.Column(db.String(40), default="номер неизвестен")
    tutor = db.Column(db.Boolean(), default=False)
    lesson = db.relationship('Lesson', secondary=lu, backref='user')
    unique_lesson = db.relationship('Unique_Lesson', backref='user')
    schedule = db.relationship('Schedule', backref='user')

    # for notifications homework
    homework_sent = db.relationship('Homework',
                                    foreign_keys='Homework.sender_id',
                                    backref='author', lazy='dynamic')
    homework_received = db.relationship('Homework',
                                        foreign_keys='Homework.recipient_id',
                                        backref='recipient', lazy='dynamic')

    # for notifications unique homework
    unique_homework_sent = db.relationship('Unique_Homework',
                                           foreign_keys='Unique_Homework.unique_sender_id',
                                           backref='author', lazy='dynamic')
    unique_homework_received = db.relationship('Unique_Homework',
                                               foreign_keys='Unique_Homework.unique_recipient_id',
                                               backref='recipient', lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime())

    def __repr__(self):
        return "<User {}>".format(self.id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Homework.query.filter_by(recipient=self).filter(
            Homework.timestamp > last_read_time).count()


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Weekday(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(10))
    schedule = db.relationship('Schedule', backref="weekday")


class Schedule(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    start = db.Column(db.Time)
    end = db.Column(db.Time)
    weekday_id = db.Column(db.Integer(), db.ForeignKey("weekday.id"))
    user_id = db.Column(db.Integer(), db.ForeignKey("user.id"))


class Program(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    program = db.Column(db.String(255), nullable=False)
    text = db.Column(db.Text())
    lesson = db.relationship('Lesson', backref='program')

    def __repr__(self):
        return self.program + "@" + str(self.id)


class Lesson(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    optional = db.Column(db.Text())
    title = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text())
    program_id = db.Column(db.Integer(), db.ForeignKey('program.id'))
    unique_lesson = db.relationship('Unique_Lesson', backref='lesson', uselist=False)
    unique_homework = db.relationship('Unique_Homework', backref='lesson', uselist=False)
    homework = db.relationship('Homework', backref='lesson_homework', uselist=False)
    test = db.relationship('Test', backref='lesson', uselist=False)

    def __repr__(self):
        return "<{}:{}>".format(self.id, self.title)


class Library(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    filename = db.Column(db.String(100))


class Homework(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    # for notifications
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    # homework itself (title, body, route to file)
    title = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text())
    to_file = db.Column(db.String(255))
    lesson_id = db.Column(db.Integer(), db.ForeignKey("lesson.id"))


class Unique_Lesson(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    lesson_id = db.Column(db.Integer(), db.ForeignKey("lesson.id"))
    user_id = db.Column(db.Integer(), db.ForeignKey("user.id"))
    title = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text())
    program = db.Column(db.Integer(), db.ForeignKey("program.id"), default=1)


class Unique_Homework(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    lesson_id = db.Column(db.Integer(), db.ForeignKey("lesson.id"))
    program = db.Column(db.Integer(), db.ForeignKey("program.id"), default=1)
    user_id = db.Column(db.Integer(), db.ForeignKey("user.id"))
    title = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text())

    # for notifications
    unique_sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    unique_recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    # route to file
    to_file = db.Column(db.String(255))


class Test(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    lesson_id = db.Column(db.Integer(), db.ForeignKey("lesson.id"))
    qa = db.relationship("QA", backref="test")


class QA(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    test_id = db.Column(db.Integer(), db.ForeignKey("test.id"))
    question = db.Column(db.String(100))
    answer = db.Column(db.String(100))


class Profile(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100))
    specialisation = db.Column(db.String(100))
    about = db.Column(db.Text())
    education = db.Column(db.Text())
    work = db.Column(db.Text())
    price = db.Column(db.Text())
    contacts = db.Column(db.Text())
