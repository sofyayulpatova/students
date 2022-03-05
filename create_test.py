from app.models import Test, Lesson, Question, IncorrectAnswers
from app import db


def create_test():
    l = Lesson.query.all()
    test = Test(title="title", lesson_id=l[0].id)
    db.session.add(test)
    db.session.commit()


def create_question():
    test = Test.query.all()
    question = Question(question="question", test_id=test[0].id, correct_answer="correct", incorrect_answer=[])
    db.session.add(question)
    db.session.commit()


def create_incorrect_answer():
    q = Question.query.all()
    incor = IncorrectAnswers(incorrect_answer='incorrect', question_id=q[0].id)
    db.session.add(incor)
    db.session.commit()



