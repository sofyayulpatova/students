from flask import render_template, request, redirect, url_for, flash, send_from_directory, session, jsonify
from flask_login import current_user, login_user, login_required, logout_user
from app.models import User, Program, Lesson, Unique_Lesson, Homework, Test, Unique_Homework, Profile, QA, Weekday, \
    Schedule, Task, Notification, Library
from app.main.forms import LoginForm
from app.main import bp
from app import db, babel, Config
import time
import os
import datetime
import requests
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

from oauth2client import client
from googleapiclient import sample_tools


def create_calendar(calendar):
    if not current_user.calendar_id:
        request_body = {'summary': "students"}
        res = calendar.calendars().insert(body=request_body).execute()
        teacher = User.query.get(current_user.id)
        teacher.calendar_id = res['id']

        db.session.add(teacher)
        db.session.commit()
        flash('calendar created!')


def create_student_event():
    credentials = google.oauth2.credentials.Credentials(
        **session['credentials'])

    calendar = googleapiclient.discovery.build(
        Config.API_SERVICE_NAME, Config.API_VERSION, credentials=credentials)


@babel.localeselector
def get_locale():
    if 'language' not in session:
        return request.accept_languages.best_match(Config.LANGUAGES)
    return session['language']


@bp.route('/language')
def set_language():
    session['language'] = request.args.get('lang')
    return redirect(request.args.get('next'))


@bp.route('/testss')
def test_api_request():
    if 'credentials' not in session:
        return redirect('authorize')

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **session['credentials'])

    calendar = googleapiclient.discovery.build(
        Config.API_SERVICE_NAME, Config.API_VERSION, credentials=credentials)

    create_calendar(calendar)

    # Save credentials back to session in case access token was refreshed.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    session['credentials'] = credentials_to_dict(credentials)
    flash('You have successfully authorized')
    return redirect(url_for('main.index'))


@bp.route('/authorize')
@login_required
def authorize():
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        Config.CLIENT_SECRETS_FILE, scopes=Config.SCOPES)

    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.
    flow.redirect_uri = url_for('main.oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline'
        # Enable incremental authorization. Recommended as a best practice.
    )

    # Store the state so the callback can verify the auth server response.
    session['state'] = state

    return redirect(authorization_url)


@bp.route('/oauth2callback')
@login_required
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        Config.CLIENT_SECRETS_FILE, scopes=Config.SCOPES, state=state)

    flow.redirect_uri = url_for('main.oauth2callback', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = request.url

    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    print(credentials)
    return redirect(url_for('main.test_api_request'))


@bp.route('/revoke')
@login_required
def revoke():
    if 'credentials' not in session:
        return ('You need to <a href="/authorize">authorize</a> before ' +
                'testing the code to revoke credentials.')

    credentials = google.oauth2.credentials.Credentials(
        **session['credentials'])

    revoke = requests.post('https://oauth2.googleapis.com/revoke',
                           params={'token': credentials.token},
                           headers={'content-type': 'application/x-www-form-urlencoded'})

    status_code = getattr(revoke, 'status_code')
    if status_code == 200:
        return ('Credentials successfully revoked.' + print_index_table())
    else:
        return ('An error occurred.' + print_index_table())


@bp.route('/clear')
@login_required
def clear_credentials():
    if 'credentials' in session:
        del session['credentials']
    return ('Credentials have been cleared.<br><br>' +
            print_index_table())


def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}


