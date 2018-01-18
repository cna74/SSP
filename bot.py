from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
from pprint import pprint
from PIL import Image
from database import *
import telegram
import datetime
import pytz
import time
import re
import matplotlib
matplotlib.use('AGG')
import matplotlib.pyplot as plt

# region vars
TOKEN = '410818874:AAEU8gHdOmurgJBf_N_p-58qVW94Rc_vgOc'
updater = Updater(TOKEN)
robot = telegram.Bot(TOKEN)
day = tuple(range(0, 6000, 1100))
kind, text, edited, sent, ch_a = 2, 4, 7, 8, 9
channel = '@ttiimmeerr'
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
    pattern1 = re.compile(r'(:\S{1,2}:)', re.I)
    if re.search(pattern1, entry):
        logo = re.findall(pattern1, entry)[0]
        entry = re.sub(pattern1, '', entry)
        entry = logo + entry
    if re.search(pattern, entry):
        state = re.findall(pattern, entry)
        for state in state:
            if state.lower() not in ('@crazymind3', '@mmd_bt'):
                entry = re.sub(state, '@CrazyMind3', entry)
        if not entry.lower().strip().endswith('@crazymind3'):
            entry = entry + '\n@CrazyMind3'
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
            n_deaf = [int((lg_sz[0] * res[0]) / deaf_l[0]), int((lg_sz[1] * res[1]) / deaf_l[1])]
            lg.thumbnail(n_deaf)

        elif res[0] == res[1]:
            if not res == box_deaf:
                n_deaf = [int((lg_sz[0] * res[0]) / box_deaf[0]), int((lg_sz[1] * res[1]) / box_deaf[1])]
                lg.thumbnail(n_deaf)

        else:
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


# region bot


# 3003
def save(bot, update):
    try:
        print(1)
        um = update.message
        ue = update.edited_message
        kind = name = text = file_id = 'none'
        if ue:
            gp_id = ue.message_id
            out = [cursor.execute("SELECT * FROM Queue WHERE gp = {0}".format(gp_id)).fetchall()][0][0]
            if ue.text and out[ch_a] == 1:
                text = id_remove(ue.text)
                robot.edit_message_text(chat_id=channel, message_id=out[6], text=text)
            elif ue.caption and out[ch_a] == 1:
                text = id_remove(ue.caption)
                robot.edit_message_caption(chat_id=channel, message_id=out[6], caption=text)
            elif ue.text:
                text = ue.text
                db_edit(caption=text, gp=gp_id, edited=1, sent=0)
            elif ue.caption:
                text = ue.caption
                db_edit(caption=text, gp=gp_id, edited=1, sent=0)
        elif um:
            from_ad = um.from_user.id if um.from_user.id else 'none'
            gp_id = um.message_id
            if um.text:
                text = um.text
                kind = 'text'
                insert(kind=kind, from_ad=from_ad, file_id=file_id, caption=text, gp=gp_id)
            else:
                text = um.caption if um.caption else ''
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
                if kind in ('photo', 'video', 'document', 'voice', 'audio', 'v_note'):
                    insert(kind=kind, from_ad=from_ad, file_id=file_id, caption=text, gp=gp_id)

    except Exception as E:
        print(3003, E)


# 1001
def send_to_ch():
    try:
        out = [i for i in cursor.execute(
            "SELECT * FROM Queue WHERE sent=0 AND caption NOT LIKE '.%' AND caption NOT LIKE '/%' ORDER BY ID LIMIT 1")][0]
        cp = id_remove(out[text])
        if out[edited] == 1 and out[sent] == 0 and out[ch_a] == 1:
            if out[kind] == 'text':
                robot.edit_message_text(chat_id=channel, text=cp, message_id=out[5])
                cursor.execute("UPDATE Queue SET sent=1 WHERE ID = {0}".format(out[0]))
                db_connect.commit()
            else:
                robot.edit_message_caption(chat_id=channel, caption=cp, message_id=out[5])
                cursor.execute("UPDATE Queue SET sent=1 WHERE ID = {0}".format(out[0]))
                db_connect.commit()
        elif out[sent] == 0 or out[ch_a] == 0:
            if out[kind] == 'text':
                db_set(robot.send_message(chat_id=channel, text=cp).message_id, out[0])
            elif out[kind] == 'video':
                db_set(robot.send_video(chat_id=channel, video=out[3], caption=cp).message_id, out[0])
            elif out[kind] == 'photo':
                cap = put(out[3], out[text])
                db_set(robot.send_photo(chat_id=channel, photo=open('out.jpg', 'rb'), caption=cap).message_id, out[0])
            elif out[kind] == 'audio':
                db_set(robot.send_audio(chat_id=channel, audio=out[3], caption=cp).message_id, out[0])
            elif out[kind] == 'document':
                db_set(robot.send_document(chat_id=channel, document=out[3], caption=cp).message_id, out[0])
            elif out[kind] == 'v_note':
                db_set(robot.send_video_note(chat_id=channel, video_note=out[3]).message_id, out[0])
            elif out[kind] == 'voice':
                db_set(robot.send_voice(chat_id=channel, voice=out[3], caption=cp).message_id, out[0])
    except IndexError:
        pass
    except Exception as E:
        print(1001, E)


