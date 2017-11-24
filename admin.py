from databse import db_connect, cursor


class Admin:
    def __init__(self, ad_name, ad_id):
        self.ad_name = ad_name
        self.ad_id = ad_id

    def create(self):
        db_connect.execute("CREATE TABLE IF NOT EXISTS {}_{}("
                           "ID INTEGER AUTOINCREMENT PRIMARY KEY,"
                           "dte TEXT,"
                           "message_count INTEGER)".format(self.ad_name, self.ad_id))
        db_connect.commit()

    def insert(self, dte, msg_cnt):
        cursor.execute("INSERT INTO {}_{}(dte, message_count) VALUES(?,?)".format(self.ad_name, self.ad_id),
                       (dte, msg_cnt))
        db_connect.commit()

    def edit(self):
        # todo update
        pass
