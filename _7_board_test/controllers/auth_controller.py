"""회원가입 / 로그인."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
  data = request.get_json(silent=True) or {}
  if not data.get('username') or not data.get('password'):
    return jsonify({'msg': 'username, password 는 필수입니다.'}), 400
  if User.query.filter_by(username=data['username']).first():
    return jsonify({'msg': '이미 존재하는 사용자입니다.'}), 400

  user = User(username=data['username'],
              password=generate_password_hash(data['password']))
  db.session.add(user)
  db.session.commit()
  return jsonify({'msg': '회원가입 성공'}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
  data = request.get_json(silent=True) or {}
  user = User.query.filter_by(username=data.get('username')).first()
  if not user or not check_password_hash(user.password, data.get('password', '')):
    return jsonify({'msg': '아이디 또는 비밀번호가 잘못되었습니다.'}), 401

  token = create_access_token(identity=str(user.id))
  return jsonify(access_token=token, username=user.username)
