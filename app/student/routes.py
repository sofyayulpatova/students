from flask import render_template, request, redirect, url_for, flash, session
from flask_login import current_user, login_required
from app.models import Lesson, Test, Task, Unique_Lesson, Unique_Homework, User
from app.student import bp
from werkzeug.utils import secure_filename
import os
from app import db, babel, Config


@babel.localeselector
def get_locale():
    if 'language' not in session:
        return request.accept_languages.best_match(Config.LANGUAGES)
    return session['language']


@bp.route('/lessons')
@login_required
def lessons():
    lessons = []
    for i in current_user.lesson:
        if i.unique_lesson:
            lessons.append(i.unique_lesson)
        else:
            lessons.append(i)
    return render_template('forstudent/lessons.html', lessons=current_user.lesson[-3:])


@bp.route('/lesson/<int:id>')
@login_required
def lesson(id):
    lesson = Lesson.query.get(id)
    unique_lesson = Unique_Lesson.query.filter(Unique_Lesson.user_id == current_user.id,
                                               Unique_Lesson.lesson_id == id).first()

    if unique_lesson:
        return render_template('forstudent/lesson.html', lesson=unique_lesson)
    else:
        return render_template('forstudent/lesson.html', lesson=lesson)


@bp.route('/homeworks')
@login_required
def homeworks():
    homeworks = []
    for i in current_user.lesson:
        if i.unique_homework:
            homeworks.append(i.unique_homework)
        else:
            homeworks.append(i.homework)
    return render_template("forstudent/homeworks.html", homeworks=homeworks)


@bp.route('/homework/<int:id>/<is_unqiue>', methods=["GET", "POST"])
@login_required
def homework(id, is_unqiue):
    lesson = Lesson.query.get(id)

    if request.method == "POST":
        # get student's tutor
        tutor = User.query.get(1)

        avatar = request.files.get('avatar')

        filename = avatar.filename
        avatar.save(os.path.join("C:/Users/h04226/PycharmProjects/students/app/uploads/", filename))

        if is_unqiue:
            unique_lesson = Lesson.query.get(id)

            print(unique_lesson.homework.id)
            task = Task(user_id=current_user.id, homework_id=2, to_file=filename, recipient=tutor)
            db.session.add(task)
            db.session.commit()
            return redirect(url_for('student.homework', id=id, is_unqiue=1))



        elif lesson.unique_homework:
            task = Task(user_id=current_user.id, unique_homework_id=lesson.unique_homework.id, to_file=filename,
                        recipient=tutor)
            db.session.add(task)
            db.session.commit()
        else:
            task = Task(user_id=current_user.id, homework_id=lesson.homework.id, to_file=filename, recipient=tutor)
            # author (user_id) - student
            # recipient - tutor
            db.session.add(task)
            db.session.commit()
        flash('successfully imported')
        return redirect(url_for('student.homework', id=id, is_unqiue=0))

    unique_homework = Unique_Homework.query.filter(Unique_Homework.lesson_id == id,
                                                   Unique_Homework.user_id == current_user.id).first()
    if unique_homework:
        task = unique_homework.task
        return render_template('forstudent/homework.html', homework=unique_homework, task=task)
    else:
        task = Task.query.filter(Task.user_id == current_user.id, Task.homework_id == lesson.homework.id).first()
        return render_template('forstudent/homework.html', homework=lesson.homework, task=task)


@bp.route('/tests')
@login_required
def tests():
    tests = [i.test for i in current_user.lesson]
    return render_template("forstudent/tests.html", tests=tests)


@bp.route('/tests/<int:id>', methods=['GET', 'POST'])
@login_required
def test(id):
    test = Test.query.get(id)
    counter = -1
    if request.method == 'POST':
        counter = 0
        questions = request.form.getlist('questions')
        for i in range(len(test.qa)):
            if test.qa[i].answer == questions[i]:
                counter += 1
        print(counter)
        return render_template("forstudent/test.html", test=test.qa, counter=counter, id=id)

    return render_template("forstudent/test.html", test=test.qa, counter=counter, id=id)


@bp.route('/main_page')
@login_required
def main_page():
    lessons, homeworks, tests = [], [], []
    for i in current_user.lesson:
        unique_lesson = Unique_Lesson.query.filter(Unique_Lesson.lesson_id == i.id,
                                                   Unique_Lesson.user_id == current_user.id).first()

        if unique_lesson:
            lessons.append(unique_lesson)
        else:
            lessons.append(i)

        unique_homework = Unique_Homework.query.filter(Unique_Homework.lesson_id == i.id,
                                                       Unique_Homework.user_id == current_user.id).first()
        if unique_homework:
            homeworks.append(unique_homework)
        else:
            homeworks.append(i.homework)

        tests.append(i.test)
    return render_template("forstudent/student_main.html", lessons=lessons[-3:], homeworks=homeworks[-3:],
                           tests=tests[-3:])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in Config.ALLOWED_EXTENSIONS


# Create a directory in a known location to save files to.
uploads_dir = os.path.join('uploads')

"""
@bp.route('/upload', methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        return render_template('forstudent/uploads.html')
    else:
        desc = request.form.get('desc')
        avatar = request.files.get('avatar')
        # Упакуйте имя файла для безопасности, но есть проблема с отображением китайского имени файла
        filename = secure_filename(avatar.filename)
        avatar.save(os.path.join("/Users/sofya/Downloads/students-master-2/app/uploads", filename))
        print(desc)
        return "reade"
"""
