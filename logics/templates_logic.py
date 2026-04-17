from flask import Blueprint, render_template, redirect, flash, request, jsonify, url_for
from flask_login import login_required, current_user
from card_data.db_session import create_session
from card_data.cards import Template
from forms.cards import TemplateForm
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, func
import os
from werkzeug.utils import secure_filename
from datetime import datetime

templates_bp = Blueprint('templates', __name__)

DESIGN_PRESETS = {
    'game': {
        'name': 'Игровая колода',
        'width': 63,
        'height': 88,
        'background_color': '#E8D9C5',
        'back_title': 'Колода карт',
        'back_background_color': '#2C3E50',
        'category': 'game',
        'description': 'Классический размер для настольных игр и коллекционных карт.'
    },
    'business': {
        'name': 'Бизнес-визитка',
        'width': 90,
        'height': 50,
        'background_color': '#FFFFFF',
        'back_title': 'Контакты',
        'back_background_color': '#F4F6F9',
        'category': 'business',
        'description': 'Европейский стандарт для деловых контактов и презентаций.'
    },
    'creative': {
        'name': 'Арт-карточка',
        'width': 100,
        'height': 70,
        'background_color': '#FF6B6B',
        'back_title': 'Творчество',
        'back_background_color': '#FFE66D',
        'category': 'creative',
        'description': 'Яркий формат для творческих проектов и идей.'
    },
    'minimalist': {
        'name': 'Минимализм',
        'width': 85,
        'height': 55,
        'background_color': '#F5F5F5',
        'back_title': 'Simple',
        'back_background_color': '#E8E8E8',
        'category': 'minimalist',
        'description': 'Лаконичный дизайн без лишних деталей.'
    },
    'elegant': {
        'name': 'Элегантная карта',
        'width': 80,
        'height': 110,
        'background_color': '#F8F0E3',
        'back_title': 'Elegance',
        'back_background_color': '#D4B8A4',
        'category': 'elegant',
        'description': 'Изысканный вертикальный формат для приглашений.'
    },
    'modern': {
        'name': 'Современная карта',
        'width': 95,
        'height': 65,
        'background_color': '#2C3E50',
        'back_title': 'Modern',
        'back_background_color': '#34495E',
        'category': 'modern',
        'description': 'Универсальный современный формат.'
    }
}


