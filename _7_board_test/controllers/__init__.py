"""컨트롤러(블루프린트) 묶음. app.py 가 이 목록을 한 번에 등록한다."""
from .auth_controller import auth_bp
from .page_controller import page_bp
from .post_controller import post_bp
from .public_controller import public_bp
from .security_controller import security_bp

all_blueprints = (page_bp, auth_bp, post_bp, security_bp, public_bp)

__all__ = ['all_blueprints', 'page_bp', 'auth_bp', 'post_bp',
           'security_bp', 'public_bp']
