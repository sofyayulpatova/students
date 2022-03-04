from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import datetime

lu = db.Table('lu',
              db.Column('user', db.Integer(), db.ForeignKey('user.id')),
              db.Column('lesson', db.Integer(), db.ForeignKey('lesson.id'))
              )


class User(UserMixin, db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    program = db.Column(db.Integer(), db.ForeignKey("program.id"), default=1)
    password_hash = db.Column(db.String(255))
    description = db.Column(db.String(255))
    phone_number = db.Column(db.String(40), default="номер неизвестен")
    tutor = db.Column(db.Boolean(), default=False)
    user = db.relationship('Lesson', secondary=lu, backref='user')
    unique_lesson = db.relationship('Unique_Lesson', backref='user')

    def __repr__(self):
        return "<User {}>".format(self.id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


lp = db.Table('lp',
              db.Column('program', db.Integer(), db.ForeignKey('program.id')),
              db.Column('lesson', db.Integer(), db.ForeignKey('lesson.id'))
              )


class Program(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    program = db.Column(db.String(255), nullable=False)
    text = db.Column(db.Text())

    def __repr__(self):
        return self.program + "@" + str(self.id)


class Lesson(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    optional = db.Column(db.Text())
    title = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text())
    program = db.relationship('Program', secondary=lp, backref='lesson')
    unique_lesson = db.relationship('Unique_Lesson', backref='lesson', uselist=False)
    homework = db.relationship('Homework', backref='hw_lesson', uselist=False)

    def __repr__(self):
        return "<{}:{}>".format(self.id, self.title)


class Library(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    filename = db.Column(db.String(100))


class Homework(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text())
    to_file = db.Column(db.String(100))
    lesson = db.Column(db.Integer(), db.ForeignKey("lesson.id"), nullable=False)


class Unique_Lesson(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    lesson_id = db.Column(db.Integer(), db.ForeignKey("lesson.id"))
    user_id = db.Column(db.Integer(), db.ForeignKey("user.id"))
    title = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text())


class Unique_Homework(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    lesson_id = db.Column(db.Integer(), db.ForeignKey("lesson.id"))
    user_id = db.Column(db.Integer(), db.ForeignKey("user.id"))
    title = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text())


class Test(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text())
