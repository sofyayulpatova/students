from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import current_user, login_user, login_required, logout_user
from app.models import User, Program, Lesson, Unique_Lesson, Homework, Test, Unique_Homework, Profile, QA
from app.main.forms import LoginForm
from werkzeug.urls import url_parse
from app.main import bp
from app import db
from functools import wraps


# greeting page
@bp.route('/')
def index():
    profile = Profile.query.get(1)

    return render_template("index.html", profile=profile)


# FOR TUTOR

# main with calendar, closest lessons, unchecked homework, etc.
@bp.route('/main/')
@login_required
def main():
    if current_user.tutor:
        return render_template("main.html")
    else:
        return redirect(url_for('main.index'))


# page with all students
@bp.route('/students/', methods=['POST', 'GET'])
@login_required
def students():
    if current_user.tutor:

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
    else:
        flash("123123")
        return redirect(url_for('main.index'))


# particular student page
@bp.route('/students/<int:person>')
@login_required
def person(person):
    if current_user.tutor:
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
    else:
        return redirect(url_for('main.index'))


# my programs page (all programs)
@bp.route('/programs/', methods=['POST', 'GET'])
@login_required
def programs():
    if current_user.tutor:
        if request.method == "POST":
            name = request.form['ProgramName']
            text = request.form['Text']
            program = Program(program=name, text=text, lesson=[])
            db.session.add(program)
            db.session.commit()
            request.close()
            return redirect(url_for('main.programs'))
        programs = Program.query.all()
        return render_template("programs.html", program=programs)
    else:
        return redirect(url_for('main.index'))


# one particular program
@bp.route("/programs/<int:id>")
def program(id):
    if current_user.tutor:
        program = Program.query.get(id)
        print(program.lesson)

        lessons = program.lesson
        homeworks = [i.homework for i in lessons]
        print(homeworks)
        tests = [i.test for i in lessons]
        return render_template("program.html", lessons=lessons[-3:], program_id=id, program=program,
                               homeworks=homeworks[-3:],

                               tests=tests[-3:])
    else:
        return redirect(url_for('main.index'))


# page with books, files etc.
@bp.route('/library')
@login_required
def library():
    if current_user.tutor:
        return render_template('library.html')
    else:
        return redirect(url_for('main.index'))


# tutor's control panel
@bp.route('/control_profile/')
@login_required
def control_profile():
    if current_user.tutor:
        students = User.query.filter_by(tutor=False).all()
        programs = Program.query.all()
        return render_template('control_profile.html', students=students, programs=programs)
    else:
        return redirect(url_for('main.index'))


