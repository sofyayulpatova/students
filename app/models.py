from app import db, login
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
import json
from time import time
import redis
import rq

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
    calendar_id = db.Column(db.String(255))
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

    # for notifications
    notifications = db.relationship('Notification', backref='user',
                                    lazy='dynamic')

    message_sent = db.relationship('Task',
                                   foreign_keys='Task.user_id',
                                   backref='author', lazy='dynamic')
    message_received = db.relationship('Task',
                                       foreign_keys='Task.recipient_id',
                                       backref='recipient', lazy='dynamic')

    last_message_read_time = db.Column(db.DateTime)

    redis_tasks = db.relationship('RedisTask', backref='user', lazy='dynamic')

    def __repr__(self):
        return "<User {}>".format(self.id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Task.query.filter_by(recipient=self).filter(
            Task.timestamp > last_read_time).count()

    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    def launch_task(self, name, description, *args, **kwargs):
        rq_job = current_app.task_queue.enqueue('app.tasks.' + name, self.id,
                                                *args, **kwargs)
        task = Task(id=rq_job.get_id(), name=name, description=description,
                    user=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return RedisTask.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return RedisTask.query.filter_by(name=name, user=self,
                                         complete=False).first()


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


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))


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
    unique_lesson = db.relationship('Unique_Lesson', backref='lesson')
    unique_homework = db.relationship('Unique_Homework', backref='lesson')
    homework = db.relationship('Homework', backref='lesson_homework', uselist=False)
    test = db.relationship('Test', backref='lesson', uselist=False)




    def __repr__(self):
        return "<{}:{}>".format(self.id, self.title)


class Library(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String())
    filename = db.Column(db.String(100))


class Homework(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    # homework itself (title, body)
    title = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text())
    lesson_id = db.Column(db.Integer(), db.ForeignKey("lesson.id"))

    task = db.relationship('Task', backref='homework')


class Task(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    grade = db.Column(db.Integer)
    to_file = db.Column(db.String(255))
    comments = db.Column(db.Text)
    user_id = db.Column(db.Integer(), db.ForeignKey("user.id"))

    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    homework_id = db.Column(db.Integer(), db.ForeignKey("homework.id"))

    unique_homework_id = db.Column(db.Integer(), db.ForeignKey("unique__homework.id"))


class Unique_Lesson(db.Model):
    id = db.Column(db.Integer(), primary_key=True)

    lesson_id = db.Column(db.Integer(), db.ForeignKey("lesson.id"))  # non-mandatory

    user_id = db.Column(db.Integer(), db.ForeignKey("user.id"))
    title = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text())
    program = db.Column(db.Integer(), db.ForeignKey("program.id"), default=2)



class Unique_Homework(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    lesson_id = db.Column(db.Integer(), db.ForeignKey("lesson.id"))
    program = db.Column(db.Integer(), db.ForeignKey("program.id"), default=2)
    user_id = db.Column(db.Integer(), db.ForeignKey("user.id"))
    title = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text())

    task = db.relationship('Task', backref='unique_homework')


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


class RedisTask(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    complete = db.Column(db.Boolean, default=False)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100
