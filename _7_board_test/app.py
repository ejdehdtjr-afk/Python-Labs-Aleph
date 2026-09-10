"""카페이야기: Flask + SQLite 접근 제어 실습. python app.py"""
import sys
from pathlib import Path
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / 'vendor'))
import secrets
import sqlite3
from functools import wraps
from flask import Flask, g, session, request, render_template, redirect, url_for, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash

ROLES = {0: '일반', 1: '골드', 2: '관리자'}

def create_app(database=None, testing=False):
    app = Flask(__name__)
    app.config.update(SECRET_KEY=secrets.token_hex(32), TESTING=testing,
                      DATABASE=str(database or BASE / 'board.db'), SESSION_COOKIE_HTTPONLY=True,
                      SESSION_COOKIE_SAMESITE='Lax')

    def db():
        if 'db' not in g:
            g.db = sqlite3.connect(app.config['DATABASE'])
            g.db.row_factory = sqlite3.Row
            g.db.execute('PRAGMA foreign_keys=ON')
        return g.db

    @app.teardown_appcontext
    def close_db(error):
        conn = g.pop('db', None)
        if conn is not None:
            conn.close()

    with app.app_context():
        db().executescript('''
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL,
          password TEXT NOT NULL, role INTEGER NOT NULL DEFAULT 0 CHECK(role IN (0,1,2)));
        CREATE TABLE IF NOT EXISTS posts(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL
          REFERENCES users(id) ON DELETE CASCADE, title TEXT NOT NULL, body TEXT NOT NULL);
        ''')
        db().commit()

    @app.before_request
    def load_user():
        g.user = db().execute('SELECT * FROM users WHERE id=?', (session.get('user_id'),)).fetchone()
        session.setdefault('csrf', secrets.token_hex(32))
        if request.method == 'POST' and not secrets.compare_digest(request.form.get('csrf', ''), session['csrf']):
            abort(400, description='요청 확인 값이 올바르지 않습니다. 화면을 새로고침하세요.')

    @app.context_processor
    def context():
        return dict(roles=ROLES)

    def require_role(minimum):
        def decorate(fn):
            @wraps(fn)
            def wrapped(*args, **kwargs):
                if not g.user:
                    return render_template('result.html', status=401, required=minimum,
                                           message='로그인이 필요합니다.'), 401
                if g.user['role'] < minimum:
                    return render_template('result.html', status=403, required=minimum,
                                           message='현재 회원 등급으로 접근할 수 없습니다.'), 403
                return fn(*args, **kwargs)
            return wrapped
        return decorate

    @app.route('/')
    def index():
        posts = db().execute('SELECT p.*, u.username FROM posts p JOIN users u ON u.id=p.user_id ORDER BY p.id DESC').fetchall()
        return render_template('index.html', posts=posts)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            name, password = request.form.get('username', '').strip(), request.form.get('password', '')
            if not 2 <= len(name) <= 40 or not 8 <= len(password) <= 128:
                flash('아이디는 2~40자, 비밀번호는 8~128자로 입력하세요.')
            else:
                try:
                    db().execute('INSERT INTO users(username,password,role) VALUES (?,?,0)', (name, generate_password_hash(password)))
                    db().commit()
                    flash('일반(0) 등급으로 가입했습니다. 로그인하세요.')
                    return redirect(url_for('login'))
                except sqlite3.IntegrityError:
                    db().rollback()
                    flash('이미 사용 중인 아이디입니다.')
        return render_template('auth.html', signup=True)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            user = db().execute('SELECT * FROM users WHERE username=?', (request.form.get('username', ''),)).fetchone()
            if user and check_password_hash(user['password'], request.form.get('password', '')):
                session.clear()
                session['user_id'] = user['id']
                return redirect(url_for('index'))
            flash('아이디 또는 비밀번호가 올바르지 않습니다.')
        return render_template('auth.html', signup=False)

    @app.post('/logout')
    def logout():
        session.clear()
        return redirect(url_for('index'))

    @app.post('/posts')
    @require_role(0)
    def post():
        title, body = request.form.get('title', '').strip(), request.form.get('body', '').strip()
        if not title or not body or len(title) > 100 or len(body) > 5000:
            abort(400, description='제목(100자 이내)과 본문(5000자 이내)을 입력하세요.')
        db().execute('INSERT INTO posts(user_id,title,body) VALUES (?,?,?)', (g.user['id'], title, body))
        db().commit()
        return redirect(url_for('index'))

    @app.get('/gold')
    @require_role(1)
    def gold():
        return render_template('result.html', status=200, required=1, message='골드 라운지 접근이 허용되었습니다.')

    @app.get('/admin')
    @require_role(2)
    def admin():
        users = db().execute('SELECT id,username,role FROM users ORDER BY id').fetchall()
        return render_template('admin.html', users=users)

    @app.post('/admin/users/<int:user_id>')
    @require_role(2)
    def edit_user(user_id):
        target = db().execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
        if not target:
            abort(404)
        if user_id == g.user['id']:
            flash('실습 관리자 잠금 방지를 위해 본인 계정은 수정·삭제할 수 없습니다.')
            return redirect(url_for('admin'))
        if request.form.get('action') == 'delete':
            db().execute('DELETE FROM users WHERE id=?', (user_id,))
            flash('회원과 해당 회원의 게시글을 삭제했습니다.')
        else:
            role = request.form.get('role')
            name = request.form.get('username', '').strip()
            if role not in ('0', '1', '2') or not 2 <= len(name) <= 40:
                abort(400, description='회원명 또는 권한 값이 올바르지 않습니다.')
            try:
                db().execute('UPDATE users SET username=?,role=? WHERE id=?', (name, int(role), user_id))
            except sqlite3.IntegrityError:
                db().rollback()
                flash('이미 사용 중인 아이디입니다.')
                return redirect(url_for('admin'))
            flash('회원 정보를 수정했습니다. 다음 요청부터 변경된 DB 권한이 적용됩니다.')
        db().commit()
        return redirect(url_for('admin'))

    @app.errorhandler(400)
    @app.errorhandler(404)
    def error(err):
        return render_template('result.html', status=err.code, required=None, message=err.description), err.code

    @app.cli.command('seed-demo')
    def seed_demo():
        """명시적으로 실습 계정 생성. 기존 계정은 변경하지 않음."""
        for name, role in [('normal', 0), ('gold', 1), ('admin', 2)]:
            db().execute('INSERT OR IGNORE INTO users(username,password,role) VALUES (?,?,?)',
                         (name, generate_password_hash('CafeTest123!'), role))
        db().commit()
        print('실습 계정: normal / gold / admin, 비밀번호: CafeTest123!')

    return app

if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=5000, debug=False)
