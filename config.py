import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')

PASTA_BACKUPS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')

IMAGENS_DE_BANCO_DE_DADOS = ['postgres','mysql', 'mariadb']