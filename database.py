from sqlalchemy import create_engine, Column, String, Integer, Date, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from khayyam3.tehran_timezone import JalaliDatetime, timedelta
from sqlalchemy.orm import Session
import logging


logging.basicConfig(filename='report.log', level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s')
Base = declarative_base()


class Channel(Base):
    def __init__(self, name, admin, group_id,
                 interval='11mr', bed='off', wake='off', register=JalaliDatetime().now().to_datetime(), expire=1):
        self.name = name
        self.admin = admin
        self.group_id = group_id
        self.interval = interval

        self.bed = bed
        self.wake = wake
        self.register = register
        self.expire = register + timedelta(days=31*expire)

    __tablename__ = "channel"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    channel_id = Column("channel_id", Integer, default=0)
    name = Column("name", String)
    admin = Column("admin", Integer)
    group_id = Column("group_id", Integer, unique=True)
    interval = Column("interval", String)
    bed = Column("bed", Integer)
    wake = Column("wake", Integer)
    register = Column("register", DateTime)
    expire = Column("expire", DateTime)


class Member(Base):
    def __init__(self, number, channel_id, calendar):
        self.number = number
        self.channel_id = channel_id
        self.calendar = calendar

    __tablename__ = "member"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    number = Column("number", Integer)
    channel_id = Column("channel_id", Integer)
    calendar = Column("calendar", Date)


class Message(Base):
    def __init__(self, from_gp, to_ch, kind, msg_gp_id,
                 txt='', file_id='', msg_ch_id=0, sent=False, ch_a=False, other=''):
        self.from_gp = from_gp
        self.to_ch = to_ch
        self.kind = kind
        self.msg_gp_id = msg_gp_id

        # optional
        self.txt = txt
        self.file_id = file_id
        self.msg_ch_id = msg_ch_id
        self.sent = sent
        self.ch_a = ch_a
        self.other = other

    __tablename__ = "message"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    from_gp = Column("from_gp", Integer)
    to_ch = Column("to_ch", String)
    kind = Column("kind", String(length=15))
    file_id = Column("file_id", Text, default='')
    txt = Column("txt", String)
    msg_gp_id = Column("msg_gp_id", Integer)
    msg_ch_id = Column("msg_ch_id", Integer, default=0)
    sent = Column("sent", Boolean, default=False)
    ch_a = Column("ch_a", Boolean, default=False)
    other = Column("other", String, default='')


# region create
engine = create_engine('sqlite:///bot_db.db', connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
session = Session(bind=engine)
conn = engine.connect()


# endregion


def add(obj):
    if obj.__class__ == Message:
        session.add(obj)
        session.commit()
        session.close()

    elif obj.__class__ == Member:
        session.add(obj)
        session.commit()
        session.close()

    elif obj.__class__ == Channel:
        search = session.query(Channel).filter(Channel.group_id == obj.group_id).first()

        if not search:
            session.add(obj)
            session.commit()
            session.close()
        else:
            logging.error("add : channel {} exist".format(search.name))
    else:
        raise Warning('WTF! "{}"'.format(obj.__class__))


def find(table, **col):
    if table == 'message':
        message = session.query(Message).filter(Message.msg_gp_id == col['msg_gp_id'],
                                                Message.from_gp == col['gp_id']).first()
        return message
    elif table == 'channel':
        channel = None

        if not col:
            return session.query(Channel).all()

        if col.get('group_id'):
            channel = session.query(Channel).filter(Channel.group_id == col['group_id']).first()
        elif col.get('admin') and col.get('name'):
            channel = session.query(Channel).filter(Channel.admin == col['admin'],
                                                    Channel.name == col['name']).first()
        elif col.get('admin'):
            channel = session.query(Channel).filter(Channel.admin == col['admin']).all()

        elif col.get('name'):
            channel = session.query(Channel).filter(Channel.name == col['name']).first()

        return channel


def update(obj):
    if obj.__class__ == Message:
        row: Message = session.query(Message).get(obj.id)

        row.txt = obj.txt
        row.msg_ch_id = obj.msg_ch_id
        row.sent = obj.sent
        row.ch_a = obj.ch_a

        if obj.kind == 'photo':
            row.file_id = obj.file_id
        elif obj.kind == 'vid':
            row.file_id = obj.file_id

        session.commit()
        session.close()

    elif obj.__class__ == Channel:
        row = session.query(Channel).filter(Channel.channel_id == obj.channel_id).first()

        row.interval = obj.interval
        row.bed = obj.bed
        row.wake = obj.wake
        row.channel_name = obj.name

        session.commit()


def remain(channel_name: str) -> int:
    rem = session.query(Message).filter(Message.to_ch == channel_name,
                                        Message.sent == False,
                                        ~Message.txt.startswith('.'),
                                        ~Message.txt.startswith('/')).all()
    rem = rem if rem else []

    return len(rem)


def get_last_msg(channel_name: str):
    res = session.query(Message).filter(Message.sent == False,
                                        ~Message.txt.startswith('.'),
                                        ~Message.txt.startswith('/'),
                                        Message.to_ch == channel_name).first()
    return res


add(Channel(name='@ttiimmeerrr', admin=103086461, group_id=-1001141277396, expire=1))
# add(Channel(name='@min1ch', admin=103086461, group_id=-1001174976706, interval='1m'))
# add(Channel(name='@min5ch', admin=103086461, group_id=-1001497526440, interval='5m'))
