from flask import Blueprint, render_template, redirect, flash, request, url_for, send_file, jsonify
from flask_login import login_required, current_user
from card_data.db_session import create_session
from card_data.cards import Card, Template
from forms.cards import CardForm
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
import io

cards_bp = Blueprint('cards', __name__)


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png', 'gif'}


def draw_card_front(c, card, template, x, y, width, height):
    """Рисует лицевую сторону карточки"""
    try:
        try:
            bg_color = HexColor(template.background_color if template.background_color else '#FFFFFF')
        except:
            bg_color = HexColor('#FFFFFF')

        c.setFillColor(bg_color)
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.setLineWidth(0.5)
        c.roundRect(x, y, width, height, 2 * mm, fill=1, stroke=1)

        c.saveState()

        if card.title:
            try:
                font_size = getattr(card, 'title_font_size', 14) or 14
                c.setFont("Helvetica-Bold", font_size)

                bg_rgb = bg_color.rgb()
                brightness = (bg_rgb[0] * 0.299 + bg_rgb[1] * 0.587 + bg_rgb[2] * 0.114)

                if brightness > 0.5:
                    text_color = HexColor('#000000')
                else:
                    text_color = HexColor('#FFFFFF')

                c.setFillColor(text_color)

                title = str(card.title)
                if len(title) > 30:
                    title = title[:27] + '...'

                text_width = c.stringWidth(title, "Helvetica-Bold", font_size)
                text_x = x + (width - text_width) / 2
                text_y = y + height - (font_size + 5)

                if text_x >= x and text_x + text_width <= x + width and text_y >= y:
                    c.drawString(text_x, text_y, title)
                else:
                    c.drawString(x + 5, y + height - 20, title[:20])

            except Exception as e:
                print(f"Ошибка отрисовки заголовка: {e}")

        if card.description:
            try:
                font_size = getattr(card, 'description_font_size', 10) or 10
                c.setFont("Helvetica", font_size)

                bg_rgb = bg_color.rgb()
                brightness = (bg_rgb[0] * 0.299 + bg_rgb[1] * 0.587 + bg_rgb[2] * 0.114)

                if brightness > 0.5:
                    text_color = HexColor('#333333')
                else:
                    text_color = HexColor('#E0E0E0')

                c.setFillColor(text_color)

                desc = str(card.description)
                max_width = width - 20

                def split_text(text, font, size, max_width):
                    words = text.split()
                    lines = []
                    current_line = []

                    for word in words:
                        test_line = ' '.join(current_line + [word]) if current_line else word
                        if c.stringWidth(test_line, font, size) <= max_width:
                            current_line.append(word)
                        else:
                            if current_line:
                                lines.append(' '.join(current_line))
                            current_line = [word] if c.stringWidth(word, font, size) <= max_width else []

                    if current_line:
                        lines.append(' '.join(current_line))

                    return lines

                lines = split_text(desc, "Helvetica", font_size, max_width)
                line_height = font_size * 1.2
                start_y = y + height - (font_size * 2 + 20)

                for i, line in enumerate(lines[:4]):
                    if start_y - (i * line_height) < y + 10:
                        break

                    line_width = c.stringWidth(line, "Helvetica", font_size)
                    line_x = x + (width - line_width) / 2
                    line_y = start_y - (i * line_height)

                    c.drawString(line_x, line_y, line)

            except Exception as e:
                print(f"Ошибка отрисовки описания: {e}")

        if getattr(card, 'image_filename', None):
            try:
                image_path = os.path.join('static/uploads', card.image_filename)
                if os.path.exists(image_path):
                    img = ImageReader(image_path)

                    max_img_size = min(width, height) * 0.5
                    img_width = min(getattr(card, 'image_width', 60) or 60, max_img_size)
                    img_height = min(getattr(card, 'image_height', 60) or 60, max_img_size)

                    img_x = x + (width - img_width) / 2
                    img_y = y + 15

                    if img_y >= y and img_y + img_height <= y + height:
                        c.setFillColor(bg_color)
                        c.setStrokeColorRGB(0.6, 0.6, 0.6)
                        c.setLineWidth(0.5)
                        c.rect(img_x - 2, img_y - 2, img_width + 4, img_height + 4, fill=1, stroke=1)

                        c.drawImage(img, img_x, img_y,
                                    width=img_width, height=img_height,
                                    preserveAspectRatio=True, mask='auto')

            except Exception as e:
                print(f"Ошибка отрисовки изображения: {e}")

        c.restoreState()

    except Exception as e:
        print(f"Общая ошибка в draw_card_front: {e}")
        c.setFillColor(HexColor('#FFCCCC'))
        c.rect(x, y, width, height, fill=1)


