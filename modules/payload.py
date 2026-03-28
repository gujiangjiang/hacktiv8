import sqlite3
import tempfile
import os

def build_db_from_sql(sql_path, backend_url, target_path):
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql = f.read()

    sql = sql.replace('BACKEND_URL', backend_url).replace('TARGET_PATH', target_path)

    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()

    try:
        con = sqlite3.connect(tmp.name)
        con.executescript(sql)
        con.commit()
        con.close()

        with open(tmp.name, 'rb') as f:
            return f.read()
    finally:
        os.unlink(tmp.name)