def print_index_table():
    return ('<table>' +
            '<tr><td><a href="/test">Test an API request</a></td>' +
            '<td>Submit an API request and see a formatted JSON response. ' +
            '    Go through the authorization flow if there are no stored ' +
            '    credentials for the user.</td></tr>' +
            '<tr><td><a href="/authorize">Test the auth flow directly</a></td>' +
            '<td>Go directly to the authorization flow. If there are stored ' +
            '    credentials, you still might not be prompted to reauthorize ' +
            '    the application.</td></tr>' +
            '<tr><td><a href="/revoke">Revoke current credentials</a></td>' +
            '<td>Revoke the access token associated with the current user ' +
            '    session. After revoking credentials, if you go to the test ' +
            '    page, you should see an <code>invalid_grant</code> error.' +
            '</td></tr>' +
            '<tr><td><a href="/clear">Clear Flask session credentials</a></td>' +
            '<td>Clear the access token currently stored in the user session. ' +
            '    After clearing the token, if you <a href="/test">test the ' +
            '    API request</a> again, you should go back to the auth flow.' +
            '</td></tr></table>')


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
            program_id = request.form['Course']
            weekday = request.form.getlist('weekday')
            start = request.form.getlist('start-time')
            end = request.form.getlist('end-time')

            student = User(name=name, username=login)
            student.program.append(Program.query.get(program_id))

            student.set_password(password)
            db.session.add(student)
            db.session.commit()

            datetimes = []

            for i in range(len(weekday)):
                date = datetime.datetime.combine(datetime.datetime.today(), datetime.datetime.min.time())

                while date.weekday() != int(weekday[i]) - 1:
                    date = date + datetime.timedelta(days=1)

                datetimes.append(date)

                date = datetime.datetime.combine(datetime.datetime.today(), datetime.datetime.min.time())

            create_schedule(datetimes, student.id, start, end, name)

            request.close()
            return redirect('/students', 302)
        programs = Program.query.all()
        students = []
        for i in User.query.all():
            if not is_tutor(i):
                students.append(i)
        return render_template("students.html", students=students, programs=programs)
    else:
        return redirect(url_for('main.index'))


@bp.route('/unread')
@login_required
def unread():
    current_user.last_message_read_time = datetime.datetime.utcnow()
    db.session.commit()
    messages = current_user.message_received.order_by(Task.timestamp.desc())

    return render_template('unread.html', messages=messages)


@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])


weekday_from_int = {
    1: "MO",
    2: "TU",
    3: 'WE',
    4: "TH",
    5: 'FR',
    6: 'ST',
    7: "SU"
}


def create_schedule(weekday, user_id, start, end, student_name):
    if 'credentials' not in session:
        print('HERE cred')

        return redirect(url_for('main.authorize'))
        # return redirect(url_for('main.test_api_request'))
    print('HERE')

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **session['credentials'])

    calendar = googleapiclient.discovery.build(
        Config.API_SERVICE_NAME, Config.API_VERSION, credentials=credentials)

    sch = []
    # date = date + datetime.timedelta(days=1)

    for i in range(len(weekday)):
        start_time = datetime.datetime.strptime(start[i], '%H:%M').time()
        end_time = datetime.datetime.strptime(end[i], '%H:%M').time()

        date_start = ((weekday[i] + datetime.timedelta(hours=start_time.hour, minutes=start_time.minute,
                                                       seconds=0)).isoformat()) + '+03:00'

        date_end = ((weekday[i] + datetime.timedelta(hours=end_time.hour, minutes=end_time.minute,
                                                     seconds=0)).isoformat()) + '+03:00'

        print(weekday_from_int[weekday[i].isoweekday()])
        json_date = {
            'summary': 'lesson with ' + student_name,
            'description': 'lesson with ' + student_name,
            'start': {
                'dateTime': date_start,
                'timeZone': 'Europe/Riga'
            },
            'end': {
                'dateTime': date_end,
                'timeZone': 'Europe/Riga'
            },
            'recurrence':
                [
                    "RRULE:FREQ=WEEKLY;COUNT=53;BYDAY=" + weekday_from_int[weekday[i].isoweekday()]
                ],
        }
        event = calendar.events().insert(calendarId=current_user.calendar_id, body=json_date).execute()
        print(event)
        sch.append(Schedule(start=start_time,
                            end=end_time, weekday_id=weekday[i],
                            user_id=user_id))

    db.session.add_all(sch)
    db.session.commit()