def report_members(bot, update, args):
    try:
        param = days = out = months = year = title = None
        param = str(args[0]).lower()
        if re.fullmatch(r'd[0-9]*', param):
            days = param[1:]
            out = [i for i in db_connect.execute("SELECT * FROM Mem_count ORDER BY ID DESC LIMIT {}".format(days))]
            title = '{} days'.format(days)
        elif re.fullmatch(r'm[0-9]*', param):
            months = param[1:]
            year = current_time()[0][:4]
            out = [i for i in db_connect.execute("SELECT * FROM Mem_count WHERE ddd LIKE '{}-{}%' ORDER BY ID DESC".format(year, months))]
            title = 'graph of {}-{}'.format(year, months)
        elif re.fullmatch(r'y[0-9]*', param):
            year = '20'+param[1:] if len(param) == 3 else param[1:]
            out = [i for i in db_connect.execute("SELECT * FROM Mem_count WHERE ddd LIKE '{}%' ORDER BY ID DESC".format(year))]
            pprint(out)
            title = 'graph of {}'.format(year)
        elif re.fullmatch(r'[0-9]*-[0-9]*', param):
            year = param[:2]
            months = param[3:]
            days = 32
            out = [i for i in db_connect.execute("SELECT * FROM Mem_count WHERE ddd LIKE '20{}-{}%' ORDER BY ID DESC".format(year, months))]
            title = 'graph of 20{}-{}'.format(year, months)
        if months or year or int(days) <= len(out):
            balance = [j[3] for j in out]
            balance = [i for i in reversed(balance)]
            balance.append(robot.get_chat_members_count(channel))
            plt.xlabel('days')
            plt.ylabel('members')
            plt.title(title)
            plt.plot(range(1, len(balance) + 1), balance, marker='o', linestyle='--', label='now', color='red', markersize=4)
            plt.plot(range(1, len(balance)), balance[:-1], marker='o', linestyle='--', label='members', color='blue', markersize=4)
            plt.legend(loc=4)
            plt.savefig('plot.jpg')
            bot.send_photo(chat_id=update.message.chat_id,
                           photo=open('plot.jpg', 'rb'),
                           caption='balance = {}\nfrom {} till today'.format(balance[-1] - balance[0], out[-1][1]))
            plt.close()
        # elif days.isnumeric and not int(days) <= len(out):
        #     bot.send_message(update.message.chat_id, 'فعلا بیشتر از {} تا رو نمیتونم'.format(len(out)))
        #
         else:
             bot.send_message(update.message.chat_id, 'والا خودمم نمیدونم چه مرگمه. بابامو خبر کن 😢😭')
    except Exception as E:
        print(E)


dp = updater.dispatcher
updater.start_polling()
while True:
    dp.add_handler(CommandHandler('report', report_members, pass_args=True))
    dp.add_handler(MessageHandler(Filters.chat(-1001141277396), save, edited_updates=True))

    if 30000 < int(current_time()[1]) < 90000:
        time.sleep(20)

    elif int(current_time()[1][2:]) in day and not int(current_time()[1][2:]) == 0:
        send_to_ch()

    if int(current_time()[1]) == 0:
        mem = [robot.get_chat_members_count(channel)]
        try:
            last = db_connect.execute("SELECT members FROM Mem_count ORDER BY ID DESC LIMIT 1").fetchone()
        except IndexError:
            last = mem[0]
        last = last if last else mem
        cursor.execute("INSERT INTO Mem_count(ddd, balance, members) VALUES(?,?,?)",
                       (current_time()[0], mem[0] - last[0], mem[0]))
        db_connect.commit()
    time.sleep(1)
# endregion
