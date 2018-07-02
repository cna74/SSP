from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
from khayyam import JalaliDate, JalaliDatetime
from datetime import datetime, timedelta
from pprint import pprint
from database import *
from PIL import Image
import matplotlib
import telegram
import logging
import pytz
import time
import var
import re
import os
matplotlib.use('AGG', force=True)
import matplotlib.pyplot as plt

# sina, lili, fery = 103086461, 303962908, 319801025
admins = var.admins
sina = var.sina
logging.basicConfig(filename='report.log', level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s')


class SSP:
    def __init__(self, token):
        self.robot = telegram.Bot(token)
        self.updater = Updater(token)
        self.channel_name = var.channel_name
        self.group_id = var.group_id
        self.delay = [600, 1200, 1800, 2100]
        self.bed_time = 210000
        self.wake_time = 60000

    @staticmethod
    def current_time():
        utc = pytz.utc
        u = time.gmtime()
        utc_dt = datetime(u[0], u[1], u[2], u[3], u[4], u[5], tzinfo=utc)
        eastern = pytz.timezone('Asia/Tehran')
        loc_dt = utc_dt.astimezone(eastern)
        return JalaliDatetime().now().strftime('%Y-%m-%d'), loc_dt.strftime('%H%M%S')

    @staticmethod
    def _before(year=None, months=None, plot='plot') -> list:
        out = None
        if year and months:
            before = JalaliDate().strptime(year + months, '%Y%m') - timedelta(days=1)
            if plot == 'plot':
                out = [db_connect.execute("SELECT * FROM Mem_count WHERE ddd = '{}'".format(str(before))).fetchone()]
                out.extend([i for i in db_connect.execute(
                    "SELECT * FROM Mem_count WHERE ddd LIKE '{}-{}%'".format(year, months)).fetchall()])
            elif plot == 'pie':
                out = [i[0] for i in db_connect.execute(
                    "SELECT from_ad FROM Queue WHERE ch_a=1 AND out_date LIKE '{}-{}%'".format(
                        year, months)).fetchall()]
        return out

    # region CommandHandlers
    # setters

    # def set_delay(self, bot, update, args):
    #     try:
    #         if args:
    #             entry = str(args[0])
    #             if entry.isdecimal():
    #                 if 1 <= int(entry) < 60:
    #                     entry = int(entry)
    #                     if entry % 5 == 0 and entry <= 30:
    #                         self.delay = tuple(range(0, 60, entry))
    #                     else:
    #                         self.delay = tuple(range(entry, 60, entry))
    #                     bot.send_message(chat_id=update.message.chat_id,
    #                                      text='delay = <b>{}</b> minute'.format(args[0]),
    #                                      parse_mode='HTML')
    #     except Exception as _:
    #         bot.send_message(chat_id=update.message.chat_id, text='<b>Error</b>')

    def set_bed(self, bot, update, args):
        try:
            if args:
                entry = str(args[0])
                if 0 <= int(entry) < 24:
                    bot.send_message(chat_id=update.message.chat_id, parse_mode='HTML',
                                     text='<b>bed</b> time starts from <b>{}</b>'.format(str(args[0]) + ':00'))
                    self.bed_time = int(entry) * 10000
        except Exception as E:
            bot.send_message(chat_id=update.message.chat_id, text='ERROR')

    def set_wake(self, bot, update, args):
        try:
            if args:
                entry = str(args[0])
                if 0 <= int(entry) < 24:
                    bot.send_message(chat_id=update.message.chat_id, parse_mode='HTML',
                                     text='<b>wake</b> time starts from <b>{}</b>'.format(str(args[0]) + ':00'))
                    self.wake_time = int(entry) * 10000
        except Exception as E:
            bot.send_message(chat_id=update.message.chat_id, text='ERROR')

    def state(self, bot, update):
        try:
            bot.send_message(chat_id=update.message.chat_id,
                             text='<b>delay =</b> {}\n<b>bed =</b> {}\n<b>wake = </b>{}'.format(
                                 self.delay, str(self.bed_time)[:-4], str(self.wake_time)[:-4]),
                             parse_mode='HTML')
            logging.info("/state by {}".format(update.message.from_user))
        except Exception as E:
            logging.error("/state {} by {}".format(E, update.message.from_user))

    def report_members(self, bot, update, args):
        try:
            param = days = out = months = year = title = plus = predict = None
            if args:
                param = str(args[0]).lower()
                year_month = re.compile(r"(?P<year>\d{,4})-(?P<month>\d{,2})")
                if re.fullmatch(r'd\d*', param):
                    days = param[1:]
                    out = [i for i in
                           db_connect.execute("SELECT * FROM Mem_count ORDER BY ID DESC LIMIT {}".format(days))]
                    out = [j for j in reversed(out)]
                    title = '{} days'.format(days)
                    plus = True
                elif re.fullmatch(r'm\d{,2}', param):
                    months = param[1:].zfill(2)
                    year = self.current_time()[0][:4]
                    out = self._before(year, months)
                    title = 'graph of {}-{}'.format(year, months)
                    if year + months == str(self.current_time()[0].replace('-', '')[:6]):
                        plus = predict = True
                elif re.fullmatch(r'y\d{,2}', param):
                    year = '13' + param[1:] if len(param) == 3 else param[1:]
                    out = [i for i in db_connect.execute("SELECT * FROM Mem_count WHERE ddd LIKE '{}%'".format(year))]
                    title = 'graph of {}'.format(year)
                    if year == self.current_time()[0][:4]:
                        plus = True
                elif re.fullmatch(year_month, param):
                    date = re.fullmatch(year_month, param)
                    year = '13' + date.group('year') if len(date.group('year')) == 2 else date.group('year')
                    months = date.group('month')
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
                    average = sum(balance) / len(balance)
                    caption = '{}\nbalance = {}\naverage = {:.2f}\nfrom {} till {}'.format(
                        title, members[-1] - members[0], average, members[0], members[-1])
                    days_of_this_month = JalaliDatetime.now().daysinmonth
                    if predict and not (average * (days_of_this_month - len(members))) <= 0:
                        pdt = int(members[-1] + (average * (days_of_this_month - len(members))))
                        caption += '\npredict of month = {}'.format(pdt)
                    plt.plot(range(1, len(members) + 1), members, marker='o', label='now', color='red', markersize=4)
                    plt.plot(range(1, len(members)), members[:-1], marker='o', label='members', color='blue',
                             markersize=4)
                else:
                    plt.plot(range(1, len(members) + 1), members, marker='o', label='members', color='blue',
                             markersize=4)
                plt.grid()
                plt.xlim(1, )
                plt.xlabel('days')
                plt.ylabel('members')
                plt.title(title)
                plt.legend(loc=4)
                plt.savefig('plot/plot.png')
                bot.send_photo(chat_id=update.message.chat_id, photo=open('plot/plot.png', 'rb'), caption=caption)
                plt.close()
            logging.info('plot:: args {} -- by: {}'.format(args, update.message.from_user))
        except TimeoutError:
            pass
        except Exception as E:
            self.robot.send_message(chat_id=update.message.chat_id,
                                    text='**ERROR {}**'.format(update.message.text),
                                    parse_mode='Markdown')
            logging.error("Could't get plot:: args {} -- {} - by: {}".format(args, E, update.message.from_user))

    def report_admins(self, bot, update, args):
        try:
            param = out = title = None
            if args:
                pattern = re.compile(r"(?P<year>\d{,4})-(?P<month>\d{,2})")
                param = str(args[0]).lower()
                if re.fullmatch(r'm\d{,2}', param):
                    months = param[1:].zfill(2)
                    year = self.current_time()[0][:4]
                    out = self._before(year, months, plot='pie')
                    title = 'graph of {}-{}'.format(year, months)
                elif re.fullmatch(pattern, param):
                    date = re.fullmatch(pattern, param)
                    year = '13' + date.group('year') if len(date.group('year')) == 2 else date.group('year')
                    months = date.group('month').zfill(2)
                    out = self._before(year, months, plot='pie')
                    title = 'graph of {}-{}'.format(year, months)
            else:
                out = [i[0] for i in db_connect.execute("SELECT from_ad FROM Queue WHERE ch_a=1").fetchall()]
                title = 'graph of all time'
            tmp = set(out.copy())
            admins = {}
            for i in tmp:
                admins[str(i)] = out.count(i)
            for k in admins.keys():
                try:
                    j = self.robot.get_chat(k).to_dict()
                    if j.get('first_name') and j.get('last_name'):
                        count = admins[k]
                        del admins[k]
                        admins[(' '.join([j['first_name']] + [j['last_name']]))] = count
                    elif j.get('first_name'):
                        count = admins[k]
                        del admins[k]
                        admins[j['first_name']] = count
                except Exception as E:
                    pass
            ex = [[x, y] for x, y in admins.items()]
            data = [x[1] for x in ex]
            labels = ["{}\n{}".format(x[0], x[1]) for x in ex]
            explode = [0.1 for _ in labels]
            plt.figure(figsize=(12.80, 7.20))
            plt.title(title)
            plt.axes(aspect=1)
            plt.pie(x=data, labels=labels, explode=explode, startangle=90,
                    autopct='%1.1f%%', radius=1.25, labeldistance=1.14, pctdistance=.9)
            plt.savefig('plot/pie.jpg')
            bot.send_photo(photo=open('plot/pie.jpg', 'rb'), chat_id=update.message.chat_id)
            plt.close()
            os.remove('./plot/pie.jpg')
        except Exception as E:
            logging.error('report admins {}'.format(E))

    def remain(self, bot, update):
        try:
            remaining = len(db_connect.execute(
                "SELECT ID FROM Queue WHERE sent=0 and caption not like '.%' and caption not like '/%'").fetchall())
            if remaining > 0:
                text = '{} remaining'.format(remaining)
            else:
                text = '0 remaining'
            bot.send_message(chat_id=update.message.chat_id, text=text, parse_mode='HTML')
            logging.info("remain by {}".format(update.message.from_user))
        except Exception as E:
            logging.error("Could't get remaining time by {}".format(update.message.from_user))

    # endregion

    def add_member(self):
        try:
            cu = self.current_time()
            mem = [self.robot.get_chat_members_count(self.channel_name)]
            try:
                last = db_connect.execute("SELECT members FROM Mem_count ORDER BY ID DESC LIMIT 1").fetchone()
            except IndexError:
                last = mem[0]
            last = last if last else mem
            cursor.execute("INSERT INTO Mem_count(ddd, balance, members) VALUES(?,?,?)",
                           (cu[0], mem[0] - last[0], mem[0]))
            db_connect.commit()
            self.robot.send_document(document=open('bot_db.db', 'rb'), caption=' '.join(self.current_time()),
                                     chat_id=sina)
            logging.info('members{}'.format(mem[0]))
        except Exception as E:
            logging.error('add members {}'.format(E))

    def id_remove(self, entry):
        pattern = re.compile(r'(@\S+)', re.I)
        pattern1 = re.compile(r'(:\S{1,2}:)', re.I)
        pattern2 = re.compile(r'https://t\.me\S*')
        if re.search(pattern2, entry):
            link = re.findall(pattern2, entry)
            for i in link:
                entry = entry.replace(i, '')
        if re.search(pattern1, entry):
            logo = re.findall(pattern1, entry)[0]
            entry = re.sub(pattern1, '', entry)
            entry = logo + entry
        if re.search(pattern, entry):
            state = re.findall(pattern, entry)
            for state in state:
                if state.lower() not in (var.channel_name, '@mmd_bt'):
                    entry = re.sub(state, var.channel_name, entry)
            if entry.lower().strip()[len(self.channel_name) * (-2):].find(var.channel_name) == -1:
                entry = entry + '\n' + var.channel_name
            return entry
        else:
            return entry + '\n' + var.channel_name

    def image_watermark(self, photo, caption) -> str:
        try:
            pattern = re.compile(r':\S{,2}:', re.I)
            div = 5
            coor_pt = re.compile(r'\d', re.I)

            self.robot.getFile(photo).download('image/tmp.jpg')
            if re.search(pattern, caption):
                i_cor = ''.join(re.findall(pattern, caption)[0])
                coor = int(re.findall(coor_pt, i_cor)[0]) if re.findall(coor_pt, i_cor)[0] else 0
            else:
                coor = 7
            bg = Image.open('image/tmp.jpg')
            if not coor == 0:
                lg = Image.open('logo/CC.png')
                res, lg_sz = bg.size, lg.size
                if res[0] > res[1]:
                    n_def = (res[1]//div, res[1]//div)
                else:
                    n_def = (res[0]//div, res[0]//div)

                lg.thumbnail(n_def, Image.ANTIALIAS)
                lg_sz = lg.size
                dict1 = {1: (0, 0),
                         2: ((res[0] // 2) - (lg_sz[0] // 2), 0),
                         3: (res[0] - lg_sz[0], 0),
                         4: (0, (res[1] // 2 - lg_sz[1] // 2)),
                         5: (res[0] // 2 - lg_sz[0] // 2, res[1] // 2),
                         6: (res[0] - lg_sz[0], res[1] // 2 - lg_sz[1] // 2),
                         7: (0, res[1] - lg_sz[1]),
                         8: (res[0] // 2 - lg_sz[0] // 2, res[1] - lg_sz[1]),
                         9: (res[0] - lg_sz[0], res[1] - lg_sz[1])}

                if dict1.get(coor):
                    bg.paste(lg, dict1.get(coor, 'sw'), lg)
                    bg.save('image/out.jpg')
            else:
                bg.save('image/out.jpg')

            if re.search(pattern, caption):
                caption = self.id_remove(re.sub(pattern, '', caption))
            else:
                caption = self.id_remove(caption)
            return caption
        except Exception as E:
            logging.error("put {}".format(E))

    def gif_watermark(self, gif, form, caption) -> str:
        try:
            caption = str(caption)
            file = 'vid/tmp.'+form
            pattern = re.compile(r':\d:')
            find = int(re.findall(pattern, caption)[0][1:-1]) if re.search(pattern, caption) else 7
            self.robot.getFile(gif).download(file)
            clip = VideoFileClip(file, audio=False)
            w, h = clip.size

            pos = {1: ('left', 'top'), 2: ('center', 'top'), 3: ('right', 'top'),
                   4: ('left', 'center'), 5: ('center', 'center'), 6: ('right', 'center'),
                   7: ('left', 'bottom'), 8: ('center', 'bottom'), 9: ('right', 'bottom')}
            size = h//5 if w > h else w//5

            logo = ImageClip("logo/CC.png") \
                .set_duration(clip.duration) \
                .resize(width=size, height=size) \
                .set_pos(pos.get(find, 7))
            final = CompositeVideoClip([clip, logo])
            final.write_videofile(filename='vid/out.mp4', progress_bar=False, verbose=False)
            if re.search(pattern, caption):
                caption = self.id_remove(re.sub(pattern, '', caption))
            else:
                caption = self.id_remove(caption)
            return caption
        except Exception as E:
            logging.error('vid_watermark {}'.format(E))

    def save(self, bot, update):
        try:
            um = update.message
            ue = update.edited_message
            kind = name = text = file_id = 'none'
            url = None
            if ue:
                gp_id = ue.message_id
                out = [cursor.execute("SELECT * FROM Queue WHERE gp = {0}".format(gp_id)).fetchall()][0][0]
                if ue.text and out[9] == 1:
                    text = self.id_remove(ue.text)
                    bot.edit_message_text(chat_id=self.channel_name, message_id=out[6], text=text)
                elif ue.caption and out[9] == 1:
                    text = self.id_remove(ue.caption)
                    bot.edit_message_caption(chat_id=self.channel_name, message_id=out[6], caption=text)
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
                if len(um.entities) > 0:
                    entities = um.entities
                    url = ''.join([entities[i].url if entities[i].url else '' for i in range(len(entities))])
                if um.text:
                    text = um.text + '\n<a href="{}">​​​​​​​​​​​</a>'.format(url) if url else um.text
                    kind = 'text'
                    url = 'url' if url else ''
                    insert(kind=kind, from_ad=from_ad, file_id=file_id, caption=text,
                           gp=gp_id, in_date=in_date, other=url)
                else:
                    text = um.caption if um.caption else ''
                    other = None
                    if um.photo:
                        kind = 'photo'
                        file_id = um.photo[-1].file_id
                    elif um.video:
                        kind = 'video'
                        file_id = um.video.file_id
                    elif um.document:
                        kind = 'document'
                        if um.document.mime_type in ('video/mp4', 'image/gif') and um.document.file_size / 1000000 < 10:
                            kind = 'vid'
                            other = str(um.document.mime_type).split('/')[1]
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
                    if kind in ('photo', 'video', 'document', 'vid', 'voice', 'audio', 'v_note'):
                        insert(kind=kind, from_ad=from_ad, file_id=file_id,
                               caption=text, gp=gp_id, in_date=in_date, other=other)

        except Exception as E:
            logging.error('save {}'.format(E))

    def send_to_ch(self):
        out = [i for i in cursor.execute("""
        SELECT * FROM Queue WHERE sent=0 AND 
        caption NOT LIKE '.%' AND 
        caption NOT LIKE '/%' 
        ORDER BY ID LIMIT 1""")][0]
        ch = None
        try:
            cp = self.id_remove(out[4])
            if out[7] == 1 and out[8] == 0 and out[9] == 1:
                if out[2] == 'text':
                    self.robot.edit_message_text(chat_id=self.channel_name, text=cp, message_id=out[5])
                    cursor.execute("UPDATE Queue SET sent=1 WHERE ID = {0}".format(out[0]))
                    db_connect.commit()
                else:
                    self.robot.edit_message_caption(chat_id=self.channel_name, caption=cp, message_id=out[5])
                    cursor.execute("UPDATE Queue SET sent=1 WHERE ID = {0}".format(out[0]))
                    db_connect.commit()
                logging.info('edit_msg msg_ID_in_db {}'.format(out[0]))
            elif out[8] == 0 or out[9] == 0:
                if out[2] == 'text':
                    if out[-1] == 'url':
                        ch = self.robot.send_message(chat_id=self.channel_name, text=cp, parse_mode='HTML').message_id
                    else:
                        ch = self.robot.send_message(chat_id=self.channel_name, text=cp).message_id
                elif out[2] == 'video':
                    # TODO set logo on videos
                    # form = out[12]
                    # cp = self.gif_watermark(vid=out[3], form=form, caption=out[4])
                    ch = self.robot.send_video(chat_id=self.channel_name, video=out[3], caption=cp).message_id
                elif out[2] == 'photo':
                    cp = self.image_watermark(out[3], out[4])
                    ch = self.robot.send_photo(chat_id=self.channel_name, photo=open('image/out.jpg', 'rb'),
                                               caption=cp).message_id
                    os.remove('./image/out.jpg')
                elif out[2] == 'audio':
                    ch = self.robot.send_audio(chat_id=self.channel_name, audio=out[3], caption=cp).message_id
                elif out[2] == 'document':
                    ch = self.robot.send_document(chat_id=self.channel_name, document=out[3], caption=cp).message_id
                elif out[2] == 'v_note':
                    ch = self.robot.send_video_note(chat_id=self.channel_name, video_note=out[3]).message_id
                elif out[2] == 'voice':
                    ch = self.robot.send_voice(chat_id=self.channel_name, voice=out[3], caption=cp).message_id
                elif out[2] == 'vid':
                    form = out[12]
                    cp = self.gif_watermark(gif=out[3], form=form, caption=out[4])
                    ch = self.robot.send_document(chat_id=self.channel_name, document=open('vid/out.mp4', 'rb'),
                                                  caption=cp).message_id
                    os.remove('./vid/out.mp4')
                logging.info('send_to_ch msg_ID_in_db {}'.format(out[0]))
        except IndexError:
            pass
        except Exception as E:
            logging.error('send_to_ch msg_num {}'.format(E))
        finally:
            db_set(ch=ch, i_d=out[0], out_date=' '.join(self.current_time()))

    def sleep(self, entry=None):
        entry = int(self.current_time()[1]) if not entry else int(entry)
        if entry >= self.bed_time > self.wake_time < entry or entry >= self.bed_time < self.wake_time > entry:
            return True
        return False

    def task(self, bot, job):
        try:
            t1 = self.current_time()[1]

            if int(t1[:-2]) == 0:
                self.add_member()

            if int(t1[:-2]) in self.delay and not self.sleep():
                self.send_to_ch()

        except Exception as E:
            logging.error('Task {}'.format(E))

    def start(self):
        dpa = self.updater.dispatcher.add_handler
        job = self.updater.job_queue
        self.updater.start_polling()
        print('started')

        dpa(CommandHandler('remain', self.remain, Filters.user(admins)))
        dpa(CommandHandler('member', self.report_members, Filters.user(admins), pass_args=True))
        dpa(CommandHandler('admin', self.report_admins, Filters.user(admins), pass_args=True))
        dpa(CommandHandler('state', self.state, Filters.user(admins)))
        # dpa(CommandHandler('delay', self.set_delay, Filters.user(admins), pass_args=True))
        dpa(CommandHandler('bed', self.set_bed, Filters.user(admins), pass_args=True))
        dpa(CommandHandler('wake', self.set_wake, Filters.user(admins), pass_args=True))
        dpa(MessageHandler(Filters.chat(self.group_id), self.save, edited_updates=True))
        job.run_repeating(callback=self.task, interval=timedelta(minutes=1), first=0)
        self.updater.idle()


timer = SSP(var.TOKEN)
timer.start()
