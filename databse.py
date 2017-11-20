import sqlite3

db_connect = sqlite3.connect(database='bot_db.db', check_same_thread=False)
cursor = db_connect.cursor()


def create_db():
    try:
        db_connect.execute("CREATE TABLE IF NOT EXISTS Queue("
                           "ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,"
                           "from_ad INTEGER,"
                           "kind TEXT,"
                           "file_id TEXT,"
                           "caption TEXT,"
                           "gp INTEGER,"
                           "ch INTEGER,"
                           "edited INTEGER DEFAULT 0,"
                           "sent INTEGER DEFAULT 0,"
                           "ch_a INTEGER DEFAULT 0);")
        db_connect.execute("CREATE TABLE IF NOT EXISTS Activity("
                           "ID INTEGER PRIMARY KEY AUTOINCREMENT DEFAULT 0,"
                           "admin_name TEXT,"
                           "user_id INTEGER,"
                           "message_count INTEGER);")
        db_connect.execute("CREATE TABLE IF NOT EXISTS Mem_count("
                           "ID INTEGER PRIMARY KEY AUTOINCREMENT,"
                           "ddd TEXT,"
                           "balance INTEGER DEFAULT 0,"
                           "members INTEGER);")
        db_connect.commit()
    except Exception as E:
        print(E)


# 5005
def insert(kind, from_ad, file_id, caption, gp):
    try:
        cursor.execute("INSERT INTO Queue(kind, from_ad, file_id, caption, gp, ch_a) VALUES(?,?,?,?,?,?)",
                       (kind, from_ad, file_id, caption, gp, 0))
        db_connect.commit()
    except Exception as E:
        print(5005, E)


# 2002
def db_edit(caption, gp, edited, sent):
    try:
        cursor.execute("UPDATE Queue SET edited={0}, sent={1}, caption='{2}' WHERE gp = {3}"
                       .format(edited, sent, caption, gp))
        db_connect.commit()
    except Exception as E:
        print(2002, E)


# 3003
def db_set(ch, i_d):
    try:
        cursor.execute("UPDATE Queue SET ch={0},edited=0,sent=1,ch_a=1 WHERE ID = {1}".format(ch, i_d))
        db_connect.commit()
    except Exception as E:
        print(3003, E)