# particular student page
@bp.route('/students/<int:person>')
@login_required
def person(person):
    if current_user.tutor:
        person = User.query.get(person)

        # TODO for now only one program per student, later, add more!!!
        current_program = person.program[0]
        lesson = current_program.lesson
        homeworks, lessons, tests = [], lesson.copy(), []

        # trash_program imported
        trash_lessons = []
        trash_program = Program.query.get(2)
        for i in trash_program.lesson:

            if person in i.user:
                trash_lessons.append(i)

        lessons = lessons + trash_lessons

        # lessons from program and unique lessons from program
        for i in range(len(lessons)):

            # add homework
            flag = False
            if lessons[i].unique_homework:
                for j in lessons[i].unique_homework:
                    if j.user_id == person.id:
                        flag = True
                        homeworks.append(j)
                        break



            elif (not flag) or (not lessons[i].unique_homework):
                homeworks.append(lessons[i].homework)

            # add test
            tests.append(lessons[i].test)

            # add lesson
            if lessons[i].unique_lesson:
                for j in lessons[i].unique_lesson:
                    if j.user_id == person.id:
                        lessons[i] = j
                        break

        print(person.program)

        # lessons = lessons + trash_lessons

        return render_template('student.html', student=person, lessons=lessons, homeworks=homeworks,
                               tests=tests, program=person.program[0].program)
    else:
        return redirect(url_for('main.index'))


@bp.route('/delete_student/<int:student_id>')
@login_required
def delete_student(student_id):
    credentials = google.oauth2.credentials.Credentials(
        **session['credentials'])

    calendar = googleapiclient.discovery.build(
        Config.API_SERVICE_NAME, Config.API_VERSION, credentials=credentials)
    uniq_hw = Unique_Homework.query.filter_by(user_id=student_id).first()

    uniq_le = Unique_Lesson.query.filter_by(user_id=student_id).first()

    if uniq_le is not None:
        db.session.delete(uniq_le)
    # student = User.query.get(student_id)
    if uniq_hw is not None:
        db.session.delete(uniq_hw)

    db.session.commit()
    print("first delete")
    return redirect(url_for('main.delete_completely_student', student_id=student_id))


@bp.route('/notifications')
@bp.route('/delete_student_complete/<int:student_id>')
@login_required
def delete_completely_student(student_id):
    student = User.query.get(student_id)
    db.session.delete(student)
    db.session.commit()
    print("sedondd delete")
    return redirect(url_for('main.students'))


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
@login_required
def program(id):
    if current_user.tutor:
        program = Program.query.get(id)
        print(program.lesson)

        lessons = program.lesson
        homeworks = [i.homework for i in lessons]
        print(homeworks)
        tests = [i.test for i in lessons]
        return render_template("program.html", lessons=lessons, program_id=id, program=program,
                               homeworks=homeworks,

                               tests=tests)
    else:
        return redirect(url_for('main.index'))


@bp.route("/program/remove/<int:id>", methods=["GET", "POST"])
@login_required
def remove_program(id):
    if current_user.tutor:
        program = Program.query.get(id)
        for i in range(len(program.lesson)):

            # homework
            if program.lesson[i].unique_homework:
                db.session.delete(program.lesson[i].unique_homework)
                db.session.delete(program.lesson[i].homework)
            else:
                db.session.delete(program.lesson[i].homework)

            # test
            db.session.delete(program.lesson[i].test)
            # lesson
            if program.lesson[i].unique_lesson:
                db.session.delete(program.lesson[i].unique_lesson)
                db.session.delete(program.lesson[i])
            else:
                db.session.delete(program.lesson[i])
        db.session.delete(program)
        db.session.commit()
        '''
    lesson = Lesson.query.get(id)
    homework = Homework.query.filter_by(lesson_id=lesson.id).first()
    test = Test.query.filter_by(lesson_id=lesson.id).first()
    db.session.delete(homework)
    db.session.delete(test)
    db.session.delete(lesson)
    db.session.commit()
    request.close()
    '''

        return redirect(url_for('main.programs'))
    else:
        return redirect(url_for('main.index'))


