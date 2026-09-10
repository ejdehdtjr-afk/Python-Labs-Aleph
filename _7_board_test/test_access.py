import tempfile
import unittest
import sqlite3
from contextlib import closing
from pathlib import Path
from app import create_app

class AccessTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'test.db'
        self.app = create_app(self.path, True)
        self.app.test_cli_runner().invoke(args=['seed-demo'])
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def post(self, client, path, **data):
        client.get('/')
        with client.session_transaction() as session:
            data['csrf'] = session['csrf']
        return client.post(path, data=data)

    def login(self, name, client=None):
        client = client or self.client
        return self.post(client, '/login', username=name, password='CafeTest123!')

    def test_access_matrix(self):
        for name, gold, admin in [(None,401,401),('normal',403,403),('gold',200,403),('admin',200,200)]:
            client = self.app.test_client()
            if name:
                self.login(name, client)
            self.assertEqual(client.get('/gold').status_code, gold)
            self.assertEqual(client.get('/admin').status_code, admin)

    def test_registration_cannot_choose_role(self):
        self.post(self.client, '/register', username='newuser', password='CafeTest123!', role='2')
        with closing(sqlite3.connect(self.path)) as conn:
            self.assertEqual(conn.execute("SELECT role FROM users WHERE username='newuser'").fetchone()[0], 0)

    def test_live_role_change_delete_and_admin_protection(self):
        self.login('normal')
        admin = self.app.test_client()
        self.login('admin', admin)
        self.assertEqual(self.post(self.client, '/admin/users/2', username='hacked', role='2').status_code,403)
        self.post(admin, '/admin/users/1', username='normal', role='1')
        self.assertEqual(self.client.get('/gold').status_code,200)
        self.post(admin, '/admin/users/1', username='normal', role='0')
        self.assertEqual(self.client.get('/gold').status_code,403)
        self.post(admin, '/admin/users/3', action='delete')
        self.assertEqual(admin.get('/admin').status_code,200)
        self.post(admin, '/admin/users/1', action='delete')
        self.assertEqual(self.client.get('/gold').status_code,401)

    def test_csrf_and_invalid_role(self):
        self.login('admin')
        self.assertEqual(self.client.post('/admin/users/1', data={'role':'2'}).status_code,400)
        self.assertEqual(self.post(self.client, '/admin/users/1', username='normal', role='9').status_code,400)

if __name__ == '__main__':
    unittest.main(verbosity=2)
