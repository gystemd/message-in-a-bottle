from datetime import date
import pytest
import unittest
import wtforms as f

from monolith.database import db, User, Message
from monolith.tests.test_base import TestBase
from monolith.app import app as tested_app

class TestApp(TestBase):

    def test_message_draft(self):

        self.login(self.sender, "1234")

        reply = self.app.get("/draft")
        self.assertEqual(reply.status, '405 METHOD NOT ALLOWED')

        message = dict(
            receiver=self.receiver,
            date='2020-10-26T01:01',
            text='Draft message')

        reply = self.app.post("/draft",
                              data=message)
        self.assertEqual(reply.status, '302 FOUND')

        self.logout()

    def test_message_send(self):

        #reply = app.get("/message/send")
        # self.assertIn(b"Redirecting...",reply.data)

        self.login(self.sender, "1234")

        reply = self.app.get("/message/send")
        self.assertEqual(reply.status, '200 OK')

        message = dict(
            receiver=self.receiver,
            date='2020-10-26t01:01',
            text='test message')

        reply = self.app.post("/message/send",
                              data=message)
        self.assertEqual(reply.status, '200 OK')
        self.assertIn(b"Message sent correctly!", reply.data)

        # User.query.filter_by(email="prova_001@example.it").delete()

        self.logout()

    def test_message_send_recipient_not_exists(self):

        self.login(self.sender, "1234")

        message = dict(
            receiver=self.receiver,
            date='2020-10-26T01:01',
            text='Test message')

        reply = self.app.post("/message/send",
                              data=message,
                              follow_redirects=True)
        #self.assertEqual(reply.status, '400 Bad Request')
        self.logout()

    def test_message_send_recipient_is_sender(self):

        self.login(self.sender, "1234")

        message = dict(
            receiver=self.receiver,
            date='2020-10-26T01:01',
            text='Test message 1234')

        reply = self.app.post("/message/send",
                              data=message,
                              follow_redirects=True)
        self.assertEqual(reply.status, '200 OK')

        with tested_app.app_context():
            result = db.session.query(Message).filter(
                Message.text == 'Test message 1234').first()
            self.assertEqual('Test message 1234', result.text) 

        self.logout()

    def test_message_view(self):

        self.login(self.sender, "1234")

        id = 4

        reply = self.app.get("/message/" + str(id))
        self.assertEqual(reply.status, '403 FORBIDDEN')

        reply = self.app.get("/message/" + str(id - 2748923748927489))
        self.assertEqual(reply.status, '404 NOT FOUND')

        reply = self.app.get("/message/2")

        self.logout()

    def test_recipients(self):

        self.login(self.sender, "1234")

        self.app.get('/message/recipients')

        self.logout()

    def test_send_image(self):

        self.login(self.sender, "1234")
        with open("monolith/index.png", "rb") as image:
            f = image.read()
            data = dict(file=f)
            message = dict(
                receiver=self.receiver,
                date='2020-10-26t01:01',
                text='test message image',
                file=image)

            reply = self.app.post("/message/send", content_type='multipart/form-data',
                                  data=message, follow_redirects=True)
            reply = self.app.get('/mailbox/sent')
            self.assertIn(b"test message image", reply.data)
        self.logout()
