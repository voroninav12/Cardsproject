from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, IntegerField, BooleanField, SelectField
from wtforms import SubmitField
from wtforms.validators import DataRequired, Optional


class TemplateForm(FlaskForm):
    name = StringField('Название шаблона', validators=[DataRequired()])
    description = TextAreaField('Описание шаблона', validators=[Optional()])
    width = IntegerField('Ширина (мм)', default=85)
    height = IntegerField('Высота (мм)', default=55)
    background_color = StringField('Цвет фона лицевой стороны', default='#FFFFFF')

    # Оборотная сторона шаблона
    back_title = StringField('Заголовок на обороте', validators=[DataRequired()])
    back_background_color = StringField('Цвет фона оборотной стороны', default='#FFFFFF')
    back_image_file = FileField('Изображение на обороте', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!')
    ])

    category = SelectField('Категория', choices=[
        ('game', 'Игровые карточки'),
        ('business', 'Бизнес'),
        ('creative', 'Креативные'),
        ('minimalist', 'Минимализм'),
        ('elegant', 'Элегантные'),
        ('modern', 'Современные'),
        ('vintage', 'Винтажные'),
        ('other', 'Другие')
    ], default='game')
    tags = StringField('Теги (через запятую)', validators=[Optional()])
    is_private = BooleanField('Личное', default=True)
    submit = SubmitField('Создать шаблон')


class CardForm(FlaskForm):
    # Только лицевая сторона
    title = StringField('Название карточки', validators=[DataRequired()])
    description = TextAreaField("Описание")
    image_file = FileField('Изображение (лицевая сторона)', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!')
    ])

    # Скрытые поля для позиционирования
    title_x = IntegerField(default=10)
    title_y = IntegerField(default=10)
    title_font_size = IntegerField(default=16)
    description_x = IntegerField(default=10)
    description_y = IntegerField(default=40)
    description_font_size = IntegerField(default=12)
    image_x = IntegerField(default=10)
    image_y = IntegerField(default=100)
    image_width = IntegerField(default=80)
    image_height = IntegerField(default=80)

    submit = SubmitField('Создать карточку')