# page with books, files etc.
@bp.route('/library', methods=['GET', 'POST'])
@login_required
def library():
    if current_user.tutor:


        lib = Library.query.all()


        if request.method == 'POST':
            name = request.form['name']
            avatar = request.files.get('avatar')

            print(avatar)
            filename = avatar.filename
            avatar.save(os.path.join("/Users/sofya/Downloads/students-master-2/app/uploads", filename))

            lib = Library(name=name, filename=filename)
            db.session.add(lib)
            db.session.commit()

            flash('successfully imported')

        return render_template('library.html', lib=lib)

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
@bp.route("/<int:user_id>/lesson/<int:id>/")
@login_required
def lesson(user_id, id):
    if current_user.tutor:
        lesson = Lesson.query.get(id)
        # from student page
        if user_id != 0:

            unique_lesson = Unique_Lesson.query.filter(
                Unique_Lesson.lesson_id == id, Unique_Lesson.user_id == user_id).first()
            print(unique_lesson)

            if unique_lesson:
                return render_template("lesson.html", lesson=unique_lesson, id=id)
            else:
                print("in program == 0 and not unique lesson")
                return render_template("lesson.html", lesson=lesson, id=id)
        # from program page
        return render_template("lesson.html", lesson=lesson, id=id)
    else:
        return redirect(url_for('main.index'))


@bp.route('/<int:course_id>/lessons/create/<int:user_id>', methods=['GET', 'POST'])
@login_required
def create_lesson(course_id, user_id):
    if current_user.tutor:
        if user_id == 0 and request.method != "POST":
            return render_template('create_lesson.html', programs=Program.query.all())
        elif user_id != 0 and request.method != "POST":
            user = User.query.get(user_id)
            # TODO THIS IS TRASH PROGRAM!!!!!!
            program = [Program.query.get(2)]
            # print(Program.query.filter(Program.user.contains(user)))
            return render_template('create_lesson.html', program=program)

        if request.method == "POST":
            if user_id == 0:
                title = request.form.get('LessonName')
                body = request.form.get('editordata')
                program = Program.query.get(course_id)
                lesson = Lesson(title=title, program=program, text=body)

                db.session.add(lesson)
                db.session.commit()
                request.close()
                return redirect(url_for('main.create_empty_homework', id=lesson.id))
            else:
                print("we are creating for user")
                title = request.form.get('LessonName')
                course = request.form.get('Course')
                body = request.form.get('editordata')

                # TODO THIS IS TRASH PROGRAM!!!!!!

                program = Program.query.get(2)
                lesson = Lesson(title=title, program=program, text=body, user=[User.query.get(user_id)], is_unique=1)
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
                # print(lesson, lesson.program)
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

@bp.route("/lesson/<int:id>/homework/<int:user_id>", methods=['GET', 'POST'])
@login_required
def homework(id, user_id):
    # if we are logged in using tutor account
    if current_user.tutor:
        lesson = Lesson.query.get(id)
        # if we are browsing homework from some student page
        if user_id != 0:

            # if we want to evaluate student's homework
            if request.method == "POST":
                # inputs
                grade = request.form.get('grade')
                comment = request.form.get('comment')

                # if we have UNIQUE homework for exact student
                if lesson.unique_homework and lesson.unique_homework.user_id == user_id:

                    # get student's submission
                    task = Task.query.filter(
                        Task.user_id == user_id and Task.unique_homework_id == lesson.unique_homework.id).first()
                    if task is not None:
                        current_user.last_message_read_time = datetime.datetime.utcnow()  # HOMEWORK GRADED

                        task.grade = grade
                        task.comment = comment
                        db.session.add(task)
                        db.session.commit()
                # if it is original homework for student
                else:
                    task = Task.query.filter(
                        Task.user_id == user_id and Task.homework_id == lesson.homework.id).first()
                    if task is not None:
                        current_user.last_message_read_time = datetime.datetime.utcnow()  # HOMEWORK GRADED
                        task.grade = grade
                        task.comment = comment
                        db.session.add(task)
                        db.session.commit()

                # redirect on this page
                return redirect(url_for('main.homework', user_id=user_id, id=id))

            # for GET method

            unique_homework = Unique_Homework.query.filter(
                Unique_Homework.user_id == user_id and Unique_Homework.lesson_id == id).first()
            if unique_homework:
                return render_template("homework.html", lesson=lesson, homework=unique_homework,
                                       task=unique_homework.task[0])
            else:
                task = Task.query.filter(Task.user_id == user_id, Task.homework_id == lesson.homework.id).first()
                return render_template("homework.html", lesson=lesson, homework=lesson.homework, task=task)

        # if we are browsing homework from some program page
        else:
            return render_template("homework.html", lesson=lesson, homework=lesson.homework, user_id=0)
    # if we have a smart student, who wants to find some info on website
    else:
        return redirect(url_for("main.index"))