@templates_bp.route('/create_template', methods=['GET', 'POST'])
@login_required
def create_template():
    form = TemplateForm()

    preset = request.args.get('preset')
    if preset and preset in DESIGN_PRESETS:
        preset_data = DESIGN_PRESETS[preset]
        form.name.data = preset_data['name']
        form.description.data = preset_data['description']
        form.width.data = preset_data['width']
        form.height.data = preset_data['height']
        form.background_color.data = preset_data['background_color']
        form.back_title.data = preset_data['back_title']
        form.back_background_color.data = preset_data['back_background_color']
        form.category.data = preset_data['category']

    if form.validate_on_submit():
        db_sess = create_session()
        try:
            template = Template(
                name=form.name.data,
                description=form.description.data,
                width=form.width.data,
                height=form.height.data,
                background_color=form.background_color.data,
                back_title=form.back_title.data,
                back_background_color=form.back_background_color.data,
                category=form.category.data,
                tags=form.tags.data,
                is_private=form.is_private.data,
                user_id=current_user.id
            )

            if form.back_image_file.data and form.back_image_file.data.filename:
                filename = secure_filename(form.back_image_file.data.filename)
                unique_filename = f"{current_user.id}_back_{int(datetime.now().timestamp())}_{filename}"
                filepath = os.path.join('static/uploads', unique_filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                form.back_image_file.data.save(filepath)
                template.back_image_filename = unique_filename

            db_sess.add(template)
            db_sess.commit()

            status = "личным" if template.is_private else "публичным"
            flash(f'Шаблон успешно создан! Шаблон является {status}.', 'success')
            return redirect(url_for('templates.my_templates'))

        except Exception as e:
            db_sess.rollback()
            flash(f'Ошибка при создании шаблона: {e}', 'error')
        finally:
            db_sess.close()

    return render_template('create_template.html', title='Создание шаблона', form=form, presets=DESIGN_PRESETS)


@templates_bp.route('/apply_preset', methods=['POST'])
@login_required
def apply_preset():
    try:
        data = request.get_json()
        preset_key = data.get('preset', 'game')
        preset = DESIGN_PRESETS.get(preset_key, DESIGN_PRESETS['game'])
        return jsonify({'success': True, 'preset': preset})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@templates_bp.route('/my_templates')
@login_required
def my_templates():
    db_sess = create_session()
    try:
        templates = db_sess.query(Template).options(
            joinedload(Template.cards)
        ).filter(Template.user_id == current_user.id).all()

        total_cards = sum(len(template.cards) for template in templates)

        return render_template('my_templates.html',
                               title='Мои шаблоны',
                               templates=templates,
                               total_cards=total_cards)
    except Exception as e:
        flash(f'Ошибка при загрузке шаблонов: {e}', 'error')
        return render_template('my_templates.html',
                               title='Мои шаблоны',
                               templates=[],
                               total_cards=0)
    finally:
        db_sess.close()


@templates_bp.route('/public_templates')
def public_templates():
    db_sess = create_session()
    try:
        category = request.args.get('category', '')
        search = request.args.get('search', '')
        sort_by = request.args.get('sort', 'newest')

        query = db_sess.query(Template).options(
            joinedload(Template.user),
            joinedload(Template.cards)
        ).filter(Template.is_private == False)

        if category and category != 'all':
            query = query.filter(Template.category == category)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Template.name.ilike(search_term),
                    Template.description.ilike(search_term),
                    Template.tags.ilike(search_term)
                )
            )

        if sort_by == 'popular':
            query = query.order_by(Template.likes_count.desc())
        elif sort_by == 'cards':
            query = query.outerjoin(Template.cards)
            query = query.group_by(Template.id).order_by(func.count(Template.cards).desc())
        elif sort_by == 'views':
            query = query.order_by(Template.views_count.desc())
        else:
            query = query.order_by(Template.created_date.desc())

        templates = query.all()

        total_cards = sum(len(template.cards) for template in templates)

        author_ids = set()
        for template in templates:
            if template.user_id:
                author_ids.add(template.user_id)
        authors_count = len(author_ids)

        categories_stats = {}
        for template in templates:
            cat = template.category
            categories_stats[cat] = categories_stats.get(cat, 0) + 1

        return render_template('public_templates.html',
                               title='Публичные шаблоны',
                               templates=templates,
                               total_cards=total_cards,
                               authors_count=authors_count,
                               categories_stats=categories_stats,
                               current_category=category,
                               search_query=search,
                               sort_by=sort_by)
    except Exception as e:
        flash(f'Ошибка при загрузке публичных шаблонов: {e}', 'error')
        return render_template('public_templates.html',
                               title='Публичные шаблоны',
                               templates=[],
                               total_cards=0,
                               authors_count=0,
                               categories_stats={})
    finally:
        db_sess.close()


@templates_bp.route('/toggle_template_visibility/<int:template_id>')
@login_required
def toggle_template_visibility(template_id):
    db_sess = create_session()
    template = db_sess.query(Template).filter(
        Template.id == template_id,
        Template.user_id == current_user.id
    ).first()

    if template:
        template.is_private = not template.is_private
        db_sess.commit()
        status = "личным" if template.is_private else "публичным"
        flash(f'Шаблон "{template.name}" теперь является {status}', 'success')
    else:
        flash('Шаблон не найден', 'error')

    db_sess.close()
    return redirect(url_for('templates.my_templates'))


@templates_bp.route('/template/<int:template_id>/like', methods=['POST'])
@login_required
def like_template(template_id):
    db_sess = create_session()
    try:
        template = db_sess.query(Template).filter(Template.id == template_id).first()
        if template and not template.is_private:
            template.likes_count += 1
            db_sess.commit()
            return jsonify({'success': True, 'likes': template.likes_count})
        return jsonify({'success': False, 'error': 'Шаблон не найден'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        db_sess.close()


@templates_bp.route('/template/<int:template_id>/view', methods=['POST'])
def view_template(template_id):
    db_sess = create_session()
    try:
        template = db_sess.query(Template).filter(
            Template.id == template_id,
            Template.is_private == False
        ).first()
        if template:
            template.views_count += 1
            db_sess.commit()
            return jsonify({'success': True, 'views': template.views_count})
        return jsonify({'success': False})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        db_sess.close()