import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import os

SqlAlchemyBase = orm.declarative_base()

__factory = None

def global_init(db_file):
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("Необходимо указать файл базы данных.")

    # Создаем папку если её нет
    db_dir = os.path.dirname(db_file)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'

    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)

def create_session() -> Session:
    global __factory
    return __factory()