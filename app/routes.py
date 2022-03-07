from app import app, db
from app.models import User
from flask import render_template, request, redirect, url_for, flash
from app import login
from flask_login import current_user, login_user, login_required, logout_user
from app.models import User, Program, Lesson, Unique_Lesson, Homework, Test, Unique_Homework
from app.forms import LoginForm
from werkzeug.urls import url_parse


# greeting page
@app.route('/')
def index():
    return render_template("index.html")


# FOR TUTOR

# main with calendar, closest lessons, unchecked homework, etc.
@app.route('/main/')
@login_required
def main():
    return render_template("main.html")


# page with all students
@app.route('/students/', methods=['POST', 'GET'])
def students():
    if request.method == 'POST':
        name = request.form['StudentName']
        login = request.form['StudentLogin']
        password = request.form['StudentPassword']
        program = request.form['Course']

        student = User(name=name, username=login, program_id=program)
        student.set_password(password)
        db.session.add(student)
        db.session.commit()
        request.close()
        return redirect('/students', 302)
    programs = Program.query.all()
    students = []
    for i in User.query.all():
        if not is_tutor(i):
            students.append(i)
    return render_template("students.html", students=students, programs=programs)


# particular student page
@app.route('/students/<int:person>')
@login_required
def person(person):
    person = User.query.get(person)
    current_program = person.program
    lesson = current_program.lesson
    homeworks, lessons, tests = [], lesson.copy(), []

    # lessons from program and unique lessons from program
    for i in range(len(lessons)):

        # add homework

        if lessons[i].unique_homework and lessons[i].unique_homework == person.id:
            homeworks.append(lessons[i].unique_homework)
        else:
            homeworks.append(lessons[i].homework)

        # add test
        tests.append(lessons[i].test)

        # add lesson
        if lessons[i].unique_lesson and lessons[i].unique_lesson.user_id == person.id:
            lessons[i] = lessons[i].unique_lesson

    # add unique lesson for student (from rubbish program, u know)
    lesson = Lesson.query.filter(Lesson.user.contains(person))
    for i in lesson:
        if i not in lessons:
            lessons.append(i)
            homeworks.append(i.homework)
            tests.append(i.test)

    return render_template('student.html', student=person, lessons=lessons[-3:], homeworks=homeworks[-3:],
                           tests=tests[-3:])


# my programs page (all programs)
@app.route('/programs/', methods=['POST', 'GET'])
@login_required
def programs():
    if request.method == "POST":
        name = request.form['ProgramName']
        text = request.form['Text']
        program = Program(program=name, text=text)
        db.session.add(program)
        db.session.commit()
        request.close()
        return redirect(url_for('programs'))
    programs = Program.query.all()
    return render_template("programs.html", program=programs)


# one particular program
@app.route("/programs/<int:id>")
def program(id):
    program = Program.query.get(id)
    lessons = program.lesson
    homeworks = [i.homework for i in lessons]
    tests = [i.test for i in lessons]
    return render_template("program.html", lessons=lessons[-3:], program_id=id, program=program,
                           homeworks=homeworks[-3:],
                           tests=tests[-3:])


# page with books, files etc.
@app.route('/library')
@login_required
def library():
    return render_template('library.html')


# tutor's control panel
@app.route('/control/')
@login_required
def control():
    return render_template('control.html')


# login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


# logout
@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return "logout"


def is_tutor(obj):
    return obj.tutor


# lesson
@app.route("/<int:program_id>/lesson/<int:id>")
@login_required
def lesson(program_id, id):
    lesson = Lesson.query.get(id)
    les = Unique_Lesson.query.get(id)

    if program_id == 0:
        if lesson.unique_lesson:
            return render_template("lesson.html", lesson=lesson.unique_lesson)
        else:
            return render_template("lesson.html", lesson=lesson)
    return render_template("lesson.html", lesson=lesson)


@app.route('/lessons/create/', methods=['GET', 'POST'])
@login_required
def create_lesson():
    programs = Program.query.all()
    users = User.query.filter_by(tutor=False).all()

    if request.method == "POST":
        title = request.form.get('LessonName')
        course = request.form.get('Course')
        body = request.form.get('editordata')
        open_for_users_id = request.form.getlist("users")
        lesson = Lesson(title=title, program=[], text=body)
        program = Program.query.get(course)
        lesson.program.append(program)
        open_for_users = User.query.filter(User.id.in_(open_for_users_id)).all()

        lesson.user.extend(open_for_users)
        db.session.add(lesson)
        db.session.commit()
        request.close()
        return redirect(url_for('create_empty_homework', id=lesson.id))

    return render_template('create_lesson.html', programs=programs, users=users)


