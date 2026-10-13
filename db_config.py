import os

import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': os.getenv('DB_PASSWORD', ''),
    'database': 'parc_informatique',
    'charset': 'utf8mb4',
    'cursorclass': DictCursor
}


def get_connection():
    return pymysql.connect(**DB_CONFIG)
