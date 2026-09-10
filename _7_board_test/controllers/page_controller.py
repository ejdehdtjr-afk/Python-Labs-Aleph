"""화면(HTML) 라우트만 모음. 데이터는 각 페이지의 JS 가 API 로 가져온다."""
from flask import Blueprint, render_template

page_bp = Blueprint('page', __name__)


@page_bp.route('/')
def index():
  return render_template('index.html')


@page_bp.route('/dashboard')
def dashboard():
  """보안 이벤트 대시보드 (n8n 이 저장한 허용/거부 기록)."""
  return render_template('dashboard.html')


@page_bp.route('/public-posts')
def public_posts_page():
  return render_template('public_posts.html')


@page_bp.route('/public-posts/<int:uc_seq>')
def public_post_detail_page(uc_seq):
  return render_template('public_detail.html', uc_seq=uc_seq)