@app.route('/lessons/<int:id>/create/empty_homework/', methods=['GET', 'POST'])
@login_required
def create_empty_homework(id):
    lesson = Lesson.query.get(id)
    homework = Homework(text="Домашки нет!", lesson=lesson.id, title=lesson.title)
    test = Test(question=[], lesson_id=lesson.id, title=lesson.title)
    db.session.add_all([homework, test])
    db.session.commit()

    return redirect(url_for("program", id=lesson.program[0].id))


@app.route("/lessons/edit/<int:id>/<int:user_id>", methods=["GET", "POST"])
def edit_lesson(id, user_id):
    lesson = Lesson.query.get(id)
    programs = Program.query.all()
    if request.method == "POST":
        if request.form.get("question") == "yes":
            lesson.title = request.form.get('LessonName')
            lesson.course = request.form.get('Course')
            lesson.text = request.form.get('editordata')

            db.session.add_all(lesson)
            db.session.commit()
            request.close()
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                return redirect(url_for('program', id=lesson.course))
            return redirect(next_page)
        else:
            title = request.form.get('LessonName')
            text = request.form.get('editordata')
            user_id = user_id
            unique_lesson = Unique_Lesson(lesson=lesson, user_id=user_id, title=title, text=text)

            db.session.add(unique_lesson)
            db.session.commit()
            request.close()
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                return redirect(url_for('person', person=user_id))
            return redirect(next_page)

    return render_template("edit_lesson.html", lesson=lesson, programs=programs)


@app.route("/lessons/remove/<int:id>/<int:course_id>", methods=["GET", "POST"])
@login_required
def remove_lesson(id, course_id):
    lesson = Lesson.query.get(id)
    homework = Homework.query.filter_by(lesson=id).first()
    test = Test.query.filter_by(lesson_id=id).first()
    db.session.delete(homework)
    db.session.delete(test)
    db.session.delete(lesson)
    db.session.commit()
    request.close()
    return redirect(url_for('program', id=course_id))


# homework

@app.route("/lesson/<int:id>/homework")
@login_required
def homework(id):
    lesson = Lesson.query.get(id)
    if lesson.unique_homework:
        return render_template("homework.html", lesson=lesson, homework=lesson.unique_homework)
    else:
        return render_template("homework.html", lesson=lesson, homework=lesson.homework)


@app.route("/lesson/<int:id>/homework/edit", methods=['GET', 'POST'])
@login_required
def edit_homework(id):
    if request.method == 'POST':
        unique_homework = Unique_Homework.query.get(id)
        if unique_homework is None:
            title = request.form.get('HomeworkName')
            text = request.form.get('editordata')
            unique_homework = Unique_Homework(title=title, text=text, lesson_id=id)
        else:
            unique_homework.lesson_id = id
            unique_homework.title = request.form.get('HomeworkName')
            unique_homework.text = request.form.get('editordata')
            Lesson.query.get(id).unique_homework = unique_homework

        db.session.add(unique_homework)
        db.session.commit()
        request.close()
        return redirect(url_for('homework', id=id))
    lesson = Lesson.query.get(id)
    if lesson.unique_homework:
        return render_template("edit_homework.html", homework=lesson.unique_homework)
    return render_template("edit_homework.html", homework=lesson.homework)


@app.route("/lesson/<int:id>/homework/remove")
@login_required
def remove_homework(id):
    homework = Homework.get(id)
    homework.text = "Ничего не задано"
    db.session.add(homework)
    return redirect(url_for('program', id=homework.hw_lesson.id))


# test
@app.route("/lesson/<int:id>/test")
@login_required
def test(id):
    test = Test.query.get(id)
    return render_template("test.html", test=test)


@app.route("/lesson/<int:id>/test/edit")
@login_required
def edit_test(id):
    test = Test.query.get(id)
    return render_template('edit_test.html', test=test)


@app.route("/lesson/<int:id>/test/remove")
@login_required
def remove_test(id):
    pass
