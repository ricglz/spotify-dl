from contextlib import contextmanager
from typing import Generator

from sqlalchemy import orm
from sqlalchemy.engine import create_engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from song_model import BaseModel, SongModel

@contextmanager
def create_scoped_session(
    scoped_session: orm.scoped_session,
    ignore_integrity_error: bool = False,
) -> Generator[Session, None, None]:
    session = scoped_session()
    try:
        yield session
        session.commit()
    except IntegrityError as e:
        session.rollback()
        if ignore_integrity_error:
            print(
                "Ignoring {}. This happens due to a timing issue among threads/processes/nodes. "
                "Another one might have committed a record with the same key(s).".format(repr(e))
            )
        else:
            raise
    except SQLAlchemyError as e:
        session.rollback()
        message = (
            "An exception is raised during the commit. "
            "This typically happens due to invalid data in the commit, "
            "e.g. exceeding max length. "
        )
        raise ValueError(message) from e
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class Storage():
    def __init__(self, url: str):
        self.url = self._fill_storage_url_template(url)
        try:
            self.engine = create_engine(self.url)
        except ImportError as e:
            raise ImportError(
                "Failed to import DB access module for the specified storage URL. "
                "Please install appropriate one."
            ) from e
        self.scoped_session = orm.scoped_session(orm.sessionmaker(bind=self.engine))
        BaseModel.metadata.create_all(self.engine)

    @staticmethod
    def _fill_storage_url_template(template: str) -> str:
        return template.format(SCHEMA_VERSION='123456789')

    def get_link(self, song_id: str):
        with create_scoped_session(self.scoped_session) as session:
            return SongModel.find_or_raise_by_id(song_id, session).song_link

    def store_link(self, song_id: str, song_link: str):
        with create_scoped_session(self.scoped_session) as session:
            song = SongModel(song_id=song_id, song_link=song_link)
            session.add(song)
