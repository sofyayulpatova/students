from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user, login_user, login_required, logout_user
from app.models import User, Program, Lesson, Unique_Lesson, Homework, Test, Unique_Homework, Profile
from app.main.forms import LoginForm
from werkzeug.urls import url_parse
from app.student import bp
from app import db
from functools import wraps


@bp.route('/lessons')
@login_required
def lesson():
    print(current_user.lesson)
    return render_template("hehehe.html", lessons={{url_for('student.lessons')}})


@bp.route('/homework')
@login_required
def homework():
    return render_template("hehehe.html")


@bp.route('/tests')
@login_required
def tests():
    return render_template("hehehe.html")


@bp.route('/main_page')
@login_required
def main_page():
    return render_template("hehehe.html")
