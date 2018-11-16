from sqlalchemy import create_engine, Column, String, Integer, Date, DateTime, Boolean, Text, Float
from khayyam3.tehran_timezone import timedelta, JalaliDatetime as JDateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
import numpy as np
import logging

logging.basicConfig(filename='report.log', level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s')
Base = declarative_base()


class Channel(Base):
    def __init__(self, name, admin, group_id, plan,
                 interval='20mr', bed='off', wake='off', up=True, logo=False, pos=7,
                 register=JDateTime().now().to_datetime(), expire=timedelta):
        # required
        self.name = name
        self.admin = admin
        self.group_id = group_id
        self.plan = plan

        # optional
        self.interval = interval
        self.bed = bed
        self.wake = wake
        self.up = up
        self.logo = logo
        self.pos = pos
        self.register = register
        self.expire = register + expire

    def __str__(self):
        return "ch_name: {}, ch_admin: {}, group_id: {}, plan {}".format(
            self.name, self.admin, self.group_id, self.plan)

    __tablename__ = "channel"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(Integer, default=0)
    name = Column(String)
    admin = Column(Integer)
    group_id = Column(Integer, unique=True)
    plan = Column(Integer, default=0)
    interval = Column(String)
    bed = Column(Integer)
    wake = Column(Integer)
    up = Column(Boolean)
    logo = Column(Boolean)
    pos = Column(Integer)
    register = Column(DateTime)
    expire = Column(DateTime)


class Member(Base):
    def __init__(self, number, channel_name, calendar):
        self.number = number
        self.channel_name = channel_name
        self.calendar = calendar

    __tablename__ = "member"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    number = Column("number", Integer)
    channel_name = Column("channel_id", String)
    calendar = Column("calendar", Date)


class Message(Base):
    def __init__(self, from_group, to_channel, kind, msg_gp_id,
                 txt='', file_id='', msg_ch_id=0, sent=False, ch_a=False, size=None, mime="", other=""):
        # required
        self.from_group = from_group
        self.to_channel = to_channel
        self.kind = kind
        self.msg_gp_id = msg_gp_id

        # optional
        self.txt = txt
        self.file_id = file_id
        self.msg_ch_id = msg_ch_id
        self.sent = sent
        self.ch_a = ch_a
        self.size = size
        self.mime = mime
        self.other = other

    def __str__(self):
        return "from_group: {}, to_channel: {}, kind: {}".format(self.from_group, self.to_channel, self.kind)

    __tablename__ = "message"

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_group = Column(Integer)
    to_channel = Column(String)
    kind = Column(String(length=15))
    file_id = Column(Text, default="")
    txt = Column(String)
    msg_gp_id = Column(Integer)
    msg_ch_id = Column(Integer, default=0)
    sent = Column(Boolean, default=False)
    ch_a = Column(Boolean, default=False)
    size = Column(Float, default=0)
    mime = Column(String, default="")
    other = Column(String, default="")


# region create
engine = create_engine('sqlite:///bot_db.db', connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
session = Session(bind=engine)
# endregion


def add(obj):
    if isinstance(obj, (Message, Member)):
        session.add(obj)
        session.commit()

    elif isinstance(obj, Channel):
        search = session.query(Channel).filter(Channel.group_id == obj.group_id).first()

        if not search:
            session.add(obj)
            session.commit()
        else:
            logging.error("add : channel {} exist".format(search.name))
    else:
        raise Warning('WTF! "{}"'.format(obj.__class__))


def delete(obj):
    if isinstance(obj, Channel):
        channel = session.query(Channel).filter(Channel.admin == obj.admin, Channel.name == obj.name)
        if channel:
            channel.delete()


def find(table, **col):
    if table == "message":
        message = None
        if col.get("msg_gp_id") and col.get("gp_id"):
            message = session.query(Message).filter(Message.msg_gp_id == col["msg_gp_id"],
                                                    Message.from_group == col["gp_id"]).first()
        elif col.get("media"):
            message = session.query(Message).filter(Message.other == col["media"]).all()

        return message

    elif table == "channel":
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
            if len(channel) == 1:
                channel = channel[0]

        elif col.get('name'):
            channel = session.query(Channel).filter(Channel.name == col['name']).first()

        return channel

    elif table == "member":
        if col.get('admin') and col.get('name'):
            q = session.query(Channel).filter(Channel.name == col['name'],
                                              Channel.admin == col['admin']).first()
            if q:
                member = session.query(Member.number,
                                       Member.calendar).filter(Member.channel_name == col['name'],
                                                               Member.calendar.between(col['from_'], col['til'])).all()
                member = np.array(member).reshape((-1, 2))
                return member


def update(obj):
    if isinstance(obj, Message):
        row = session.query(Message).get(obj.id)

        row.txt = obj.txt
        row.msg_ch_id = obj.msg_ch_id
        row.sent = obj.sent
        row.ch_a = obj.ch_a

        if obj.kind == 'photo':
            row.file_id = obj.file_id
        elif obj.kind == 'vid':
            row.file_id = obj.file_id

        session.commit()

    elif isinstance(obj, Channel):
        row = session.query(Channel).filter(Channel.name == obj.name).first()

        row.interval = obj.interval
        row.bed = obj.bed
        row.wake = obj.wake
        row.up = obj.up
        row.name = obj.name
        row.logo = obj.logo
        row.pos = obj.pos
        row.expire = obj.expire
        session.commit()


def remain(channel) -> int:
    rem = session.query(Message).filter(Message.to_channel == channel.name,
                                        Message.sent == False,
                                        ~Message.txt.startswith('.'),
                                        ~Message.txt.startswith('/')).all()
    rem = rem if rem else []

    return len(rem)


def get_last_msg(channel_name):
    res = session.query(Message).filter(Message.sent == False,
                                        ~Message.txt.startswith('.'),
                                        ~Message.txt.startswith('/'),
                                        Message.to_channel == channel_name).first()
    if res:
        if res.other.isnumeric():
            media = res.other
            res = session.query(Message).filter(Message.sent == False,
                                                ~Message.txt.startswith('.'),
                                                ~Message.txt.startswith('/'),
                                                Message.to_channel == channel_name,
                                                Message.other == media).all()
    return res

# add(Channel(name='@ttiimmeerrr', admin=103086461, group_id=-1001141277396, expire=timedelta(days=7), plan=3))
# add(Channel(name='@min1ch', admin=103086461, group_id=-1001174976706, interval='1m'))
# add(Channel(name='@min5ch', admin=103086461, group_id=-1001497526440, interval='5m'))
# add(Member(number=2, channel_name="@ttiimmeerrr", calendar=JDateTime().now().to_date()))
