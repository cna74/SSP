from telegram.ext import Updater, MessageHandler, Filters
import matplotlib.pyplot as plt
from PIL import Image
import telegram
import datetime
import sqlite3
import pytz
import time
import re

# '354237673:AAEqjI0X33Ji3SnaO3y8bT_guZvhhvMyVGQ' ========= >> crazy
# '410818874:AAEU8gHdOmurgJBf_N_p-58qVW94Rc_vgOc' =========  >> ttiimmeerr
TOKEN = '410818874:AAEU8gHdOmurgJBf_N_p-58qVW94Rc_vgOc'
# region vars
updater = Updater(TOKEN)
robot = telegram.Bot(TOKEN)
db_connect = sqlite3.connect(database='bot_db.db', check_same_thread=False)
cursor = db_connect.cursor()
day = tuple(range(0, 6000, 1200))
kind, text, edited, sent, ch_a = 1, 3, 6, 7, 8
channel = '@crazymind3'
# endregion


def current_time():
    utc = pytz.utc
    u = time.gmtime()
    utc_dt = datetime.datetime(u[0], u[1], u[2], u[3], u[4], u[5], tzinfo=utc)
    eastern = pytz.timezone('Asia/Tehran')
    loc_dt = utc_dt.astimezone(eastern)
    date = '%Y-%m-%d'
    hour = '%H%M%S'
    week_day = '%a'
    return loc_dt.strftime(date), loc_dt.strftime(hour), loc_dt.strftime(week_day)


def id_remove(entry):
    pattern = re.compile(r'(@\S+)', re.I)
    if re.search(pattern, entry):
        state = re.findall(pattern, entry)
        for state in state:
            if not state.lower() in ('@crazymind3', '@crazy_miind3', '@mmd_bt'):
                entry = re.sub(state, '', entry)
        return entry
    else:
        return entry + '\n@CrazyMind3'


# 4004
def put(photo, caption):
    try:
        robot.getFile(photo).download('tmp.jpg')
        pattern = re.compile(r':(\S{1,2}):', re.I)
        coor_pt = re.compile(r'(nw|ne|nc|cw|cc|ce|sw|sc|se|e|n|w|s)', re.I)
        if re.search(pattern, caption):
            i_cor = ''.join(re.findall(pattern, caption)[0]).lower()
            coor = re.findall(coor_pt, i_cor)[0] if re.findall(coor_pt, i_cor)[0] else 'sw'
        else:
            coor = 'sw'
        lg = Image.open('CC.png')
        bg = Image.open('tmp.jpg')
        res, lg_sz = bg.size, lg.size
        deaf_l, deaf_p, box_deaf = (3800, 1000), (1000, 3800), (3200, 3200)

        if res[0] > res[1]:
            if not res[0] == deaf_l[0] and not res[1] == deaf_l[1]:
                n_deaf = [int((lg_sz[0] * res[0]) / deaf_l[0]), int((lg_sz[1] * res[1]) / deaf_l[1])]
                lg.thumbnail(n_deaf)

        elif res[0] == res[1]:
            if not res == box_deaf:
                n_deaf = [int((lg_sz[0] * res[0]) / box_deaf[0]), int((lg_sz[1] * res[1]) / box_deaf[1])]
                lg.thumbnail(n_deaf)

        else:
            if not res[0] == deaf_p[0] and not res[1] == deaf_p[1]:
                n_deaf = [int((lg_sz[0] * res[0]) / deaf_p[0]), int((lg_sz[1] * res[1]) / deaf_p[1])]
                lg.thumbnail(n_deaf)
        lg_sz = lg.size
        dict1 = {'nw': (0, 0),
                 'n': (int((res[0] / 2) - (lg_sz[0] / 2)), 0),
                 'nc': (int(res[0] / 2 - lg_sz[0] / 2), 0),
                 'ne': (res[0] - lg_sz[0], 0),
                 'w': (0, (int(res[1] / 2 - lg_sz[1] / 2))),
                 'cw': (0, (int(res[1] / 2 - lg_sz[1] / 2))),
                 'cc': (int(res[0] / 2 - lg_sz[0] / 2), int(res[1] / 2)),
                 'e': (res[0] - lg_sz[0], int(res[1] / 2) - int(lg_sz[1] / 2)),
                 'ce': (res[0] - lg_sz[0], int(res[1] / 2) - int(lg_sz[1] / 2)),
                 'sw': (0, res[1] - lg_sz[1]),
                 's': (int(res[0] / 2) - int(lg_sz[0] / 2), res[1] - lg_sz[1]),
                 'sc': (int(res[0] / 2) - int(lg_sz[0] / 2), res[1] - lg_sz[1]),
                 'se': (res[0] - lg_sz[0], res[1] - lg_sz[1])
                 }

        if dict1.get(coor):
            bg.paste(lg, dict1.get(coor), lg)
            bg.save('out.jpg')
        else:
            bg.paste(lg, dict1.get('sw'), lg)
            bg.save('out.jpg')
        caption = id_remove(re.sub(':\S{,2}:', '', caption)) if re.search(r':\S{,2}:', caption) else id_remove(caption)
        return caption
    except Exception as E:
        print(4004, E)


# region DataBase


