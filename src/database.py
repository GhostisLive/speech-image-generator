import pymysql

__tables = """
CREATE TABLE IF NOT EXISTS users (username VARCHAR(60) NOT NULL, password VARCHAR(255), email VARCHAR(255) NOT NULL, auth VARCHAR(6), valid BOOLEAN, PRIMARY KEY (email))
"""

def create_tables(conn: pymysql.Connection):
  with conn.cursor() as cursor:
    tables = __tables.strip("\n").split("\n")
    for table in tables:
      cursor.execute(table)
