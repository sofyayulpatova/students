from app import app, db
from app.models import User
from flask import render_template, request, redirect, url_for, flash
from app import login
from flask_login import current_user, login_user, login_required, logout_user
from app.models import User, Program, Lesson, Unique_Lesson, Homework, Test
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

        student = User(name=name, username=login, program=program)
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
    lesson = Lesson.query.all()
    homework = Homework.query.all()
    print(homework[0].hw_lesson.user)
    test = Test.query.all()
    # for lessons with unique lessons
    lessons = []
    homeworks = []
    tests = []
    for i in range(3, 0, -1):
        if lesson[-i].unique_lesson and lesson[-i].unique_lesson.user == person:
            lessons.append(lesson[-i].unique_lesson)
        else:
            lessons.append(lesson[-i])

        if homework[-i].hw_lesson:
            homeworks.append(homework[-i])
        '''   
       if test[-i].test_lesson.user == person:
           homeworks.append(test[-i])
       '''
    return render_template('student.html', student=person, lessons=lessons, homeworks=homeworks, tests=tests)


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
    lessons = Lesson.query.all()
    lesson = []
    for i in lessons:
        if program in i.program:
            lesson.append(i)
    return render_template("program.html", lessons=lesson, program_id=id, program=program)


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
def logout():
    logout_user()
    return "logout"


def is_tutor(obj):
    return obj.tutor


# lesson
@app.route("/lesson/<int:id>")
def lesson(id):
    lesson = Lesson.query.get(id)
    les = Unique_Lesson.query.get(id)
    if lesson.unique_lesson:
        return render_template("lesson.html", lesson=lesson.unique_lesson)
    else:
        return render_template("lesson.html", lesson=lesson)


@app.route('/lessons/create/', methods=['GET', 'POST'])
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
def create_empty_homework(id):
    lesson = Lesson.query.get(id)
    homework = Homework(text="Домашки нет!", lesson=lesson.id, title=lesson.title)
    db.session.add(homework)
    db.session.commit()

    return redirect(url_for('control'))


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
def remove_lesson(id, course_id):
    lesson = Lesson.query.get(id)
    homework = Homework.query.get(id)
    print(homework)
    db.session.delete(homework)
    db.session.delete(lesson)
    db.session.commit()

    request.close()
    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).netloc != '':
        return redirect(url_for('program', id=course_id))

    return redirect(next_page)


# homework

@app.route("/lesson/<int:id>/homework")
def homework(id):
    lesson = Lesson.query.get(id)
    homework = Homework.query.get(id)

    return render_template("homework.html", lesson=lesson, homework=homework)


'''
@app.route("/lesson/<int:id>/homework/create", methods=["GET", "POST"])
def create_homework(id):
    lesson = Lesson.query.get(id)
    if request.method == "POST":
        homework = Homework.query.get(id)
        print(id)
        print(homework)
        # homework.text = request.form.get('editordata')
        # db.session.add(homework)
        # db.session.commit()
        # print(homework)
        return redirect(url_for('lesson', id=id))
    return render_template("create_homework.html", id=id)
'''


@app.route("/lesson/<int:id>/homework/edit", methods=['GET', 'POST'])
def edit_homework(id):
    homework = Homework.query.get(id)
    if request.method == 'POST':
        homework.title = request.form.get('HomeworkName')
        homework.text = request.form.get('editordata')
        db.session.add(homework)
        db.session.commit()
        request.close()
        return redirect(url_for('homework', id=id))

    return render_template("edit_homework.html", homework=homework)


@app.route("/lesson/<int:id>/homework/remove")
def remove_homework(id):
    pass


# test
@app.route("/lesson/<int:id>/test")
def test(id):
    test = Test.query.get(1)
    return render_template("test.html", test=test)


@app.route("/lesson/test/create")
def create_test():
    pass


@app.route("/lesson/<int:id>/test/edit")
def edit_test(id):
    pass


@app.route("/lesson/<int:id>/test/remove")
def remove_test(id):
    pass
