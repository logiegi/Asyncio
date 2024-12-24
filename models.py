from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from db_conf import DSN
engine = create_async_engine(DSN)

Session = async_sessionmaker(bind=engine,
                             class_=AsyncSession,
                             expire_on_commit=False)

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from sqlalchemy import Column, Integer, String


# модель персонажей
class SwapiPeople(Base):
    __tablename__ = 'swapi_people'

    id = Column(Integer, primary_key=True, autoincrement=False)
    birth_year = Column(String(50))
    eye_color = Column(String(50))
    films = Column(String(500))       # Список
    gender = Column(String(50))
    hair_color = Column(String(50))
    height = Column(String(50))
    homeworld = Column(String(50))
    mass = Column(String(50))
    name = Column(String(50))
    skin_color = Column(String(50))
    species = Column(String(500))     # Список
    starships = Column(String(500))   # Список
    vehicles = Column((String(500)))    # Список