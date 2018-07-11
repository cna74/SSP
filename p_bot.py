from telegram.ext import Updater, MessageHandler, CommandHandler, ConversationHandler, CallbackQueryHandler, Filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton as Inline
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
from khayyam import JalaliDatetime
from datetime import datetime
from pprint import pprint
from database import *
from PIL import Image
import telegram
import logging
import pytz
import time
import var
import re
import os

# sina, lili, fery = 103086461, 303962908, 319801025
admins = var.admins
sina = var.sina
pouriya = var.pouriya
logging.basicConfig(filename='report.log', level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s')


class SSP:
    def __init__(self, token):
        self.robot = telegram.Bot(token)
        self.updater = Updater(token)
        self.channel_name = var.channel_name
        self.group_id = var.group_id
        self.chat_group = var.chat_group

        # True means lock
        self.group = False
        self.sticker = False
        self.photo = False
        self.video = False
        self.document = False

    # region general
    @staticmethod
    def current_time():
        utc = pytz.utc
        u = time.gmtime()
        utc_dt = datetime(u[0], u[1], u[2], u[3], u[4], u[5], tzinfo=utc)
        eastern = pytz.timezone('Asia/Tehran')
        loc_dt = utc_dt.astimezone(eastern)
        return JalaliDatetime().now().strftime('%Y-%m-%d'), loc_dt.strftime('%H%M%S')

    def help(self, _, update):
        try:
            self.robot.send_message(chat_id=update.message.chat_id,
                                    text='/group <on-off>\n'
                                         '/sticker <on-off>\n'
                                         '/photo <on-off>\n'
                                         '/video <on-off>\n'
                                         '/doc <on-off>')
        except Exception as E:
            logging.error('help {}'.format(E))

    def state(self, _, update):
        try:
            j = ['on' if i is self.check_switch(i) else 'off' for i in
                 (self.group, self.sticker, self.photo, self.video, self.document)]
            self.robot.send_message(chat_id=update.message.chat_id,
                                    text='group **{}**\nsticker **{}**\nphoto **{}**\nvideo **{}**\ndoc **{}**'.format(
                                        *j),
                                    parse_mode=telegram.ParseMode.MARKDOWN)
        except Exception as E:
            logging.error('state {}'.format(E))

    def send_db(self, _, update, args):
        try:
            if args:
                self.send_student(n=args[0])
                logging.info('send_db {} {}'.format(update.message.from_user.id, update.message.from_user.first_name))
            else:
                self.send_student(n=10)
                self.robot.send_document(chat_id=sina, document=open('./bot_db.db', 'rb'), caption='database')
                logging.info('send_db {} {}'.format(update.message.from_user.id, update.message.from_user.first_name))
        except Exception as E:
            logging.error('send_db {}'.format(E))

    def welcome(self, _, update):
        try:
            self.robot.send_message(chat_id=update.message.chat_id,
                                    text='''
                                    🎖داوطلبِ گرامی سلاااام☺️ ، به رباتِ " ثبتِ نام " طرحِ تابستانه VOB خوش آمدید⚔️
ابتدا گزینه👈  reg/  را بزنید!                                    
                                    ''',
                                    reply_to_message_id=update.message.message_id,
                                    parse_mode=telegram.ParseMode.MARKDOWN)
        except Exception as E:
            logging.error('welcome {}'.format(E))

    def remain(self, _, update):
        try:
            remaining = len(db_connect.execute(
                "SELECT ID FROM Queue WHERE sent=0 and caption not like '.%' and caption not like '/%'").fetchall())
            rem = remaining

            if rem > 0:
                text = '{} remaining'.format(rem)
            else:
                text = '0 remaining'
            self.robot.send_message(chat_id=update.message.chat_id, text=text)
            logging.info("remain by {}".format(update.message.from_user))
        except Exception as E:
            logging.error("remain: {} {}".format(E, update.message.from_user))

    # endregion

    # region channel_part
    @staticmethod
    def id_remove(entry):
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
                if state.lower() not in (var.channel_name,):
                    entry = re.sub(state, var.channel_name, entry)
            return entry
        else:
            return entry

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
                    n_def = (res[1] // div, res[1] // div)
                else:
                    n_def = (res[0] // div, res[0] // div)

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
            file = 'vid/tmp.' + form
            pattern = re.compile(r':\d:')
            find = int(re.findall(pattern, caption)[0][1:-1]) if re.search(pattern, caption) else 7
            self.robot.getFile(gif).download(file)
            clip = VideoFileClip(file, audio=False)
            w, h = clip.size

            pos = {1: ('left', 'top'), 2: ('center', 'top'), 3: ('right', 'top'),
                   4: ('left', 'center'), 5: ('center', 'center'), 6: ('right', 'center'),
                   7: ('left', 'bottom'), 8: ('center', 'bottom'), 9: ('right', 'bottom')}
            size = h // 5 if w > h else w // 5

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
            logging.info('save')
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

    def task(self, _, __):
        try:
            self.send_to_ch()
            self.robot.send_document(chat_id=admins[0], document='./bot_db.db', caption='database')
        except Exception as E:
            logging.error('Task {}'.format(E))

    # endregion

    # region group
    def check_switch(self, switch, entry=None) -> bool:
        entry = int(self.current_time()[1][:-4]) if not entry else int(entry)
        if isinstance(switch, tuple):
            if entry >= switch[0] > switch[1] < entry or entry >= switch[0] < switch[1] > entry:
                return True
            return False
        elif isinstance(switch, bool):
            return True if switch else False

    def manage(self, _, update):
        try:
            if update.message.text:
                text = update.message.text if update.message.text else ''
            else:
                text = update.message.caption if update.message.caption else ''

            user_id = update.message.from_user.id
            link = re.compile(r'(((http(s)?):/+(www\.)?\w+\.\w+)|((www\.)?\w+\.\w+)|(http(s)?))', re.IGNORECASE)
            joined = is_admin = None

            try:
                if self.robot.get_chat_member(self.channel_name, user_id):
                    joined = True
            except Exception:
                joined = False

            group_admins = [i.user.id for i in self.robot.get_chat_administrators(self.group_id)]
            if user_id not in group_admins:
                if self.check_switch(self.group) or len(re.findall(link, text)) > 0 or not joined:
                    self.robot.delete_message(self.chat_group, update.message.message_id)

                elif update.message.photo and not self.check_switch(self.photo):
                    self.robot.delete_message(self.chat_group, update.message.message_id)
                elif (update.message.video or update.message.video_note) and not self.check_switch(self.video):
                    self.robot.delete_message(self.chat_group, update.message.message_id)
                elif update.message.sticker and not self.check_switch(self.sticker):
                    self.robot.delete_message(self.chat_group, update.message.message_id)
                elif update.message.document and not self.check_switch(self.document):
                    self.robot.delete_message(self.chat_group, update.message.message_id)

            # new member
            if len(update.message.new_chat_members) > 0:
                new_member = update.message.new_chat_members[0]
                self.robot.send_message(chat_id=update.message.chat_id,
                                        text='سلام {} خوش آمدید برای استفاده'
                                             ' از گروه ابتدا در کانال @VOB10 عضو شوید'.format(new_member.first_name),
                                        reply_to_message_id=update.message.message_id,
                                        reply_markup=InlineKeyboardMarkup(
                                            [[Inline('VOB10', url='https://t.me/{}'.format(self.channel_name[1:]))]]),
                                        one_time_keyboard=True, resize_keyboard=True)
        except Exception as E:
            logging.error('manage {}'.format(E))

    def toggle(self, key, b):
        if isinstance(b, tuple):
            b = (int(b[0]), int(b[1]))

        if key == 'group':
            self.group = b
        elif key == 'sticker':
            self.sticker = b
        elif key == 'photo':
            self.photo = b
        elif key == 'video':
            self.video = b
        elif key == 'doc':
            self.document = b

    def turn(self, _, update, args):
        try:
            key = update.message.text.split()[0][1:]
            entry = ' '.join(args).strip()
            switch = ('group', 'sticker', 'photo', 'video', 'doc')
            key = key if key in switch else False
            if key:
                if entry == 'on':
                    self.toggle(key, b=True)
                    self.robot.send_message(chat_id=update.message.chat_id,
                                            text='{} **unlocked**'.format(key),
                                            reply_to_message_id=update.message.message_id,
                                            parse_mode=telegram.ParseMode.MARKDOWN)
                elif re.fullmatch(r'\d{,2}\s\d{,2}', entry):
                    from_, until = entry.split()
                    self.toggle(key, (from_, until))
                    self.robot.send_message(chat_id=update.message.chat_id,
                                            text='{} **locked up** from {} until {}'.format(key, from_, until),
                                            reply_to_message_id=update.message.message_id,
                                            parse_mode=telegram.ParseMode.MARKDOWN)
                elif entry == 'off':
                    self.toggle(key, b=False)
                    self.robot.send_message(chat_id=update.message.chat_id,
                                            text='{} **locked up**'.format(key),
                                            reply_to_message_id=update.message.message_id,
                                            parse_mode=telegram.ParseMode.MARKDOWN)
                else:
                    self.robot.send_message(chat_id=update.message.chat_id,
                                            text='Error **{}**\n**on** or **off**'.format(entry),
                                            reply_to_message_id=update.message.message_id,
                                            parse_mode=telegram.ParseMode.MARKDOWN)

            logging.info('turn {} {}'.format(update.message.from_user, entry))
        except Exception as E:
            logging.error('turn user:{} args:{} E:{}'.format(update.message.from_user, args, E))

    # endregion

    # region contact
    def send_student(self, n: int = None, user_id=None):
        try:
            if n:
                stds = cursor.execute("SELECT name,number,grade FROM Student ORDER BY ID DESC LIMIT ?", (n,)).fetchall()
                stds = '\n'.join(['🤓{} 📲{} 📚{}'.format(i[0], i[1], i[2]) for i in stds])
                self.robot.send_message(pouriya, str(stds))
            elif user_id:
                std = cursor.execute("SELECT * FROM Student WHERE user_id = ?", (user_id,)).fetchone()
                self.robot.send_message(pouriya, str(std[2:]))
        except Exception as E:
            logging.error('send student {}'.format(E))

    def register(self, _, update):
        try:
            um = update.message
            user_id = um.from_user.id
            chat_id = um.chat_id
            message_id = um.message_id
            user = cursor.execute("SELECT * FROM Student WHERE user_id = {0}".format(user_id, )).fetchone()
            if user is None:
                self.robot.send_message(chat_id=chat_id,
                                        text='''
                                        🎓 خب عزیزم حالا " نام_نام خانوادگی" خودت رو وارد کن!✍️
                                        ''',
                                        reply_to_message_id=message_id, )
                return self.get_name
            else:
                name, number, grade = user[2], user[3], user[4]
                self.robot.send_message(chat_id=chat_id,
                                        text='شما با نام {} و شماره {} در مقطع {} در لیست ما حضور دارید\n'
                                             'آیا مایلید اطلاعات خود را تغییر دهید؟'.format(name, number, grade),
                                        reply_to_message_id=message_id,
                                        reply_markup=InlineKeyboardMarkup(
                                            [[Inline('نام', callback_data='name'),
                                              Inline('شماره', callback_data='number'),
                                              Inline('مقطع', callback_data='grade')],
                                             [Inline('OK', callback_data='ok')]]))
                return self.edit_or_name_or_number_or_grade
        except Exception as E:
            logging.error('register {}'.format(E))

    def get_name(self, _, update):
        try:
            name = chat_id = message_id = user_id = None
            if update.callback_query:
                um = update.callback_query
                user_id = um.from_user.id
                chat_id = um.message.chat_id
                message_id = um.message.message_id
            else:
                um = update.message
                chat_id = um.chat_id
                user_id = um.from_user.id
                message_id = um.message_id
                name = '{}'.format(um.text)
            cursor.execute("INSERT INTO Student(user_id, name) VALUES(?,?)", (user_id, name))
            db_connect.commit()
            self.robot.send_message(chat_id=chat_id,
                                    text="""
                                    🎖بسیار عالی ، "سالِ چندم_چه رشته ای" هستی ؟؟👊
                                    """,
                                    reply_to_message_id=message_id,
                                    reply_markup=InlineKeyboardMarkup(
                                        [[Inline('📚دهم تجربی', callback_data='10'),
                                          Inline('📚یازدهم تجربی', callback_data='11'),
                                          Inline('📚دوازدهم تجربی', callback_data='12')],
                                         [Inline('📚فارغ التحصیل', callback_data='20')]]
                                    ))
            return self.get_grade
        except Exception as E:
            logging.error('get_name {}'.format(E))

    def get_grade(self, _, update):
        try:
            if update.callback_query:
                um = update.callback_query
                user_id = um.from_user.id
                chat_id = um.message.chat_id
                message_id = um.message.message_id
                grade = um.data
                db_connect.execute("UPDATE Student SET grade=? WHERE user_id = ?", (grade, user_id))
                db_connect.commit()
                self.robot.edit_message_text(chat_id=chat_id,
                                             text="""
                                        🎖 حالا "شماره موبایلِ 📱خودت (یا والدین ) "رو
                                          جهتِ تماسِ مشاورین و کارشناسانِ ما ✍️بنویس⚔️
                                        """,
                                             message_id=message_id)
                return self.get_number_and_finish
        except Exception as E:
            logging.error('get_grade {}'.format(E))

    def get_number_and_finish(self, _, update):
        try:
            phone_number = message_id = chat_id = None
            if update.message:
                um = update.message
                user_id = um.from_user.id
                chat_id = um.chat_id
                message_id = um.message_id
                phone_number = um.text if um.text else um.contact.phone_number
                name = cursor.execute("SELECT name FROM Student WHERE user_id = {0}".format(user_id)).fetchone()[0]
                if not re.fullmatch(r'(^(989|09)\d{9}$)', phone_number):
                    self.robot.send_message(chat_id=chat_id,
                                            text='شماره وارد شده صحیح نیست دقت کنید که شماره با حروف لاتین 09 آغاز شود',
                                            reply_to_message_id=message_id)
                    return self.get_number_and_finish
                elif um.text or um.contact:
                    phone_number = '0' + str(phone_number)[2:] if str(phone_number).startswith('98') else phone_number
                    db_connect.execute("UPDATE Student SET number=? WHERE user_id = ?", (phone_number, user_id))
                    db_connect.commit()
                    self.robot.send_message(chat_id=chat_id,
                                            text="""🎖بسیار عالی ، اطلاعاتِ شما با موفقیت ثبت شد✅ ، کارشناسان 👨‍⚕و مشاورین👩‍⚕ به زودی با شما تماس خواهند گرفت🤙\n
اگر همه موارد رو درست پر کردید تایید رو انتخاب کن اگر میخوای چیزیو تغییر بدی یکی از موارد پایین رو انتخاب کن
                                            """,
                                            reply_to_message_id=message_id,
                                            reply_markup=InlineKeyboardMarkup([[Inline('تایید', callback_data='ok')],
                                                                               [Inline('نام',
                                                                                       callback_data='name'),
                                                                                Inline('شماره',
                                                                                       callback_data='number'),
                                                                                Inline('مقطع',
                                                                                       callback_data='grade')]]))

                    return self.edit_or_name_or_number_or_grade
        except Exception as E:
            logging.error('get_number_and_finish {}'.format(E))

    def edit_or_name_or_number_or_grade(self, _, update):
        try:
            if update.callback_query:
                um = update.callback_query
                chat_id = um.message.chat_id
                message_id = um.message.message_id
                user_id = um.from_user.id
                name, phone_number, grade = cursor.execute(
                    "SELECT name, number, grade FROM Student WHERE user_id = {0}".format(user_id)).fetchone()
                if um.data == 'name':
                    self.robot.edit_message_text(chat_id=chat_id,
                                                 message_id=message_id,
                                                 text='نام جدید را وارد کنید',
                                                 reply_markup=InlineKeyboardMarkup(
                                                     [[Inline('بی خیال', callback_data='cancel')]]))
                    return self.edit_name
                elif um.data == 'number':
                    self.robot.edit_message_text(chat_id=chat_id,
                                                 message_id=message_id,
                                                 text='شماره جدید را وارد کنید',
                                                 reply_markup=InlineKeyboardMarkup(
                                                     [[Inline('بی خیال', callback_data='cancel')]]))
                    return self.edit_number
                elif um.data == 'grade':
                    self.robot.edit_message_text(chat_id=chat_id,
                                                 message_id=message_id,
                                                 text='سال چندم چه رشته ای هستی؟',
                                                 reply_markup=InlineKeyboardMarkup(
                                                     [[Inline('📚دهم تجربی', callback_data='10'),
                                                       Inline('📚یازدهم تجربی', callback_data='11'),
                                                       Inline('📚دوازدهم تجربی', callback_data='12')],
                                                      [Inline('📚فارغ التحصیل', callback_data='20')],
                                                      [Inline('بی خیال', callback_data='cancel')]]))
                    return self.edit_grade
                elif um.data == 'ok':
                    self.robot.edit_message_text(text='تمام\n'
                                                      'نام: {}\n'
                                                      'شماره: {}\n'
                                                      'مقطع: {}\n'.format(name, phone_number, grade),
                                                 chat_id=chat_id,
                                                 message_id=message_id)
                    self.send_student(user_id=user_id)
                    return ConversationHandler.END
                elif um.data == 'edit':
                    self.robot.send_message(chat_id=chat_id,
                                            text='کدام:\n'
                                                 'نام: {}\n'
                                                 'شماره: {}\n'
                                                 'مقطع: {}\n'.format(name, phone_number, grade),
                                            reply_to_message_id=message_id,
                                            reply_markup=InlineKeyboardMarkup([[Inline('نام',
                                                                                       callback_data='name')],
                                                                               [Inline('شماره',
                                                                                       callback_data='number'),
                                                                                Inline('مقطع',
                                                                                       callback_data='grade')]]))
                    return self.edit_or_name_or_number_or_grade
        except Exception as E:
            logging.error('edit_or_name_or_number_or_grade {}'.format(E))

    def edit_name(self, _, update):
        try:
            if update.message:
                um = update.message
                name = um.text
                chat_id = um.chat_id
                message_id = um.message_id
                user_id = um.from_user.id
                db_connect.execute("UPDATE Student SET name=? WHERE user_id = ?", (name, user_id))
                db_connect.commit()
                self.robot.send_message(text='نام: {}\n'
                                             'تغییر دیگری در سر دارید؟'.format(name),
                                        chat_id=chat_id,
                                        reply_to_message_id=message_id,
                                        reply_markup=InlineKeyboardMarkup(
                                            [[Inline('نام', callback_data='name'),
                                              Inline('شماره', callback_data='number'),
                                              Inline('OK', callback_data='ok')]]))
                return self.edit_or_name_or_number_or_grade
            elif update.callback_query:
                um = update.callback_query
                chat_id = um.message.chat_id
                message_id = um.message.message_id
                if um.data == 'cancel':
                    self.robot.send_message(chat_id=chat_id,
                                            text='لغو عملیات',
                                            reply_to_message_id=message_id)
                    return ConversationHandler.END
        except Exception as E:
            logging.error('edit_name {}'.format(E))

    def edit_grade(self, _, update):
        try:
            if update.callback_query:
                um = update.callback_query
                chat_id = um.message.chat_id
                message_id = um.message.message_id
                user_id = um.from_user.id

                if not um.data == 'cancel':
                    grade = um.data
                    db_connect.execute("UPDATE Student SET grade=? WHERE user_id = ?", (grade, user_id))
                    db_connect.commit()
                    self.robot.send_message(text='مقطع: {}\n'
                                                 'تغییر دیگری در سر دارید؟'.format(grade),
                                            chat_id=chat_id,
                                            reply_to_message_id=message_id,
                                            reply_markup=InlineKeyboardMarkup(
                                                [[Inline('نام', callback_data='name'),
                                                  Inline('شماره', callback_data='number'),
                                                  Inline('مقطع', callback_data='grade')],
                                                 [Inline('خیر', callback_data='ok')]]))
                    return self.edit_or_name_or_number_or_grade

                elif um.data == 'cancel':
                    self.robot.send_message(chat_id=chat_id,
                                            text='لغو عملیات',
                                            reply_to_message_id=message_id)
                    return ConversationHandler.END
        except Exception as E:
            logging.error('edit_grade {}'.format(E))

    def edit_number(self, _, update):
        try:
            if update.message:
                um = update.message
                chat_id = um.chat_id
                message_id = um.message_id
                user_id = um.from_user.id
                phone_number = um.text if um.text else um.contact.phone_number
                phone_number = '0' + str(phone_number)[2:] if str(phone_number).startswith('98') else phone_number
                if not re.fullmatch(r'(^(989|09)\d{9}$)', phone_number):
                    self.robot.send_message(chat_id=chat_id,
                                            text='شماره وارد شده صحیح نیست دقت کنید که شماره با حروف لاتین 09 آغاز شود',
                                            reply_to_message_id=message_id)
                    return self.edit_number
                db_connect.execute("UPDATE Student SET number=? WHERE user_id = ?", (phone_number, user_id))
                db_connect.commit()
                self.robot.send_message(text='شماره: {}\n'
                                             'تغییر دیگری در سر دارید؟'.format(phone_number),
                                        chat_id=chat_id,
                                        reply_markup=InlineKeyboardMarkup(
                                            [[Inline('نام', callback_data='name'),
                                              Inline('شماره', callback_data='number'),
                                              Inline('OK', callback_data='ok')]]))
                return self.edit_or_name_or_number_or_grade
            elif update.callback_query:
                um = update.callback_query
                chat_id = um.message.chat_id
                message_id = um.message.message_id
                if um.data == 'cancel':
                    self.robot.send_message(chat_id=chat_id,
                                            text='لغو عملیات',
                                            reply_to_message_id=message_id)
                    return ConversationHandler.END
        except Exception as E:
            logging.error('edit_number {}'.format(E))

    def cancel(self, _, update):
        try:
            um = update.message
            chat_id = um.chat_id
            message_id = um.message_id
            self.robot.send_message(chat_id=chat_id,
                                    text='لغو عملیات',
                                    reply_to_message_id=message_id)
            return ConversationHandler.END
        except Exception as E:
            logging.error('cancel {}'.format(E))

    # endregion

    def start(self):
        dpa = self.updater.dispatcher.add_handler
        job = self.updater.job_queue
        self.updater.start_polling()
        print('started')

        dpa(CommandHandler('start', callback=self.welcome, filters=Filters.private))

        dpa(CommandHandler('db', callback=self.send_db, filters=Filters.user(admins), pass_args=True))
        dpa(CommandHandler('remain', callback=self.remain, filters=Filters.user(admins)))

        # channel
        dpa(CommandHandler(command='help', callback=self.help, filters=Filters.user(admins)))
        dpa(CommandHandler(command=['group', 'sticker', 'photo', 'video', 'doc'],
                           callback=self.turn, filters=Filters.user(admins), pass_args=True))

        dpa(MessageHandler(Filters.chat(self.group_id), self.save, edited_updates=True))

        # group
        dpa(MessageHandler(Filters.chat(self.chat_group), self.manage))

        # contact
        dpa(ConversationHandler(entry_points=[CommandHandler(command='reg',
                                                             callback=self.register,
                                                             filters=Filters.private)],
                                states={
                                    self.get_name: [CallbackQueryHandler(self.get_name, ),
                                                    MessageHandler(Filters.text, self.get_name)],

                                    self.get_grade: [CallbackQueryHandler(self.get_grade, ),
                                                     CommandHandler(['10', '11', '12', '20'], self.get_grade)],

                                    self.get_number_and_finish: [CallbackQueryHandler(self.get_number_and_finish),
                                                                 MessageHandler(Filters.contact,
                                                                                self.get_number_and_finish),
                                                                 MessageHandler(Filters.text,
                                                                                self.get_number_and_finish)],

                                    self.edit_or_name_or_number_or_grade: [
                                        CallbackQueryHandler(self.edit_or_name_or_number_or_grade),
                                        CommandHandler(['name', 'number', 'grade', 'edit', 'ok'],
                                                       callback=self.edit_or_name_or_number_or_grade)],

                                    self.edit_name: [CallbackQueryHandler(self.edit_name),
                                                     MessageHandler(Filters.text, callback=self.edit_name)],

                                    self.edit_number: [CallbackQueryHandler(self.edit_number),
                                                       MessageHandler(Filters.text, callback=self.edit_number)],

                                    self.edit_grade: [CallbackQueryHandler(self.edit_grade),
                                                      MessageHandler(Filters.text, callback=self.edit_grade)],
                                },
                                fallbacks=[CallbackQueryHandler(self.cancel),
                                           CommandHandler('cancel', self.cancel)]))

        job.run_daily(callback=self.task, time=datetime.time(datetime.strptime('06:00', '%H:%M')))

        self.updater.idle()


vob = SSP(var.TOKEN)
vob.start()
