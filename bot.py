from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
from khayyam import JalaliDate, JalaliDatetime
from datetime import datetime, timedelta
from pprint import pprint
from database import *
from PIL import Image
import matplotlib
import telegram
import psutil
import pytz
import time
import var
import re
matplotlib.use('AGG')
import matplotlib.pyplot as plt

kind, text, edited, sent, ch_a = 2, 4, 7, 8, 9


class SSP:
    def __init__(self, token):
        self.robot = telegram.Bot(token)
        self.updater = Updater(token)
        self.channel_name = var.channel_name
        self.group_id = var.group_id
        self.day = tuple(range(0, 6000, 1100))
        self.bed_time = 30000
        self.wake_time = 90000

    def set_delay(self, bot, update, args):
        try:
            if args:
                entry = str(args[0])
                if entry.isdecimal():
                    if 0 < int(entry) < 60:
                        entry = int(entry) * 100
                        self.day = tuple(range(0, 6000, entry))
                        bot.send_message(chat_id=update.message.chat_id,
                                         text='delay = <b>{}</b> minute'.format(args[0]),
                                         parse_mode='HTML')
        except Exception as E:
            bot.send_message(chat_id=update.message.chat_id, text='اشتباه: یک عدد صحیح بین ۱ تا ۵۹ بفرستید')

    def set_bed(self, bot, update, args):
        try:
            if args:
                entry = str(args[0])
                if -1 < int(entry) < 25:
                    if 0 < len(entry) < 3:
                        bot.send_message(chat_id=update.message.chat_id, parse_mode='HTML',
                                         text='<b>bed</b> time starts from <b>{}</b>'.format(args[0]))
                        self.bed_time = int(entry) * 10000
        except Exception as E:
            bot.send_message(chat_id=update.message.chat_id, text='ERROR')

    def set_wake(self, bot, update, args):
        try:
            if args:
                entry = str(args[0])
                if -1 < int(entry) < 25:
                    if 0 < len(entry) < 3:
                        bot.send_message(chat_id=update.message.chat_id, parse_mode='HTML',
                                         text='<b>wake</b> time starts from <b>{}</b>'.format(args[0]))
                        self.wake_time = int(entry) * 10000
        except Exception as E:
            bot.send_message(chat_id=update.message.chat_id, text='ERROR')

    @staticmethod
    def current_time():
        utc = pytz.utc
        u = time.gmtime()
        utc_dt = datetime(u[0], u[1], u[2], u[3], u[4], u[5], tzinfo=utc)
        eastern = pytz.timezone('Asia/Tehran')
        loc_dt = utc_dt.astimezone(eastern)
        return JalaliDatetime().now().strftime('%Y-%m-%d'), loc_dt.strftime('%H%M%S')

    def id_remove(self, entry):
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
            if entry.lower().strip()[len(self.channel_name)*(-2):].find('@crazymind3') == -1:
                entry = entry + '\n@CrazyMind3'
            return entry
        else:
            return entry + '\n@CrazyMind3'

    # 4004
    def put(self, photo, caption):
        try:
            self.robot.getFile(photo).download('tmp.jpg')
            pattern = re.compile(r':(\S{1,2}):', re.I)
            coor_pt = re.compile(r'(nw|ne|nc|cw|cc|ce|sw|sc|se|no|e|n|w|s)', re.I)
            if re.search(pattern, caption):
                i_cor = ''.join(re.findall(pattern, caption)[0]).lower()
                coor = re.findall(coor_pt, i_cor)[0] if re.findall(coor_pt, i_cor)[0] else 'sw'
            else:
                coor = 'sw'
            bg = Image.open('tmp.jpg')
            if not coor == 'no':
                lg = Image.open('CC.png')
                res, lg_sz = bg.size, lg.size
                def_l, def_p, box_def, n_def = (4000, 1100), (1100, 4000), (3500, 3500), None
                if res[0] > res[1]:
                    n_def = [int((lg_sz[0] * res[0]) / def_l[0]), int((lg_sz[1] * res[1]) / def_l[1])]
                elif res[0] == res[1]:
                    if not res == box_def:
                        n_def = [int((lg_sz[0] * res[0]) / box_def[0]), int((lg_sz[1] * res[1]) / box_def[1])]
                else:
                    n_def = [int((lg_sz[0] * res[0]) / def_p[0]), int((lg_sz[1] * res[1]) / def_p[1])]

                lg.thumbnail(n_def, Image.ANTIALIAS)
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
                    bg.paste(lg, dict1.get(coor, 'sw'), lg)
                    bg.save('out.jpg')
            else:
                bg.save('out.jpg')
            if re.search(r':\S{,2}:', caption):
                caption = self.id_remove(re.sub(':\S{,2}:', '', caption))
            else:
                caption = self.id_remove(caption)

            return caption
        except Exception as E:

            print(4004, E)

    # 3003
    def save(self, bot, update):
        try:
            um = update.message
            ue = update.edited_message
            kind = name = text = file_id = 'none'
            if ue:
                gp_id = ue.message_id
                out = [cursor.execute("SELECT * FROM Queue WHERE gp = {0}".format(gp_id)).fetchall()][0][0]
                if ue.text and out[ch_a] == 1:
                    text = self.id_remove(ue.text)
                    self.robot.edit_message_text(chat_id=self.channel_name, message_id=out[6], text=text)
                elif ue.caption and out[ch_a] == 1:
                    text = self.id_remove(ue.caption)
                    self.robot.edit_message_caption(chat_id=self.channel_name, message_id=out[6], caption=text)
                elif ue.text:
                    text = ue.text
                    db_edit(caption=text, gp=gp_id, edited=1, sent=0)
                elif ue.caption:
                    text = ue.caption
                    db_edit(caption=text, gp=gp_id, edited=1, sent=0)
            elif um:
                in_date = ' '.join(self.current_time())
                from_ad = um.from_user.id if um.from_user.id else 'none'
                gp_id = um.message_id
                if um.text:
                    text = um.text
                    kind = 'text'
                    insert(kind=kind, from_ad=from_ad, file_id=file_id, caption=text, gp=gp_id, in_date=in_date)
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
                        insert(kind=kind, from_ad=from_ad, file_id=file_id, caption=text, gp=gp_id, in_date=in_date)

        except Exception as E:
            print(3003, E)

    # 1001
    def send_to_ch(self):
        try:
            out = [i for i in cursor.execute("""
            SELECT * FROM Queue WHERE sent=0 AND 
            caption NOT LIKE '.%' AND 
            caption NOT LIKE '/%' 
            ORDER BY ID LIMIT 1""")][0]
            cp = self.id_remove(out[text])
            if out[edited] == 1 and out[sent] == 0 and out[ch_a] == 1:
                if out[kind] == 'text':
                    self.robot.edit_message_text(chat_id=self.channel_name, text=cp, message_id=out[5])
                    cursor.execute("UPDATE Queue SET sent=1 WHERE ID = {0}".format(out[0]))
                    db_connect.commit()
                else:
                    self.robot.edit_message_caption(chat_id=self.channel_name, caption=cp, message_id=out[5])
                    cursor.execute("UPDATE Queue SET sent=1 WHERE ID = {0}".format(out[0]))
                    db_connect.commit()
            elif out[sent] == 0 or out[ch_a] == 0:
                ch = None
                if out[kind] == 'text':
                    ch = self.robot.send_message(chat_id=self.channel_name, text=cp).message_id
                elif out[kind] == 'video':
                    ch = self.robot.send_video(chat_id=self.channel_name, video=out[3], caption=cp).message_id
                elif out[kind] == 'photo':
                    cap = self.put(out[3], out[text])
                    ch = self.robot.send_photo(chat_id=self.channel_name, photo=open('out.jpg', 'rb'),
                                               caption=cap).message_id
                elif out[kind] == 'audio':
                    ch = self.robot.send_audio(chat_id=self.channel_name, audio=out[3], caption=cp).message_id
                elif out[kind] == 'document':
                    ch = self.robot.send_document(chat_id=self.channel_name, document=out[3], caption=cp).message_id
                elif out[kind] == 'v_note':
                    ch = self.robot.send_video_note(chat_id=self.channel_name, video_note=out[3]).message_id
                elif out[kind] == 'voice':
                    ch = self.robot.send_voice(chat_id=self.channel_name, voice=out[3], caption=cp).message_id
                db_set(ch=ch, i_d=out[0], out_date=' '.join(self.current_time()), )
        except IndexError:
            pass
        except Exception as E:
            print(1001, E)

    @staticmethod
    def _before(year=None, months=None):
        out = None
        if year and months:
            before = JalaliDate().strptime(year + months, '%Y%m') - timedelta(days=1)
            out = [db_connect.execute("SELECT * FROM Mem_count WHERE ddd = '{}'".format(str(before))).fetchone()]
            out.extend([i for i in db_connect.execute(
                "SELECT * FROM Mem_count WHERE ddd LIKE '{}-{}%'".format(year, months)).fetchall()])
        return out

    def report_members(self, bot, update, args):
        try:
            param = days = out = months = year = title = plus = predict = tmp = None
            if args:
                param = str(args[0]).lower()
                if re.fullmatch(r'd[0-9]*', param):
                    days = param[1:]
                    out = [i for i in db_connect.execute("SELECT * FROM Mem_count ORDER BY ID DESC LIMIT {}".format(days))]
                    out = [j for j in reversed(out)]
                    title = '{} days'.format(days)
                    plus = True
                elif re.fullmatch(r'm[0-9]*', param):
                    months = param[1:]
                    year = self.current_time()[0][:4]
                    out = self._before(year, months)
                    title = 'graph of {}-{}'.format(year, months)
                    if year + months == str(self.current_time()[0].replace('-', '')[:6]):
                        plus = predict = True
                elif re.fullmatch(r'y[0-9]*', param):
                    year = '13' + param[1:] if len(param) == 3 else param[1:]
                    out = [i for i in db_connect.execute("SELECT * FROM Mem_count WHERE ddd LIKE '{}%'".format(year))]
                    title = 'graph of {}'.format(year)
                    if year == self.current_time()[0][:4]:
                        plus = True
                elif re.fullmatch(r'[0-9]*-[0-9]*', param):
                    year = param[:2]
                    months = param[3:]
                    out = self._before(year, months)
                    title = 'graph of 20{}-{}'.format(year, months)
                    if year + months == ''.join(self.current_time()[0].split('-'))[:6]:
                        plus = True
            else:
                out = db_connect.execute("SELECT * FROM Mem_count").fetchall()
                title = "starts from {}".format(out[0][1])
                plus = True
            if out:
                members = [i for i in [j[3] for j in out]]
                balance = [i for i in [j[2] for j in out]]
                average = sum(balance) / len(balance)
                caption = '{}\nbalance = {}\naverage = {:.2f}\nfrom {} till {}'.format(
                    title, members[-1] - members[0], average, members[0], members[-1])
                if plus:
                    now = self.robot.get_chat_members_count(self.channel_name)
                    balance.append(now - members[-1])
                    members.append(now)
                    if predict:
                        tmp = members.copy()
                        [tmp.append(int(tmp[-1] + average)) for _ in range(30 - len(members))]
                        plt.plot(range(1, len(tmp) + 1), tmp, marker='o', linestyle=' ', label='predict', color='grey', markersize=4)
                        caption = '{}\nbalance = {}\naverage = {:.2f}\nfrom {} till {}\npredict till this month = {}' \
                                  ''.format(title, members[-1] - members[0], average, members[0], members[-1], tmp[-1])

                    plt.plot(range(1, len(members) + 1), members, marker='o', label='now', color='red', markersize=4)
                    plt.plot(range(1, len(members)), members[:-1], marker='o', label='members', color='blue', markersize=4)
                else:
                    plt.plot(range(1, len(members) + 1), members, marker='o', label='members', color='blue', markersize=4)
                plt.grid()
                plt.xlabel('days')
                plt.ylabel('members')
                plt.title(title)
                plt.legend(loc=4)
                plt.savefig('plot.png')
                bot.send_photo(chat_id=update.message.chat_id, photo=open('plot.png', 'rb'), caption=caption)
                plt.close()
        except Exception as E:
            self.robot.send_message(chat_id=update.message.chat_id, text='**ERROR {}**'.format(update.message.text),
                                    parse_mode='Markdown')
            print(E)

    def remain(self, bot, update):
        try:
            remaining = len(db_connect.execute(
                "SELECT ID FROM Queue WHERE sent = 0 and caption not like '.%' and caption not like '/%'").fetchall())
            now = JalaliDatetime().strptime(' '.join(self.current_time()), '%Y-%m-%d %H%M%S')
            step = now
            minutes = int(str(self.day[1])[:-2])
            for ـ in range(remaining):
                if self.bed_time <= step.hour < self.wake_time:
                    step += timedelta(hours=self.wake_time - step.hour)
                step += timedelta(minutes=minutes)
            if remaining > 0:
                text = '{} remaining\nchannel will feed untill <b>{}</b>'.format(
                                 remaining, step.strftime('%y-%m-%d -> %H:%M'))
            else:
                text = '{} remaining'
            bot.send_message(chat_id=update.message.chat_id,
                             text=text, parse_mode='HTML')
        except Exception as E:
            print(E)

    def sleep(self):
        if int(self.current_time()[1]) > self.bed_time > self.wake_time < int(self.current_time()[1]) or \
           int(self.current_time()[1]) > self.bed_time < self.wake_time > int(self.current_time()[1]):
            return True
        return False

    def add_member(self):
        try:
            mem = [self.robot.get_chat_members_count(self.channel_name)]
            try:
                last = db_connect.execute("SELECT members FROM Mem_count ORDER BY ID DESC LIMIT 1").fetchone()
            except IndexError:
                last = mem[0]
            last = last if last else mem
            cursor.execute("INSERT INTO Mem_count(ddd, balance, members) VALUES(?,?,?)",
                           (self.current_time()[0], mem[0] - last[0], mem[0]))
            db_connect.commit()
        except Exception as E:
            print("Mem_count didn't updated")

    def start(self):
        dp = self.updater.dispatcher
        self.updater.start_polling()

        print('started')
        while True:
            dp.add_handler(CommandHandler('report', self.report_members, pass_args=True))
            dp.add_handler(CommandHandler('delay', self.set_delay, pass_args=True))
            dp.add_handler(CommandHandler('bed', self.set_bed, pass_args=True))
            dp.add_handler(CommandHandler('wake', self.set_wake, pass_args=True))
            dp.add_handler(CommandHandler('remain', self.remain))
            dp.add_handler(MessageHandler(Filters.chat(self.group_id), self.save, edited_updates=True))

            if int(self.current_time()[1][2:]) == 0:
                self.robot.send_message(chat_id=103086461, text=psutil.virtual_memory()[2])

            elif self.sleep():
                    pass

            elif int(self.current_time()[1][2:]) in self.day and not int(self.current_time()[1][2:]) == 0:
                self.send_to_ch()

            elif int(self.current_time()[1]) == self.bed_time - 4100:
                self.robot.send_message(chat_id=self.channel_name,
                                        text='''دوستانِ عزیزی که تمایل به تبادل دارن به آیدیِ زیر پیام بدن
                    👉🏻 @Mmd_bt 👈🏻
                    شرایط در پی‌وی گفته میشه🍁
                    #اینجا_همه_چی_درهمه😂😢😭😈❤️💋💏💔

                    برای پاسخگویی لطفا صبور باشید🤠

                    @crazymind3''')

            if int(self.current_time()[1]) == 0:
                self.add_member()

            time.sleep(1)


timer = SSP(var.TOKEN)
timer.start()
