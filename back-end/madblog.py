from app.app_create import app
from app.models import User, db

app


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}