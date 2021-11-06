import unittest

from monolith.tests.test_base import TestBase


class TestApp(TestBase):
    def test_user_info(self):
        self.login(self.sender, "1234")
        reply = self.app.get("/userinfo")
        self.assertIn(b'Profile info', reply.data)
        self.logout()

    def test_user_list(self):
        self.login(self.sender, "1234")
        reply = self.app.get("/users")
        self.assertIn(b'User List', reply.data)
        self.logout()

    def test_recipients(self):
        self.login(self.sender, "1234")
        reply = self.app.get("/message/recipients")
        self.assertIn(b'prova1@gmail.com', reply.data)
        self.logout()

    def test_create_user_page(self):
        self.login(self.sender, "1234")
        reply = self.app.get("/create_user")
        self.assertIn(b'email', reply.data)

        reply = self.app.post("/create_user",
                              data=dict(
                                  email='prova@gmail.com',
                                  firstname='Prova',
                                  lastname='Prova',
                                  password='1234',
                                  dateofbirth='01/01/2001'
                              ),
                              follow_redirects=True)
        self.assertIn(b'Email already in use', reply.data)

        self.logout()

    def test_content_filter(self):
        self.login(self.sender, "1234")
        reply = self.app.get('/userinfo/content_filter')
        self.assertIn(b'list', reply.data)

        reply = self.app.get('/userinfo/content_filter/10')
        self.assertEqual(reply.status, '404 NOT FOUND')

        reply = self.app.put('/userinfo/content_filter/1', data=dict(active=True))
        self.assertEqual(reply.status, '200 OK')

        reply = self.app.get('/userinfo/content_filter/1')
        self.assertIn(b'id', reply.data)

        self.logout()