@bp.route('/edit_profile/', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if current_user.tutor:
        if request.method == 'POST':
            profile = Profile.query.get(1)
            profile.name = request.form.get('Name_Surname')
            profile.specialisation = request.form.get('tutor')
            profile.about = request.form.get('about')
            profile.education = request.form.get('education')
            profile.work = request.form.get('work')
            profile.price = request.form.get('price')
            profile.contacts = request.form.get('contacts')
            db.session.add(profile)
            db.session.commit()
            return redirect(url_for('main.index'))
        profile = Profile.query.get(1)
        return render_template('edit_profile.html', profile=profile)
    else:
        return redirect(url_for('main.index'))


@bp.route('/control_students/')
@login_required
def control_students():
    if current_user.tutor:
        u = User.query.filter_by(tutor=False)
        return render_template('control_profile.html', students=u)
    else:
        return redirect(url_for('main.index'))


@bp.route('/update_profile/', methods=['GET', 'POST'])
@login_required
def update_profile():
    if current_user.tutor:
        return "really, update"
    else:
        return redirect(url_for('main.index'))


# login page
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.main'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('main.login'))
        login_user(user)
        if user.tutor:
            print("I AM TUTOR")
            return redirect(url_for('main.main'))
        elif not user.tutor:
            print("I AM STDENTS")
            print(url_for('student.main_page'))
            return redirect(url_for('student.main_page'))
    return render_template('login.html', title='Sign In', form=form)


# logout
@bp.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


def is_tutor(obj):
    return obj.tutor


# lesson
@bp.route("/<int:program_id>/lesson/<int:id>/<is_unique>")
@login_required
def lesson(program_id, id, is_unique):
    if current_user.tutor:
        print(Lesson.query.get(id).user)
        lesson = Lesson.query.get(id)
        les = Unique_Lesson.query.get(id)
        print(lesson, les, id)
        # if unique lesson only
        if is_unique == 1:
            print("in unique")
            return render_template("lesson.html", lesson=Unique_Lesson.query.get(id), program_id=program_id, id=id)
        # from student page
        if program_id == 0:
            print("in program == 0")
            if lesson.unique_lesson:
                print("in program == 0 and unique lesson")
                return render_template("lesson.html", lesson=lesson.unique_lesson, program_id=program_id, id=id)
            else:
                print("in program == 0 and not unique lesson")
                return render_template("lesson.html", lesson=lesson, program_id=program_id, id=id)
        print("hi")
        return render_template("lesson.html", lesson=lesson, program_id=program_id, id=id)
    else:
        return redirect(url_for('main.index'))


@bp.route('/lessons/create/<int:user_id>', methods=['GET', 'POST'])
@login_required
def create_lesson(user_id):
    if current_user.tutor:
        if user_id == 0 and request.method != "POST":
            return render_template('create_lesson.html', programs=Program.query.all())
        elif user_id != 0 and request.method != "POST":
            user = User.query.get(user_id)
            program = [Program.query.get(1)]
            print(Program.query.filter(Program.user.contains(user)))
            return render_template('create_lesson.html', programs=program)

        if request.method == "POST":
            if user_id == 0:
                title = request.form.get('LessonName')
                course = request.form.get('Course')
                body = request.form.get('editordata')
                program = Program.query.get(course)
                lesson = Lesson(title=title, program=program, text=body)

                db.session.add(lesson)
                db.session.commit()
                request.close()
                return redirect(url_for('main.create_empty_homework', id=lesson.id))
            else:
                title = request.form.get('LessonName')
                course = request.form.get('Course')
                body = request.form.get('editordata')
                program = Program.query.get(1)
                lesson = Lesson(title=title, program=program, text=body)
                db.session.add(lesson)
                db.session.commit()
                request.close()
                return redirect(url_for('main.create_empty_homework', id=lesson.id))
    else:
        return redirect(url_for('main.index'))


@bp.route('/lessons/<int:id>/create/empty_homework/', methods=['GET', 'POST'])
@login_required
def create_empty_homework(id):
    if current_user.tutor:
        lesson = Lesson.query.get(id)
        homework = Homework(text="Домашки нет!", lesson_id=lesson.id, title=lesson.title)
        test = Test(lesson_id=lesson.id, title=lesson.title)
        db.session.add_all([homework, test])
        db.session.commit()

        return redirect(url_for("main.program", id=lesson.program_id))
    else:
        return redirect(url_for('main.index'))


@bp.route("/lessons/edit/<int:id>/<int:user_id>", methods=["GET", "POST"])
def edit_lesson(id, user_id):
    if current_user.tutor:
        lesson = Lesson.query.get(id)
        programs = Program.query.all()
        if request.method == "POST":
            if user_id == 0:
                lesson.title = request.form.get('LessonName')
                lesson.text = request.form.get('editordata')

                db.session.add(lesson)
                db.session.commit()
                request.close()
                print(lesson, lesson.program)
                return redirect(url_for('main.program', id=lesson.program_id))
            else:
                title = request.form.get('LessonName')
                text = request.form.get('editordata')
                user_id = user_id
                unique_lesson = Unique_Lesson(lesson=lesson, user_id=user_id, title=title, text=text)

                db.session.add(unique_lesson)
                db.session.commit()
                request.close()
                return redirect(url_for('main.person', person=user_id))

        return render_template("edit_lesson.html", lesson=lesson, programs=programs)

    else:
        return redirect(url_for('main.index'))


@bp.route("/lessons/remove/<int:id>/<int:course_id>", methods=["GET", "POST"])
@login_required
def remove_lesson(id, course_id):
    if current_user.tutor:
        lesson = Lesson.query.get(id)
        homework = Homework.query.filter_by(lesson_id=id).first()
        test = Test.query.filter_by(lesson_id=id).first()
        db.session.delete(homework)
        db.session.delete(test)
        db.session.delete(lesson)
        db.session.commit()
        request.close()
        return redirect(url_for('main.program', id=course_id))
    else:
        return redirect(url_for('main.index'))

# homework

@bp.route("/<int:program>/lesson/<int:id>/homework")
@login_required
def homework(id, program):
    if current_user.tutor:
        lesson = Lesson.query.get(id)
        if program == 0:
            print('prog = 0')
            if lesson.unique_homework:
                return render_template("homework.html", lesson=lesson, homework=lesson.unique_homework)
        print("here?", lesson.homework.text)
        return render_template("homework.html", lesson=lesson, homework=lesson.homework)
    else:
        return redirect(url_for('main.index'))

@bp.route("/lesson/<int:id>/homework/<int:user_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_homework(id, user_id):
    if current_user.tutor:
        if request.method == 'POST':

            if user_id == 0:
                print("измнения из программы")
                homework = Homework.query.get(id)
                # print('hi', id, homework[0].title, homework[1].title)

                homework.lesson_id = id
                homework.title = request.form.get('HomeworkName')
                homework.text = request.form.get('editordata')
                lesson = Lesson.query.get(id)
                lesson.homework = homework

                db.session.add(homework)
                db.session.commit()
                request.close()
                return redirect(url_for('main.homework', id=id, program=lesson.program_id))
            unique_homework = Unique_Homework.query.get(id)
            if unique_homework is None:
                print("hi, were uni")
                title = request.form.get('HomeworkName')
                text = request.form.get('editordata')
                unique_homework = Unique_Homework(title=title, text=text, lesson_id=id)
            else:
                print("vjrgh")
                unique_homework.lesson_id = id
                unique_homework.title = request.form.get('HomeworkName')
                unique_homework.text = request.form.get('editordata')
                lesson = Lesson.query.get(id)
                lesson.unique_homework = unique_homework

            db.session.add(unique_homework)
            db.session.commit()
            request.close()
            return redirect(url_for('main.homework', id=id, program=0))
        lesson = Lesson.query.get(id)

        if lesson.unique_homework and user_id != 0:
            return render_template("edit_homework.html", homework=lesson.unique_homework)
        return render_template("edit_homework.html", homework=lesson.homework)
    else:
        return redirect(url_for('main.index'))

@bp.route("/lesson/<int:id>/homework/remove/<int:user_id>")
@login_required
def remove_homework(id, user_id):
    if current_user.tutor:

        hw = Homework.query.get(id)
        if user_id != 0:
            homework = Unique_Homework(text="Ничего не задано", lesson_id=id, title=hw.title)
            db.session.add(homework)
        else:
            hw.text = "Ничего не задано"
            db.session.add(hw)
        db.session.commit()
        redirect(url_for('main.homework', id=hw.lesson_homework.id, program=hw.lesson.program_id))
    else:
        return redirect(url_for('main.index'))

# test
@bp.route("/lesson/<int:id>/test")
@login_required
def test(id):
    if current_user.tutor:
        test = Test.query.get(id)
        return render_template("test.html", test=test, qa=test.qa)
    else:
        return redirect(url_for('main.index'))

@bp.route("/lesson/<int:id>/test/edit", methods=['POST', 'GET'])
@login_required
def edit_test(id):
    if current_user.tutor:
        if request.method == "POST":
            questions = request.form.getlist('questions')
            answers = request.form.getlist('answers')
            q_and_a = []
            for i in range(len(questions)):
                q = QA(test_id=id, question=questions[i], answer=answers[i])
                q_and_a.append(q)
            t = Test(title="qwe", lesson_id=id)
            db.session.add_all([t] + q_and_a)
            db.session.commit()
            return redirect(url_for('main.test', id=id))
        test = Test.query.get(id)

        return render_template('edit_test.html', test=test, qa=test.qa)
    else:
        return redirect(url_for('main.index'))

@bp.route("/lesson/<int:id>/test/remove")
@login_required
def remove_test(id):
    if current_user.tutor:
        test = Test.query.get(id)
        test.qa = []
        # TODO ничего не задано красивая страница
        db.session.add(test)
        db.session.commit()
        return redirect(url_for("main.test", id=id))
    else:
        return redirect(url_for('main.index'))

@bp.route("/student/lesson/<int:lesson_id>/<int:user_id>")
def open_lesson(lesson_id, user_id):
    if current_user.tutor:
        lesson = Lesson.query.get(lesson_id)
        lesson.user.append(User.query.get(user_id))
        db.session.add(lesson)
        db.session.commit()
        return "0"
    else:
        return redirect(url_for('main.index'))
