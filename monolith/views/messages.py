from flask import Blueprint, request, jsonify, session
from dateutil import parser
from flask.templating import render_template
from monolith.background import send_message
from monolith.database import User, db
messages = Blueprint('messages', __name__)


@messages.route('/message/send', methods = ['POST'])
def sendMessage():
    data = request.get_json()
    date = parser.parse(data['date'])
    result = send_message.apply_async((data,), eta = date)
    return jsonify({"msg":"Message sent!"})

@messages.route("/message/recipients", methods =["GET","POST"])
def chooseRecipient():
    if request.method == "GET":
        rec = db.session.query(User).filter(User.email != session["email"])
        return render_template("recipients.html", rec=rec)
