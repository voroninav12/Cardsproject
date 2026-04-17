import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Template(SqlAlchemyBase):
    __tablename__ = 'templates'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    width = sqlalchemy.Column(sqlalchemy.Integer, default=63)
    height = sqlalchemy.Column(sqlalchemy.Integer, default=88)
    background_color = sqlalchemy.Column(sqlalchemy.String, default='#FFFFFF')

    # Оборотная сторона шаблона (единая для всех карточек)
    back_title = sqlalchemy.Column(sqlalchemy.String, default='Название игры')
    back_background_color = sqlalchemy.Column(sqlalchemy.String, default='#FFFFFF')
    back_image_filename = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    back_title_x = sqlalchemy.Column(sqlalchemy.Integer, default=10)
    back_title_y = sqlalchemy.Column(sqlalchemy.Integer, default=10)
    back_title_font_size = sqlalchemy.Column(sqlalchemy.Integer, default=16)
    back_image_x = sqlalchemy.Column(sqlalchemy.Integer, default=10)
    back_image_y = sqlalchemy.Column(sqlalchemy.Integer, default=40)
    back_image_width = sqlalchemy.Column(sqlalchemy.Integer, default=80)
    back_image_height = sqlalchemy.Column(sqlalchemy.Integer, default=80)

    is_private = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
    category = sqlalchemy.Column(sqlalchemy.String, default='other')
    tags = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    likes_count = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    views_count = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)

    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relationship('User', back_populates='templates')
    cards = orm.relationship("Card", back_populates='template')


class Card(SqlAlchemyBase):
    __tablename__ = 'cards'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    # Лицевая сторона
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    image_filename = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    # Позиционирование для лицевой стороны
    title_x = sqlalchemy.Column(sqlalchemy.Integer, default=10)
    title_y = sqlalchemy.Column(sqlalchemy.Integer, default=10)
    title_font_size = sqlalchemy.Column(sqlalchemy.Integer, default=16)
    description_x = sqlalchemy.Column(sqlalchemy.Integer, default=10)
    description_y = sqlalchemy.Column(sqlalchemy.Integer, default=40)
    description_font_size = sqlalchemy.Column(sqlalchemy.Integer, default=12)
    image_x = sqlalchemy.Column(sqlalchemy.Integer, default=10)
    image_y = sqlalchemy.Column(sqlalchemy.Integer, default=100)
    image_width = sqlalchemy.Column(sqlalchemy.Integer, default=80)
    image_height = sqlalchemy.Column(sqlalchemy.Integer, default=80)

    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)

    template_id = sqlalchemy.Column(sqlalchemy.Integer,
                                    sqlalchemy.ForeignKey("templates.id"))
    template = orm.relationship('Template', back_populates='cards')

    # ДОБАВЛЯЕМ ПОЛЕ user_id
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relationship('User', back_populates='cards')