'''
    if current_user.tutor:
        lesson = Lesson.query.get(id)

        if request.method == "POST":
            grade = request.form.get('grade')
            comment = request.form.get('comment')

            if lesson.unique_lesson:
                lesson.unique_homework.text = comment
                lesson.unique_homework.grade = grade

                db.session.add(lesson.unique_homework)
            else:
                lesson.homework.text = comment
                lesson.homework.grade = grade

                db.session.add(lesson.homework)

            db.session.commit()
            return redirect(url_for('main.homework', program=program, id=id))

    # method GET
    if program == 0:
        if lesson.unique_homework:
            return render_template("homework.html", lesson=lesson, homework=lesson.unique_homework)

    return render_template("homework.html", lesson=lesson, homework=lesson.homework)


else:
return redirect(url_for('main.index'))

'''


@bp.route('/uploads/<filename>')
def get_file(filename):
    return send_from_directory('uploads', filename, as_attachment=True)


@bp.route("/lesson/<int:id>/homework/<int:user_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_homework(id, user_id):
    if current_user.tutor:
        if request.method == 'POST':

            if user_id == 0:
                # print("измнения из программы")
                homework = Homework.query.get(id)
                # print('hi', id, homework[0].title, homework[1].title)

                homework.title = request.form.get('HomeworkName')
                homework.text = request.form.get('editordata')
                lesson = Lesson.query.get(id)
                lesson.homework = homework

                db.session.add(homework)
                db.session.commit()
                request.close()
                return redirect(url_for('main.homework', id=id, user_id=user_id))

            unique_homework = Unique_Homework.query.filter(Unique_Homework.user_id == user_id).first()
            if unique_homework is None:
                print("hi, were uni")
                title = request.form.get('HomeworkName')
                text = request.form.get('editordata')
                unique_homework = Unique_Homework(title=title, text=text, lesson_id=id, user_id=user_id)

            else:
                # not uni
                unique_homework.title = request.form.get('HomeworkName')
                unique_homework.text = request.form.get('editordata')
                lesson = Lesson.query.get(id)
                lesson.unique_homework.append(unique_homework)

            db.session.add(unique_homework)
            db.session.commit()
            request.close()
            return redirect(url_for('main.homework', id=id, program=0))
        # GET
        unique_homework = Unique_Homework.query.filter(Unique_Homework.user_id == user_id).first()

        if unique_homework is not None:
            return render_template("edit_homework.html", homework=unique_homework)
        else:
            lesson = Lesson.query.get(id)
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
            Test.query.get(id).qa = []
            for i in range(len(questions)):
                q = QA(test_id=id, question=questions[i], answer=answers[i])
                q_and_a.append(q)
            db.session.add_all(q_and_a)
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
        flash("Successfully opened")
        return redirect(url_for('main.person', person=user_id))
    else:
        return redirect(url_for('main.index'))


@bp.route("/students/remove/<int:student_id>/", methods=["GET", "POST"])
@login_required
def remove_student(student_id):
    if current_user.tutor:
        student = User.query.get(student_id)
        db.session.delete(student)

        db.session.commit()
        request.close()
        return redirect(url_for('main.students'))
    else:
        return redirect(url_for('main.index'))
