from flask import Blueprint, render_template, redirect, flash, request, url_for
from flask_login import login_user, logout_user, login_required, current_user
from card_data.db_session import create_session
from card_data.users import User
from forms.user import LoginForm, RegisterForm
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        db_sess = create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()

        if user and check_password_hash(user.hashed_password, form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash('Вы успешно вошли в систему!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Неверный email или пароль', 'error')
        db_sess.close()

    return render_template('login.html', title='Вход', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = create_session()

        if db_sess.query(User).filter(User.email == form.email.data).first():
            flash('Пользователь с таким email уже существует', 'error')
            return render_template('register.html', title='Регистрация', form=form)

        if db_sess.query(User).filter(User.name == form.name.data).first():
            flash('Пользователь с таким именем уже существует', 'error')
            return render_template('register.html', title='Регистрация', form=form)

        user = User(
            name=form.name.data,
            email=form.email.data,
            hashed_password=generate_password_hash(form.password.data)
        )

        db_sess.add(user)
        db_sess.commit()
        db_sess.close()

        flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', title='Регистрация', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))