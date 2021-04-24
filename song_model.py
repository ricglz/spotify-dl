from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

BaseModel = declarative_base()

class SongModel(BaseModel):
    __tablename__ = 'songs'
    song_id = Column(String, primary_key=True)
    song_link = Column(String, nullable=False)

    @classmethod
    def find_or_raise_by_id(cls, song_id: str, session: Session):
        query = session.query(cls).filter(cls.song_id == song_id)
        song = query.one_or_none()
        if song is None:
            raise KeyError('Record does not exist')
        return song