def draw_card_back(c, template, x, y, width, height):
    """Рисует оборотную сторону карточки"""
    try:
        try:
            bg_color = HexColor(template.back_background_color if template.back_background_color else '#2C3E50')
        except:
            bg_color = HexColor('#2C3E50')

        c.setFillColor(bg_color)
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.setLineWidth(0.5)
        c.roundRect(x, y, width, height, 2 * mm, fill=1, stroke=1)

        c.saveState()

        if template.back_title:
            try:
                font_size = getattr(template, 'back_title_font_size', 18) or 18
                c.setFont("Helvetica-Bold", font_size)

                bg_rgb = bg_color.rgb()
                brightness = (bg_rgb[0] * 0.299 + bg_rgb[1] * 0.587 + bg_rgb[2] * 0.114)

                if brightness > 0.5:
                    text_color = HexColor('#000000')
                else:
                    text_color = HexColor('#FFFFFF')

                c.setFillColor(text_color)

                title = str(template.back_title)
                if len(title) > 20:
                    title = title[:17] + '...'

                text_width = c.stringWidth(title, "Helvetica-Bold", font_size)
                text_x = x + (width - text_width) / 2
                text_y = y + height - (font_size + 15)

                if text_x >= x and text_x + text_width <= x + width and text_y >= y:
                    c.drawString(text_x, text_y, title)

            except Exception as e:
                print(f"Ошибка отрисовки заголовка оборота: {e}")

        if template.back_image_filename:
            try:
                image_path = os.path.join('static/uploads', template.back_image_filename)
                if os.path.exists(image_path):
                    img = ImageReader(image_path)

                    max_img_size = min(width, height) * 0.6
                    img_width = min(getattr(template, 'back_image_width', 50) or 50, max_img_size)
                    img_height = min(getattr(template, 'back_image_height', 50) or 50, max_img_size)

                    img_x = x + (width - img_width) / 2
                    img_y = y + (height - img_height) / 2 - 10

                    if img_y >= y and img_y + img_height <= y + height:
                        c.drawImage(img, img_x, img_y,
                                    width=img_width, height=img_height,
                                    preserveAspectRatio=True, mask='auto')

            except Exception as e:
                print(f"Ошибка отрисовки изображения оборота: {e}")

        c.restoreState()

    except Exception as e:
        print(f"Общая ошибка в draw_card_back: {e}")
        c.setFillColor(HexColor('#CCCCFF'))
        c.rect(x, y, width, height, fill=1)


def draw_crop_marks(c, left, bottom, right, top):
    """Рисует метки обрезки"""
    c.setLineWidth(0.25)
    c.setStrokeColorRGB(0, 0, 0)

    mark_length = 3 * mm

    c.line(left, top, left, top - mark_length)
    c.line(left, top, left + mark_length, top)

    c.line(right, top, right, top - mark_length)
    c.line(right, top, right - mark_length, top)

    c.line(left, bottom, left, bottom + mark_length)
    c.line(left, bottom, left + mark_length, bottom)

    c.line(right, bottom, right, bottom + mark_length)
    c.line(right, bottom, right - mark_length, bottom)


