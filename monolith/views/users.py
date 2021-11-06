from flask import Blueprint, redirect, render_template, request
from flask_login.utils import login_fresh, login_required
from monolith.database import User, Blacklist, Reports, db
from monolith.forms import UserForm
from flask_login import current_user

NUM_REPORTS = 2

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
            result = db.session.query(User).filter(User.email == new_user.email).all()
            reported_user = db.session.query(User).filter(User.email == new_user.email).filter(
                User.firstname == new_user.firstname).filter(
                    User.lastname == new_user.lastname).filter(User.date_of_birth == new_user.date_of_birth).first()
            if not result and not reported_user:
                new_user.set_password(form.password.data)
                db.session.add(new_user)
                db.session.commit()
                return redirect('/')
            elif reported_user.is_reported:
                is_reported = True
                return render_template('create_user.html', form=form, is_reported=is_reported)
            return render_template("create_user.html", emailError=True, form=form)
    elif request.method == 'GET':
        return render_template('create_user.html', form=form)


@login_required
@users.route('/delete_user')
def delete_user():
    User.query.filter_by(id=current_user.id).delete()
    db.session.commit()
    return redirect('/')


@login_required
@users.route('/userinfo')
def get_user_info():
    user = db.session.query(User).filter(current_user.id == User.id).all()
    return render_template('user_info.html', user=user)


@login_required
@users.route('/blacklist/add', methods=['GET', 'POST'])
def add_user_to_blacklist():
    if request.method == 'POST':
        blacklist = Blacklist()
        blacklist.id_user = current_user.id
        email = request.form.get('email')
        blacklist.id_blacklisted = db.session.query(User.id).filter(User.email == email)
        db.session.add(blacklist)
        db.session.commit()
        return redirect('/blacklist')
    else:
        blacklist = db.session.query(User.id).join(Blacklist, Blacklist.id_blacklisted == User.id).filter(
            Blacklist.id_user == current_user.id)
        users = db.session.query(User).filter(User.email != current_user.email).filter(User.id.not_in(blacklist))
        return render_template('add_to_blacklist.html', users=users)


@login_required
@users.route('/blacklist', methods=['GET'])
def get_blacklist():
    blacklist = db.session.query(Blacklist, User).filter(
        Blacklist.id_blacklisted == User.id).filter(
            Blacklist.id_user == current_user.id).all()
    return render_template('blacklist.html', blacklist=blacklist)


@login_required
@users.route('/blacklist/remove', methods=['GET', 'POST'])
def remove_user_from_blacklist():
    if request.method == 'POST':
        email = request.form["radioEmail"]
        id_blklst = db.session.query(User.id).filter(User.email == email).all()
        db.session.query(Blacklist).filter(Blacklist.id_blacklisted == id_blklst[0].id).delete()
        db.session.commit()
        return redirect('/blacklist')
    else:
        blacklist = db.session.query(Blacklist, User).filter(
            Blacklist.id_blacklisted == User.id).filter(
                Blacklist.id_user == current_user.id).all()
        return render_template('blacklist.html', blacklist=blacklist)


@login_required
@users.route('/report', methods=['GET'])
def get_report():
    report = db.session.query(Reports, User).filter(
        Reports.id_reported == User.id).filter(
            Reports.id_user == current_user.id).all()
    return render_template('report.html', report=report)


@login_required
@users.route('/report/add', methods=['GET', 'POST'])
def report_user():
    if request.method == 'POST':
        report = Reports()
        report.id_user = current_user.id
        email = request.form.get('email')
        report.id_reported = db.session.query(User.id).filter(User.email == email)
        db.session.add(report)
        db.session.commit()

        num_reports = db.session.query(Reports).filter(Reports.id_reported == report.id_reported).all()
        print(len(num_reports))
        if len(num_reports) == NUM_REPORTS:
            print('dentro if')
            user = db.session.query(Reports, User).filter(report.id_reported == User.id).first()
            print(user)
            user.User.is_reported = True
            db.session.commit()

        return redirect('/report')
    else:
        report = db.session.query(User.id).join(Reports, Reports.id_reported == User.id).filter(
            Reports.id_user == current_user.id)
        users = db.session.query(User).filter(User.email != current_user.email).filter(User.id.not_in(report)).filter(
            User.is_reported == False)
        return render_template('report_user.html', users=users)
