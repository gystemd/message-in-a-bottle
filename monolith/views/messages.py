from flask import Blueprint, request, redirect, abort
from flask_login.utils import login_required
from monolith.database import ContentFilter, UserContentFilter, Attachments, Message, User, Blacklist, db
from dateutil import parser
from flask.templating import render_template
from flask_login import current_user
from monolith.background import send_message as send_message_task
import base64
import re
import json

messages = Blueprint('messages', __name__)


@messages.route('/message/send/<id_message>', methods=['GET', 'POST'])
@login_required
def send_draft(id_message):
    if request.method == 'POST':
        send_message_async(request.form)
        db.session.query(Message).filter(Message.id == id_message).delete()
        db.session.commit()
        return render_template("send_message.html", form=dict(), message_ok=True)
    else:
        message = db.session.query(Message).filter(Message.id == id_message).first()
        receiver = db.session.query(User).filter(User.id == message.id_receiver).first().email
        date = message.date_delivery.isoformat()
        text = message.text
        form = dict(recipient=receiver, text=text, date=date, message_id=message.id)
        return render_template("send_message.html", form=form)


@login_required
@ messages.route('/message/send', methods=['GET', 'POST'])
def send_message():
    if request.method == 'POST':
        send_message_async(request.form)
        return render_template("send_message.html", form=dict(), message_ok=True)
    else:
        # landing from the recipients page, we want to populate the field with the chosen one
        recipient_message = request.args.get('recipient')
        recipient = recipient_message if recipient_message is not None else ''
        form = dict(recipient=recipient)
        return render_template("send_message.html", form=form)


@login_required
@ messages.route('/draft', methods=['POST'])
def draft():
    data = request.form
    save_message(data)
    return redirect('/mailbox/draft')


@ messages.route('/message/send/forward/<id_message>', methods=['POST'])
def send_forward_msg(id_message):
    recipient_message = request.form['recipient']
    text = db.session.query(Message).filter(Message.id == id_message).first().text
    form = dict(recipient=recipient_message, text=text, message_id=id_message)
    return render_template("send_message.html", form=form, forward=True)


@login_required
@ messages.route("/message/recipients", methods=["GET"])
def chooseRecipient():
    email = current_user.email
    recipients = db.session.query(User).filter(User.email != email).filter(User.is_admin.is_(False))
    form = dict(recipients=recipients)
    return render_template("recipients.html", form=form)


@login_required
@ messages.route('/message/recipients/<id_message>', methods=['GET'])
def choose_recipient_msg(id_message):
    email = current_user.email
    recipients = db.session.query(User).filter(User.email != email)
    form = dict(recipients=recipients, id_message=id_message)
    return render_template("recipients.html", form=form)


@login_required
@messages.route('/message/<message_id>')
def viewMessage(message_id):
    message = db.session.query(Message, User).filter(
        Message.id == int(message_id)
    ).join(User, Message.id_sender == User.id).first()

    if message is None or (int(message.Message.id_receiver) == current_user.id and not message.Message.delivered):
        abort(404)
    elif int(message.Message.id_sender) != current_user.id and int(message.Message.id_receiver) != current_user.id:
        abort(403)
    else:
        recipient = db.session.query(User).filter(
            User.id == message.Message.id_receiver
        ).first()

        # if message contains bad words it's not showed
        if int(message.Message.id_sender) != current_user.id:
            purified_message = purify_message(message.Message.text)
            if purified_message != message.Message.text:
                message.Message.text = purified_message

        images_db = db.session.query(Attachments).filter(Attachments.id == message_id).all()
        images = []
        for image in images_db:
            images.append(base64.b64encode(image.data).decode('ascii'))

        return render_template("message.html",
                               sender=message.User,
                               recipient=recipient,
                               message=message.Message,
                               images=images,
                               date='-')


def send_message_async(data):
    email = request.form['receiver']
    recipient = db.session.query(User.id).filter(User.email == email).all()
    result = db.session.query(Blacklist).filter(
        Blacklist.id_user == recipient[0].id).filter(
            Blacklist.id_blacklisted == current_user.id).all()
    date = parser.parse(data['date'] + '+0200')
    id_message = save_message(data)

    if not result:
        send_message_task.apply_async((id_message,), eta=date)


def save_message(data):

    message = Message()
    message.text = data['text']
    id_receiver = db.session.query(User).filter(
        User.email == data['receiver']).first().id
    message.id_receiver = id_receiver
    message.id_sender = current_user.id
    message.draft = True if 'draft' in data else False
    message.date_delivery = parser.parse(data['date'] + '+0200')

    db.session.add(message)
    db.session.commit()

    for file in request.files:
        attachment = Attachments()
        attachment.id_message = message.id
        attachment.data = request.files[file].read()
        db.session.add(attachment)

    db.session.commit()

    return message.id


def purify_message(msg):
    if current_user is None or not hasattr(current_user, 'id'):
        return msg

    list = db.session.query(UserContentFilter.id_content_filter).filter(
        UserContentFilter.id_user == current_user.id
    )

    personal_filters = db.session.query(ContentFilter, UserContentFilter).filter(
        ContentFilter.id.in_(list)
    ).join(UserContentFilter, isouter=True).union_all(
        db.session.query(ContentFilter, UserContentFilter).filter(
            ContentFilter.private.is_(False), UserContentFilter.active.is_(True)
        ).join(UserContentFilter, isouter=True)
    ).all()

    purified_message = msg

    for personal_filter in personal_filters:
        print(personal_filter.ContentFilter.words)
        for word in json.loads(personal_filter.ContentFilter.words):
            insensitive_word = re.compile(re.escape(word), re.IGNORECASE)
            purified_message = insensitive_word.sub('*' * len(word), purified_message)
    return purified_message