def create_db():
    try:
        db_connect.execute("CREATE TABLE IF NOT EXISTS Queue("
                           "ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,"
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
        db_connect.commit()
    except Exception as E:
        print(E)


def insert(kind, from_ad, file_id, caption, gp):
    try:
        cursor.execute("INSERT INTO Queue(kind, from_ad, file_id, caption, gp, ch_a) VALUES(?,?,?,?,?,?)",
                       (kind, from_ad, file_id, caption, gp, 0))
        db_connect.commit()
    except Exception as E:
        print(E)


# 2002
# todo edit this like insert()
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


# endregion

# region bot


# 3003
def save(bot, update):
    try:
        from_ad = update.message.from_user.id
        um = update.message
        ue = update.edited_message
        kind = name = text = file_id = 'none'
        if ue:
            gp_id = ue.message_id
            out = [cursor.execute("SELECT * FROM Queue WHERE gp = {0}".format(gp_id)).fetchall()][0][0]
            if ue.text and out[ch_a] == 1:
                text = id_remove(ue.text)
                robot.edit_message_text(chat_id=channel, message_id=out[5], text=text)
            elif ue.caption and out[ch_a] == 1:
                text = id_remove(ue.caption)
                robot.edit_message_caption(chat_id=channel, message_id=out[5], caption=id_remove(text))
            elif ue.text:
                text = ue.text
                db_edit(caption=text, gp=gp_id, edited=1, sent=0)
            elif ue.caption:
                text = ue.caption
                db_edit(caption=text, gp=gp_id, edited=1, sent=0)
        elif um:
            gp_id = um.message_id
            if um.text:
                if str(um.text).startswith('.'):
                    pass
                else:
                    text = id_remove(um.text)
                    kind = 'text'
                    insert(kind=kind, from_ad=from_ad, file_id=file_id, caption=text, gp=gp_id)
            else:
                text = id_remove(um.caption) if um.caption else id_remove('')
                if str(text).startswith('.'):
                    pass
                else:
                    if um.photo:
                        kind = 'photo'
                        file_id = um.photo[-1].file_id
                    elif um.video:
                        kind = 'video'
                        file_id = um.video.file_id
                    elif um.document:
                        kind = 'document'
                        file_id = um.document.file_id
                    elif um.voice:
                        kind = 'voice'
                        file_id = um.voice.file_id
                    elif um.audio:
                        kind = 'audio'
                        file_id = um.audio.file_id
                    elif um.video_note:
                        kind = 'v_note'
                        file_id = um.video_note.file_id
                    insert(kind=kind, from_ad=from_ad, file_id=file_id, caption=text, gp=gp_id)
    except Exception as E:
        print(4004, E)


# 1001
def send_to_ch():
    try:
        out = [i for i in cursor.execute("SELECT * FROM Queue WHERE sent=0 ORDER BY ID LIMIT 1")][0]
        if out[edited] == 1 and out[sent] == 0 and out[ch_a] == 1:
            if out[kind] == 'text':
                robot.edit_message_text(chat_id=channel, text=out[text], message_id=out[5])
                cursor.execute("UPDATE Queue SET sent=1 WHERE ID = {0}".format(out[0]))
                db_connect.commit()
            else:
                robot.edit_message_caption(chat_id=channel, caption=out[text], message_id=out[5])
                cursor.execute("UPDATE Queue SET sent=1 WHERE ID = {0}".format(out[0]))
                db_connect.commit()
        elif out[sent] == 0 or out[ch_a] == 0:
            if out[kind] == 'text':
                db_set(robot.send_message(chat_id=channel, text=out[text]).message_id, out[0])
            elif out[kind] == 'video':
                db_set(robot.send_video(chat_id=channel, video=out[3], caption=out[text]).message_id, out[0])
            elif out[kind] == 'photo':
                cap = put(out[3], out[text])
                db_set(robot.send_photo(chat_id=channel, photo=open('out.jpg', 'rb'), caption=cap).message_id,
                       out[0])
            elif out[kind] == 'audio':
                db_set(robot.send_audio(chat_id=channel, audio=out[3], caption=out[text]).message_id, out[0])
            elif out[kind] == 'document':
                db_set(robot.send_document(chat_id=channel, document=out[3], caption=out[text]).message_id, out[0])
            elif out[kind] == 'v_note':
                db_set(robot.send_video_note(chat_id=channel, video_note=out[3]).message_id, out[0])
            elif out[kind] == 'voice':
                db_set(robot.send_voice(chat_id=channel, voice=out[3], caption=out[text]).message_id, out[0])
            admins = [i for i in cursor.execute("SELECT * FROM Activity").fetchall()]
            for j in admins:
                if out[1] in j:
                    cursor.execute(
                        "UPDATE Activity SET message_count={0} WHERE user_id={1}".format(j[3] + 1, out[1]))
                    db_connect.commit()
    except IndexError:
        pass
    except Exception as E:
        print(1001, E)


create_db()
dp = updater.dispatcher
updater.start_polling()
while True:
    time.sleep(1)
    dp.add_handler(MessageHandler(Filters.all, save, edited_updates=True))
    if 50000 < int(current_time()[1]) < 90000:
        time.sleep(10)
    elif int(current_time()[1][2:]) in day:
        send_to_ch()
    if int(current_time()[1]) == 0:
        with open('daylog.txt', 'a') as log:
            log.write('\n' + str(robot.get_chat_members_count(channel)) + ' '.join(current_time()))
    if int(current_time()[1]) == 14230 and current_time()[2].lower() == 'sat':
        print('pie time')
        data = []
        label = []
        for d in [i for i in db_connect.execute("SELECT * FROM Activity")]:
            label.append(d[1])
            data.append(d[3])
        # todo fill activity database first
        plt.axes(aspect=1)
        plt.pie(x=data, labels=label, shadow=True, explode=(0, 0.1, 0, 0), startangle=90, autopct='%1.1f%%',
                radius=1.2)
        plt.savefig('plot.jpg')
        robot.send_photo(chat_id=channel, photo=open('plot.jpg', 'rb'), caption='Sina')
# endregion
