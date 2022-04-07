from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user, login_user, login_required, logout_user
from app.models import User, Program, Lesson, Unique_Lesson, Homework, Test, Unique_Homework, Profile
from app.main.forms import LoginForm
from werkzeug.urls import url_parse
from app.student import bp
from werkzeug.utils import secure_filename
import os
from app import db
from functools import wraps

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'pptx', 'ppt', 'txt'}


@bp.route('/lessons')
@login_required
def lessons():
    lessons = []
    for i in current_user.lesson:
        if i.unique_lesson:
            lessons.append(i.unique_lesson)
        else:
            lessons.append(i)
    return render_template('forstudent/lessons.html', lessons=current_user.lesson)


@bp.route('/lesson/<int:id>')
@login_required
def lesson(id):
    lesson = Lesson.query.get(id)
    if lesson.unique_lesson:
        return render_template('forstudent/lesson.html', lesson=lesson.unique_lesson)
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


@bp.route('/homework/<int:id>')
@login_required
def homework(id):
    lesson = Lesson.query.get(id)
    if lesson.unique_homework:
        return render_template('forstudent/homework.html', homework=lesson.unique_homework)
    else:
        return render_template('forstudent/homework.html', homework=lesson.homework)


@bp.route('/tests')
@login_required
def tests():
    tests = [i.test for i in current_user.lesson]
    return render_template("forstudent/tests.html", tests=tests)


@bp.route('/tests/<int:id>')
@login_required
def test(id):
    tests = [i.test for i in current_user.lesson]
    return render_template("forstudent/tests.html", tests=tests)


@bp.route('/main_page')
@login_required
def main_page():
    lessons, homeworks, tests = [], [], []
    for i in current_user.lesson:
        if i.unique_lesson:
            lessons.append(i.unique_lesson)
        else:
            lessons.append(i)
        if i.unique_homework:
            homeworks.append(i.unique_homework)
        else:
            homeworks.append(i.homework)
        tests.append(i.test)
    return render_template("forstudent/hehehe.html", lessons=lessons, homeworks=homeworks, tests=tests)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


# Create a directory in a known location to save files to.
uploads_dir = os.path.join('uploads')




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
