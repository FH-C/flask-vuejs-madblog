from flask import jsonify, g

from app.models import db
from app.api import bp
from app.api.auth import basic_auth, token_auth


@bp.route('/tokens', methods=['POST'])
@basic_auth.login_required
def get_token():
    token = g.current_user.get_jwt()
    g.current_user.ping()
    g.current_user.save()
    return jsonify({'token': token})