@cards_bp.route('/create_card', methods=['GET', 'POST'])
@login_required
def create_card():
    form = CardForm()
    selected_template_id = request.args.get('template_id')

    db_sess = create_session()
    templates = []

    try:
        # Получаем шаблоны
        templates_query = db_sess.query(Template).filter(
            (Template.user_id == current_user.id) | (Template.is_private == False)
        ).all()

        # Преобразуем в список словарей, чтобы избежать проблем с сессией
        for t in templates_query:
            templates.append({
                'id': t.id,
                'name': t.name,
                'width': t.width,
                'height': t.height,
                'user_id': t.user_id,
                'is_private': t.is_private
            })

        if form.validate_on_submit():
            template_id = int(request.form.get('template_id'))

            # Находим шаблон в списке
            template_data = None
            for t in templates:
                if t['id'] == template_id:
                    template_data = t
                    break

            if not template_data:
                flash('Шаблон не найден', 'error')
                return render_template('create_card.html',
                                       title='Создание карточки',
                                       form=form,
                                       templates=templates,
                                       selected_template_id=selected_template_id)

            if template_data['user_id'] != current_user.id and template_data['is_private']:
                flash('У вас нет доступа к этому шаблону', 'error')
                return render_template('create_card.html',
                                       title='Создание карточки',
                                       form=form,
                                       templates=templates,
                                       selected_template_id=selected_template_id)

            # Создаём карточку
            card = Card(
                title=form.title.data,
                description=form.description.data,
                template_id=template_id,
                user_id=current_user.id,  # Теперь это поле есть в модели
                title_x=int(request.form.get('title_x', 20)),
                title_y=int(request.form.get('title_y', 20)),
                title_font_size=int(request.form.get('title_font_size', 20)),
                description_x=int(request.form.get('description_x', 20)),
                description_y=int(request.form.get('description_y', 60)),
                description_font_size=int(request.form.get('description_font_size', 14)),
                image_x=int(request.form.get('image_x', 20)),
                image_y=int(request.form.get('image_y', 120)),
                image_width=int(request.form.get('image_width', 100)),
                image_height=int(request.form.get('image_height', 100))
            )

            if form.image_file.data and allowed_file(form.image_file.data.filename):
                filename = secure_filename(form.image_file.data.filename)
                unique_filename = f"{current_user.id}_{template_id}_{int(datetime.now().timestamp())}_{filename}"
                filepath = os.path.join('static/uploads', unique_filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                form.image_file.data.save(filepath)
                card.image_filename = unique_filename

            db_sess.add(card)
            db_sess.commit()
            flash('Карточка успешно создана!', 'success')
            db_sess.close()
            return redirect(url_for('cards.my_cards'))

        return render_template('create_card.html',
                               title='Создание карточки',
                               form=form,
                               templates=templates,
                               selected_template_id=selected_template_id)

    except Exception as e:
        print(f"Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Ошибка: {str(e)}', 'error')
        return render_template('create_card.html',
                               title='Создание карточки',
                               form=form,
                               templates=[],
                               selected_template_id=selected_template_id)
    finally:
        db_sess.close()


@cards_bp.route('/my_cards')
@login_required
def my_cards():
    db_sess = create_session()
    try:
        # Получаем карточки текущего пользователя
        cards = db_sess.query(Card).filter(
            Card.user_id == current_user.id
        ).all()

        # Загружаем шаблоны для каждой карточки
        for card in cards:
            if card.template_id:
                template = db_sess.query(Template).filter(
                    Template.id == card.template_id
                ).first()
                card.template = template

        # Получаем уникальные шаблоны для фильтрации
        template_ids = set()
        for card in cards:
            if card.template:
                template_ids.add(card.template.id)

        templates = []
        for template_id in template_ids:
            template = db_sess.query(Template).filter(
                Template.id == template_id
            ).first()
            if template:
                templates.append(template)

        return render_template('my_cards.html',
                               title='Мои карточки',
                               cards=cards,
                               templates=templates)
    except Exception as e:
        print(f"Ошибка при загрузке карточек: {str(e)}")
        flash(f'Ошибка при загрузке карточек: {str(e)}', 'error')
        return render_template('my_cards.html',
                               title='Мои карточки',
                               cards=[],
                               templates=[])
    finally:
        db_sess.close()


@cards_bp.route('/print/<int:template_id>')
@login_required
def print_cards(template_id):
    db_sess = create_session()
    try:
        template = db_sess.query(Template).filter(
            Template.id == template_id
        ).first()

        if not template:
            flash('Шаблон не найден', 'error')
            return redirect(url_for('cards.my_cards'))

        if template.is_private and template.user_id != current_user.id:
            flash('Нет доступа к этому шаблону', 'error')
            return redirect(url_for('cards.my_cards'))

        cards = db_sess.query(Card).filter(
            Card.template_id == template_id,
            Card.user_id == current_user.id
        ).all()

        cards_data = []
        for card in cards:
            cards_data.append({
                'id': card.id,
                'title': card.title[:30] + '...' if card.title and len(card.title) > 30 else (
                        card.title or 'Без названия'),
                'description': card.description[:100] + '...' if card.description and len(card.description) > 100 else (
                        card.description or 'Без описания'),
                'image_filename': card.image_filename
            })

        template_data = {
            'id': template.id,
            'name': template.name or 'Без названия',
            'width': template.width if template.width is not None else 85,
            'height': template.height if template.height is not None else 55,
            'background_color': template.background_color or '#FFFFFF',
            'back_title': template.back_title or 'Карточка',
            'back_background_color': template.back_background_color or '#2C3E50',
            'back_image_filename': template.back_image_filename
        }

        return render_template('static_print.html',
                               title='Печать карточек',
                               template=template_data,
                               cards=cards_data)

    except Exception as e:
        print(f"ERROR в print_cards: {str(e)}")
        flash(f'Ошибка при загрузке карточек: {str(e)}', 'error')
        return redirect(url_for('cards.my_cards'))
    finally:
        db_sess.close()


@cards_bp.route('/export_pdf/<int:template_id>')
@login_required
def export_pdf(template_id):
    db_sess = create_session()
    try:
        template = db_sess.query(Template).filter(
            Template.id == template_id
        ).first()

        if not template:
            flash('Шаблон не найден', 'error')
            return redirect(url_for('cards.my_cards'))

        if template.is_private and template.user_id != current_user.id:
            flash('Нет доступа к этому шаблону', 'error')
            return redirect(url_for('cards.my_cards'))

        cards = db_sess.query(Card).filter(
            Card.template_id == template_id,
            Card.user_id == current_user.id
        ).all()

        if not cards:
            flash('Нет карточек для печати', 'error')
            return redirect(url_for('cards.print_cards', template_id=template_id))

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        card_width_mm = template.width if template.width is not None else 85
        card_height_mm = template.height if template.height is not None else 55

        card_width = card_width_mm * 2.83465
        card_height = card_height_mm * 2.83465

        cards_per_row = 2
        cards_per_column = 2

        horizontal_spacing = 15 * mm
        vertical_spacing = 20 * mm

        total_block_width = (card_width * cards_per_row) + (horizontal_spacing * (cards_per_row - 1))
        total_block_height = (card_height * cards_per_column) + (vertical_spacing * (cards_per_column - 1))

        margin_x = (width - total_block_width) / 2
        margin_y = (height - total_block_height) / 2

        cards_per_page = cards_per_row * cards_per_column

        positions = []
        for row in range(cards_per_column):
            for col in range(cards_per_row):
                x = margin_x + (col * (card_width + horizontal_spacing))
                y = margin_y + ((cards_per_column - 1 - row) * (card_height + vertical_spacing))
                positions.append((x, y))

        total_pages = (len(cards) + cards_per_page - 1) // cards_per_page

        for page_num in range(total_pages):
            start_idx = page_num * cards_per_page
            page_cards = cards[start_idx:start_idx + cards_per_page]

            for i, card in enumerate(page_cards):
                if i >= len(positions):
                    break
                x, y = positions[i]
                draw_card_front(c, card, template, x, y, card_width, card_height)

            for i, card in enumerate(page_cards):
                if i >= len(positions):
                    break
                x, y = positions[i]
                draw_crop_marks(c, x, y, x + card_width, y + card_height)

            c.setFont("Helvetica", 10)
            c.setFillColorRGB(0.3, 0.3, 0.3)
            page_info = f"Страница {page_num * 2 + 1} из {total_pages * 2} - Лицевая сторона"
            c.drawCentredString(width / 2, 15, page_info)

            c.showPage()

            for i, card in enumerate(page_cards):
                if i >= len(positions):
                    break
                x, y = positions[i]
                draw_card_back(c, template, x, y, card_width, card_height)

            for i, card in enumerate(page_cards):
                if i >= len(positions):
                    break
                x, y = positions[i]
                draw_crop_marks(c, x, y, x + card_width, y + card_height)

            c.setFont("Helvetica", 10)
            c.setFillColorRGB(0.3, 0.3, 0.3)
            page_info = f"Страница {page_num * 2 + 2} из {total_pages * 2} - Оборотная сторона"
            c.drawCentredString(width / 2, 15, page_info)

            if page_num < total_pages - 1:
                c.showPage()

        c.save()
        buffer.seek(0)
        filename = f'карточки_{template.name.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'

        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"Ошибка создания PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Ошибка при создании PDF: {str(e)}', 'error')
        return redirect(url_for('cards.print_cards', template_id=template_id))
    finally:
        db_sess.close()


@cards_bp.route('/api/print_settings', methods=['POST'])
@login_required
def save_print_settings():
    try:
        data = request.get_json()
        settings = {
            'crop_marks': data.get('cropMarks', True),
            'bleed_area': data.get('bleedArea', True),
            'quality': data.get('quality', 'high'),
            'paper_size': data.get('paperSize', 'A4'),
            'margins': data.get('margins', 10)
        }

        return jsonify({'success': True, 'settings': settings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@cards_bp.route('/test_pdf/<int:template_id>')
@login_required
def test_pdf(template_id):
    try:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)

        c.setFont("Helvetica-Bold", 20)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(100, 700, "Тест шрифтов и кириллицы")

        c.setFont("Helvetica", 14)
        c.drawString(100, 670, "Заголовок: Профессиональная визитка")

        c.setFont("Helvetica", 12)
        c.drawString(100, 650, "Описание: Качественные услуги с индивидуальным подходом")

        c.setFillColorRGB(1, 0, 0)
        c.drawString(100, 630, "Красный текст")

        c.setFillColorRGB(0, 0, 1)
        c.drawString(100, 610, "Синий текст")

        c.setFillColorRGB(0, 0, 0)
        c.drawString(100, 590, f"Шаблон ID: {template_id}")
        c.drawString(100, 570, f"Время: {datetime.now().strftime('%H:%M:%S')}")

        c.save()
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'тест_шрифтов_{template_id}.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        return f"Ошибка: {str(e)}", 500