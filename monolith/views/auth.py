from flask import Blueprint, redirect, render_template, session
from flask_login import login_user, logout_user

from monolith.database import User, db
from monolith.forms import LoginForm

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    is_reported = False
    form = LoginForm()
    if form.validate_on_submit():
        session["email"], session["password"] = form.data['email'], form.data['password']
        q = db.session.query(User).filter(User.email == session["email"])
        user = q.first()
        if user.is_reported:
            is_reported = True
            return redirect('/create_user')
        if user is not None and user.authenticate(session["password"]):
            login_user(user)
            return redirect('/')
    return render_template('login.html', form=form, is_reported=is_reported)


@auth.route("/logout")
def logout():
    logout_user()
    return redirect('/')
