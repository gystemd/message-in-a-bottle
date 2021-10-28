from flask import Blueprint, redirect, render_template, request

from monolith.database import User, db
from monolith.forms import UserForm
from flask_login import current_user

users = Blueprint('users', __name__)


@users.route('/users')
def _users():
    _users = db.session.query(User)
    return render_template("users.html", users=_users)


@users.route('/create_user', methods=['POST', 'GET'])
def create_user():
    form = UserForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            new_user = User()
            form.populate_obj(new_user)
            """ Password should be hashed with some salt. For example if you choose a hash function x,
            where x is in [md5, sha1, bcrypt], the hashed_password should be = x(password + s) where
            s is a secret key.
            """
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            db.session.commit()
            return redirect('/')
    elif request.method == 'GET':
        return render_template('create_user.html', form=form)
    else:
        raise RuntimeError('This should not happen!')


@users.route('/delete_user')
def delete_user():
    User.query.filter_by(id=current_user.id).delete()
    db.session.commit()
    return redirect('/')


@users.route('/userinfo')
def get_user_info():
    user = db.session.query(User).filter(current_user.id == User.id).all()
    return render_template('user_info.html', user=user)
