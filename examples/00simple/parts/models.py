import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

Session = scoped_session(sessionmaker())

Base = declarative_base()


class Pet(Base):
    __tablename__ = "Pet"

    id = sa.Column(sa.Integer, primary_key=True, doc="primary key")
    name = sa.Column(sa.String(255), default="", nullable=False)
    animal_type = sa.Column(sa.Enum("cat", "dog"))
    created = sa.Column(sa.DateTime, nullable=True)
    # tags
