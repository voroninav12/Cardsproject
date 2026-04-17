import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, redirect, request, jsonify
from card_data import db_session
from flask_login import LoginManager, current_user, login_required
from sqlalchemy.orm import joinedload

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cardscards123'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

db_session.global_init("cards.db")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    from card_data.users import User
    try:
        user = db_sess.query(User).get(user_id)
        return user
    finally:
        db_sess.close()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
@login_required
def dashboard():
    from card_data.db_session import create_session
    from card_data.users import User
    from card_data.cards import Template

    db_sess = create_session()
    try:
        user = db_sess.query(User).options(
            joinedload(User.templates)
        ).filter(User.id == current_user.id).first()

        personal_templates = db_sess.query(Template).options(
            joinedload(Template.cards)
        ).filter(Template.user_id == current_user.id).all()

        total_cards = sum(len(template.cards) for template in personal_templates)

        all_public_templates = db_sess.query(Template).filter(
            Template.is_private == False
        ).count()

        return render_template("dashboard.html",
                               current_user_data=user,
                               templates=personal_templates,
                               total_cards=total_cards,
                               public_templates_count=all_public_templates)
    except Exception as e:
        print(f"Ошибка в dashboard: {e}")
        return render_template("dashboard.html",
                               current_user_data=None,
                               templates=[],
                               total_cards=0,
                               public_templates_count=0)
    finally:
        db_sess.close()


@app.route("/health")
def health_check():
    return jsonify({"status": "healthy", "message": "Cards is running"})


@app.route("/features")
def features():
    return render_template("features.html")


if __name__ == '__main__':
    from logics import auth_logic, templates_logic, cards_logic

    app.register_blueprint(auth_logic.auth_bp, url_prefix='/auth')
    app.register_blueprint(templates_logic.templates_bp, url_prefix='/templates')
    app.register_blueprint(cards_logic.cards_bp, url_prefix='/cards')

    for rule in app.url_map.iter_rules():
        print(f"{rule.rule} -> {rule.endpoint}")

    app.run(host='0.0.0.0', debug=True)