from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String)

class Notebook(Base):
    __tablename__ = 'notebooks'
    id = Column(Integer, primary_key=True)
    usuario = Column(String)
    matricula = Column(String)
    departamento = Column(String)
    modelo = Column(String)
    numero_serie = Column(String)
    etiqueta_ativo = Column(String)
    processador = Column(String)
    ram = Column(String)
    armazenamento = Column(String)
    ip = Column(String)
    mac = Column(String)
    so = Column(String)
    localizacao = Column(String)
    status = Column(String)

class SimCard(Base):
    __tablename__ = 'sim_cards'
    id = Column(Integer, primary_key=True)
    iccid = Column(String)
    pin = Column(String)
    puk1 = Column(String)
    puk2 = Column(String)
    operadora = Column(String)
    status = Column(String)

class Mobile(Base):
    __tablename__ = 'mobiles'
    id = Column(Integer, primary_key=True)
    usuario = Column(String)
    matricula = Column(String)
    departamento = Column(String)
    modelo = Column(String)
    numero_serie = Column(String)
    imei1 = Column(String)
    imei2 = Column(String)
    msisdn = Column(String)
    chip_em_uso = Column(String)
    conta_google = Column(String)
    id_frota = Column(String)
    id_pulsus_mobi = Column(String)
    status = Column(String)

class Log(Base):
    __tablename__ = 'log'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    usuario = Column(String)
    acao = Column(String)
    detalhes = Column(String)

engine = create_engine('sqlite:///devices.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Ensure admin user exists
session = Session()
if not session.query(User).filter_by(username="admin").first():
    admin = User(username="admin", password="admin", role="admin")
    session.add(admin)
    session.commit()
session.close()
