from telegram.ext import Updater, MessageHandler, CommandHandler, Filters, PicklePersistence
from khayyam3.tehran_timezone import timedelta, JalaliDatetime
from utils import editor, strings, db, util
from datetime import time
import telegram
import logging
import psutil
import conv
import var
import os

cna, rhn = 103086461, 303962908
limit_size = 1
time_out = 60
persistence = PicklePersistence("file")
logging.basicConfig(filename='report.log', level=logging.INFO,
                    format='%(asctime)s: %(levelname)s: %(message)s')


# noinspection PyBroadException
class SSP:
    def __init__(self, token):
        self.updater = Updater(token, use_context=True, persistence=persistence)
        # self.robot = telegram.Bot(token)
        # self.updater = Updater(token)
        try:
            for folder in ['vid', 'plot', 'logo', 'image', 'gif']:
                dir_ = os.path.join(os.getcwd(), folder)
                if not os.path.exists(dir_):
                    os.makedirs(dir_)
        except Exception as _:
            pass

    def save(self, update, content):
        try:
            um = update.message
            ue = update.edited_message
            message = None
            # edited
            if ue:
                from_gp = ue.chat_id
                msg_gp_id = ue.message_id
                # channel = db.find('channel', group_id=from_gp)
                message = db.find('message', msg_gp_id=msg_gp_id, gp_id=from_gp)
                if isinstance(message, db.Message):
                    if ue.reply_to_message:
                        if ue.text:
                            message = db.find("message",
                                              msg_gp_id=ue.reply_to_message.message_id,
                                              gp_id=ue.chat_id)
                            if isinstance(message, db.Message):
                                if message.other.isnumeric():
                                    message = db.find("message", media=message.other)
                                    for msg in message:
                                        msg.txt = ue.text
                                        db.update(msg)
                                else:
                                    message.txt = ue.text
                                    db.update(message)

                    # # after sent
                    # elif ue.text and message.sent:
                    #     message.txt = editor.id_remove(text=ue.text, channel=channel)
                    #     if len(um.entities) > 0:
                    #         entities = um.entities
                    #         url = ''.join([entities[i].url if entities[i].url else '' for i in range(len(entities))])
                    #         message.txt += '\n<a href="{}">​​​​​​​​​​​</a>'.format(url)
                    #         message.other = 'url'
                    #     parse_mode = 'HTML' if message.other == 'url' else None
                    #     self.robot.edit_message_text(chat_id=message.to_channel, message_id=message.msg_ch_id,
                    #                                  text=message.txt, parse_mode=parse_mode)
                    #     message.sent = message.ch_a = True
                    # elif message.sent:
                    #     media = out = None
                    #     text = ue.caption if ue.caption else ' '
                    #     text = editor.id_remove(text=text, channel=channel)
                    #
                    #     if ue.photo:
                    #         media = ue.photo[-1].file_id
                    #         dir_ = "image/{}.jpg".format(channel.name)
                    #         out = 'image/{}_out.jpg'.format(channel.name)
                    #         self.robot.getFile(media).download(dir_)
                    #
                    #         message.kind = "photo"
                    #         if channel.plan >= 1:
                    #             text = editor.image_watermark(photo=dir_, out=out, caption=text, channel=channel)
                    #             media = telegram.InputMediaPhoto(media=open(out, 'rb'), caption=text)
                    #         else:
                    #             text = editor.id_remove(text=text, channel=channel)
                    #             media = telegram.InputMediaPhoto(media=media, caption=text)
                    #
                    #     elif ue.animation:
                    #         media = ue.animation.file_id
                    #         mime = str(um.animation.mime_type).split('/')[1]
                    #         dir_ = "gif/{}.{}".format(channel.name, mime)
                    #         out = "gif/{}_out.mp4".format(channel.name)
                    #         size = ue.video.file_size / (1024 ** 2)
                    #
                    #         message.mime = mime
                    #         message.kind = 'animation'
                    #
                    #         if size <= limit_size and channel.plan >= 2:
                    #             self.robot.getFile(media).download(dir_)
                    #             text = editor.vid_watermark(vid=dir_, out=out, kind=message.kind,
                    #                                         caption=text, channel=channel)
                    #             media = telegram.InputMediaVideo(media=open(out, 'rb'), caption=text)
                    #         else:
                    #             text = editor.id_remove(text=text, channel=channel)
                    #             media = telegram.InputMediaAnimation(media=media, caption=text)
                    #
                    #     elif ue.video:
                    #         media = ue.video.file_id
                    #         mime = str(um.video.mime_type).split('/')[1]
                    #         dir_ = "vid/{}.{}".format(channel.name, mime)
                    #         out = 'vid/{}_out.mp4'.format(channel.name)
                    #         size = ue.video.file_size / (1024 ** 2)
                    #
                    #         message.mime = mime
                    #         message.kind = 'video'
                    #
                    #         if size < limit_size and channel.plan >= 3:
                    #             self.robot.getFile(media).download(dir_)
                    #             text = editor.vid_watermark(vid=dir_, out=out, kind=message.kind,
                    #                                         caption=text, channel=channel)
                    #             media = telegram.InputMediaVideo(media=open(out, 'rb'), caption=text)
                    #         else:
                    #             text = editor.id_remove(text=text, channel=channel)
                    #             media = telegram.InputMediaVideo(media=media, caption=text)
                    #
                    #     elif ue.document:
                    #         media = ue.document.file_id
                    #         media = telegram.InputMediaDocument(media=media, caption=text)
                    #
                    #     elif ue.audio:
                    #         media = ue.audio.file_id
                    #         media = telegram.InputMediaAudio(media=media, caption=text)
                    #
                    #     if media:
                    #         self.robot.edit_message_media(media=media, chat_id=message.to_channel,
                    #                                       message_id=message.msg_ch_id, timeout=time_out)
                    #
                    #     if out:
                    #         os.remove(out)
                    #     if ue.caption:
                    #         self.robot.edit_message_caption(chat_id=message.to_channel, message_id=message.msg_ch_id,
                    #                                         caption=text)
                    #
                    #     message.sent = message.ch_a = True
                    #     message.txt = text

                    # before sent
                    elif ue.text:
                        message.txt = ue.text
                        message.sent = message.ch_a = False
                        if len(um.entities) > 0:
                            entities = um.entities
                            url = ''.join([entities[i].url if entities[i].url else '' for i in range(len(entities))])
                            message.txt += '\n<a href="{}">​​​​​​​​​​​</a>'.format(url)
                            message.other = 'url'
                    elif ue.caption:
                        message.txt = ue.caption if ue.caption else " "
                        message.sent = message.ch_a = False
                        if ue.photo:
                            message.kind = 'photo'
                            message.file_id = ue.photo[-1].file_id
                        elif ue.video:
                            message.kind = 'video'
                            message.file_id = ue.video.file_id
                        elif ue.animation:
                            message.kind = 'animation'
                            message.file_id = ue.animation.file_id
                        elif ue.document:
                            message.kind = 'document'
                            message.file_id = ue.document.file_id
                        elif ue.audio:
                            message.kind = 'audio'
                            message.file_id = ue.audio.file_id
                    db.update(message)

            # regular
            elif um:
                channel = db.find(table="channel", group_id=um.chat_id)
                if um.reply_to_message:
                    if um.text:
                        message = db.find("message",
                                          msg_gp_id=um.reply_to_message.message_id,
                                          gp_id=um.chat_id)
                        if message.other.isnumeric():
                            message = db.find("message", media=message.other)
                            for msg in message:
                                msg.txt = um.text
                                db.update(msg)
                        else:
                            message.txt = um.text
                            db.update(message)

                elif um.text:
                    other = ""
                    txt = um.text
                    if len(um.entities) > 0:
                        entities = um.entities
                        url = ''.join([entities[i].url if entities[i].url else '' for i in range(len(entities))])
                        txt += '\n<a href="{}">​​​​​​​​​​​</a>'.format(url)
                        other = 'url'
                    message = db.Message(from_group=um.chat_id, to_channel=channel.name,
                                         kind='text', msg_gp_id=um.message_id, txt=txt, other=other)
                    db.add(message)
                else:
                    text = um.caption if um.caption else ' '
                    file_id = kind = other = mime = ''
                    size = 0
                    if um.media_group_id:
                        if um.photo:
                            kind = 'photo'
                            file_id = um.photo[-1].file_id
                        elif um.video:
                            kind = 'video'
                            file_id = um.video.file_id
                        other = um.media_group_id
                    elif um.photo:
                        kind = 'photo'
                        file_id = um.photo[-1].file_id
                    elif um.video:
                        kind = 'video'
                        size = um.video.file_size / (1024 ** 2)
                        mime = str(um.video.mime_type).split('/')[1]
                        file_id = um.video.file_id
                    elif um.animation:
                        kind = 'animation'
                        size = um.animation.file_size / (1024 ** 2)
                        mime = str(um.document.mime_type).split('/')[1]
                        file_id = um.document.file_id
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
                    elif um.sticker:
                        kind = 'sticker'
                        file_id = um.sticker.file_id

                    message = db.Message(from_group=um.chat_id, to_channel=channel.name, msg_gp_id=um.message_id,
                                         kind=kind, txt=text, file_id=file_id, size=size, mime=mime, other=other)
                    db.add(message)

            if isinstance(message, db.Message):
                logging.info("save {}".format(message.__str__()))
        except Exception as E:
            logging.error('save {}'.format(E))

    def add_member(self, channel):
        try:
            current_date = JalaliDatetime().now().to_date()
            num = self.updater.bot.get_chat_members_count(channel.name)
            member = db.Member(number=num, channel_name=channel.name, calendar=current_date)
            db.add(member)
        except Exception as E:
            logging.error('add_members {}'.format(E))

    def send_to_ch(self, channel):
        message = db.get_last_msg(channel_name=channel.name)
        dir_ = out = None
        try:
            # media_group
            if isinstance(message, list):
                chat_id = channel.name
                media = []
                new_message = []
                for msg in message:
                    txt = editor.id_remove(text=msg.txt, channel=channel)
                    if msg.kind == 'photo':
                        media.append(telegram.InputMediaPhoto(media=msg.file_id, caption=txt))
                    elif msg.kind == 'video':
                        media.append(telegram.InputMediaVideo(media=msg.file_id, caption=txt))

                    msg.sent = True
                    msg.ch_a = True
                    new_message.append(msg)

                self.updater.bot.send_media_group(chat_id=chat_id, media=media, timeout=time_out)
                for msg in new_message:
                    db.update(msg)
                logging.info('media_group sent {}'.format(message.__str__()))

            # regular
            elif not message.ch_a:
                txt = editor.id_remove(text=message.txt, channel=channel)
                parse_mode = 'HTML' if message.other == 'url' else None

                if message.kind == 'photo':
                    dir_ = "image/{}.jpg".format(channel.name)
                    out = "image/{}_out.jpg".format(channel.name)
                    if channel.plan >= 1:
                        try:
                            self.updater.bot.getFile(message.file_id).download(dir_)
                            txt = editor.image_watermark(photo=dir_, out=out, caption=message.txt, channel=channel)
                            self.updater.bot.send_photo(chat_id=message.to_channel, photo=open(out, 'rb'),
                                                        caption=txt, timeout=time_out)
                        except Exception:
                            txt = editor.id_remove(text=message.txt, channel=channel)
                            self.updater.bot.send_photo(chat_id=message.to_channel, photo=message.file_id, caption=txt)
                    else:
                        txt = editor.id_remove(message.txt, channel)
                        self.updater.bot.send_photo(chat_id=message.to_channel, photo=message.file_id, caption=txt)

                elif message.kind == 'video':
                    form = message.mime
                    dir_ = "vid/{}.{}".format(channel.name, form)
                    out = "vid/{}_out.mp4".format(channel.name)

                    if message.size <= limit_size and channel.plan >= 3:
                        self.updater.bot.getFile(message.file_id).download(dir_, timeout=20)
                        try:
                            txt = editor.vid_watermark(vid=dir_, out=out, kind=message.kind,
                                                       caption=message.txt, channel=channel)

                            self.updater.bot.send_video(chat_id=message.to_channel, video=open(out, 'rb'),
                                                        caption=txt, timeout=time_out)
                        except Exception:
                            self.updater.bot.send_video(chat_id=message.to_channel, video=message.file_id, caption=txt)
                    else:
                        txt = editor.id_remove(text=message.txt, channel=channel)
                        self.updater.bot.send_video(chat_id=message.to_channel, video=message.file_id, caption=txt)

                elif message.kind == 'animation':
                    form = message.mime
                    dir_ = "gif/{}.{}".format(channel.name, form)
                    out = "gif/{}_out.mp4".format(channel.name)

                    if message.size <= limit_size and channel.plan >= 2:
                        try:
                            self.updater.bot.getFile(message.file_id).download(dir_, timeout=20)
                            txt = editor.vid_watermark(vid=dir_, out=out, kind=message.kind,
                                                       caption=message.txt, channel=channel)

                            self.updater.bot.send_animation(chat_id=message.to_channel, animation=open(out, 'rb'),
                                                            caption=txt, timeout=time_out)
                        except Exception as _:
                            self.updater.bot.send_animation(chat_id=message.to_channel, animation=message.file_id,
                                                            caption=txt)
                    else:
                        txt = editor.id_remove(text=message.txt, channel=channel)
                        self.updater.bot.send_animation(chat_id=message.to_channel, animation=message.file_id,
                                                        caption=txt)

                elif message.kind == 'text':
                    self.updater.bot.send_message(chat_id=message.to_channel, text=txt, parse_mode=parse_mode)

                elif message.kind == 'audio':
                    self.updater.bot.send_audio(chat_id=message.to_channel, audio=message.file_id, caption=txt)

                elif message.kind == 'document':
                    self.updater.bot.send_document(chat_id=message.to_channel, document=message.file_id, caption=txt)

                elif message.kind == 'v_note':
                    self.updater.bot.send_video_note(chat_id=message.to_channel, video_note=message.file_id)

                elif message.kind == 'voice':
                    self.updater.bot.send_voice(chat_id=message.to_channel, voice=message.file_id, caption=txt)

                elif message.kind == 'sticker':
                    self.updater.bot.send_sticker(chat_id=message.to_channel, sticker=message.file_id, caption=txt)

                try:
                    if dir_ or out:
                        _ = [os.remove(i) for i in [dir_, out]]
                except Exception:
                    pass

                logging.debug('send_to_ch {}'.format(message.__str__()))
                message.sent = True
                message.ch_a = True
                db.update(message)

        except IndexError:
            pass
        except AttributeError:
            pass
        except Exception as E:
            if isinstance(message, db.Message):
                message.sent = True
                message.ch_a = True
                db.update(message)
                logging.error('send_to_ch attempt {} Error: {}'.format(message.__str__(), E))
            else:
                logging.error('send_to_ch attempt {} Error: not a message'.format(message.__str__()))

    def send_info(self, update, content):
        try:
            um = update.message
            if isinstance(um.new_chat_members, list):
                chat_member = um.new_chat_members[0]
                channel = db.find('channel', group_id=um.chat_id)

                if chat_member.id == content.bot.id:
                    if um.chat.type == 'supergroup' and isinstance(channel, db.Channel):
                        content.bot.send_message(chat_id=um.chat_id, text=strings.congrats)
                    else:
                        content.bot.send_message(chat_id=um.chat_id, text=um.chat_id)
                        content.bot.leave_chat(um.chat_id)
        except Exception as E:
            logging.error("send_info: {}".format(E))

    def admin(self, update, content):
        try:
            chat_id = update.message.chat_id
            message_id = update.message.message_id
            command = group_id = admin = channel_name = plan = expire = None
            if content.args:
                self.updater.bot.send_chat_action(chat_id=chat_id, action=telegram.ChatAction.TYPING)
                command = content.args[0]
                if command == "add":
                    group_id, admin, channel_name, plan, expire = content.args[1:]
                    if not db.find('channel', name=channel_name):
                        channel = db.Channel(name=channel_name, admin=int(admin),
                                             group_id=int(group_id), plan=int(plan), expire=timedelta(days=int(expire)))
                        db.add(channel)
                        self.updater.bot.send_message(chat_id=chat_id,
                                                      reply_to_message_id=message_id,
                                                      text="ثبت شد \n\n{}".format(channel.__str__()))
                elif command == "ren":
                    channel_name, expire = content.args[1:]
                    if db.find("channel", name=channel_name):
                        channel = db.find("channel", name=channel_name)
                        channel.expire += timedelta(days=int(expire))
                        db.update(channel)
                        self.updater.bot.send_message(chat_id=chat_id,
                                                      reply_to_message_id=message_id,
                                                      text="ثبت شد \n\n{}".format(channel.__str__()))
                elif command == "plan":
                    channel_name, plan = content.args[1:]
                    channel = db.find("channel", name=channel_name)
                    channel.plan = int(plan)
                    db.update(channel)
                    self.updater.bot.send_message(chat_id=chat_id,
                                                  reply_to_message_id=message_id,
                                                  text="ثبت شد \n\n{}".format(channel.__str__()))
                elif command == "del":
                    channel_name = content.args[1]
                    channel = db.find("channel", name=channel_name)
                    if channel:
                        db.delete(channel)
                elif command == "edit":
                    channel_name, n_channel_name = content.args[1:]
                    channel = db.find("channel", name=channel_name)
                    if channel:
                        channel.name = n_channel_name
                        db.update(channel)
                        self.updater.bot.send_message(chat_id=chat_id,
                                                      reply_to_message_id=message_id,
                                                      text="ثبت شد \n\n{}".format(channel.__str__()))
                elif command == "lst":
                    channels = db.find('channel')
                    text = "channel          expire_date\n"
                    for ch in channels:
                        expire = JalaliDatetime().from_date(ch.expire)
                        now = JalaliDatetime().now()
                        diff = expire - now
                        if diff.days < 7:
                            text += "{} {} 🔴\n\n".format(ch.name, expire.strftime("%A %d %B"))
                        else:
                            text += "{} {} ⚪️\n\n".format(ch.name, expire.strftime("%A %d %B"))

                    self.updater.bot.send_message(chat_id=cna, text=text)
                elif command == "det":
                    channel_name, = content.args[1:]
                    channel = db.find("channel", name=channel_name)
                    if isinstance(channel, db.Channel):
                        self.updater.bot.send_message(chat_id=chat_id, reply_to_message_id=message_id,
                                                      text=strings.status(channel, util.remain(channel), button=False))
                elif command == "db":
                    # db
                    self.updater.bot.send_document(chat_id=cna, document=open("bot_db.db", "rb"),
                                                   timeout=time_out)
                else:
                    self.updater.bot.send_message(chat_id=chat_id,
                                                  reply_to_message_id=message_id,
                                                  text="command {} not found".format(content.args[0]))

            else:
                self.updater.bot.send_message(chat_id=chat_id,
                                              text=strings.admin_hint)
        except Exception as E:
            logging.error("admin: {}".format(E))

    def state(self, update, content):
        try:
            admin = update.message.chat_id

            if not content.args:
                channel = db.find("channel", admin=admin)
            else:
                name = content.args[0]
                channel = db.find("channel", admin=admin, name=name)

            if isinstance(channel, db.Channel):
                text = strings.status(channel, util.remain(channel=channel), button=False)
                self.updater.bot.send_message(chat_id=admin, text=text,
                                              reply_to_message_id=update.message.message_id)
                logging.info("state : {}".format(channel.name))

            elif isinstance(channel, list):
                self.updater.bot.send_message(chat_id=admin,
                                              text="شما صاحب چندین نسخه از بات هستید لطفا نام کانال خود را نیز وارد کنید"
                                                   "مثال:\n"
                                                   "/state @channel",
                                              reply_to_message_id=update.message.message_id)

        except Exception as E:
            logging.error("state : {}".format(E))

    def set(self, update, content):
        try:
            admin = update.message.chat_id
            channel = None

            if len(content.args) == 1:
                channel = db.find("channel", admin=admin)
            elif len(content.args) == 2:
                name = content.args[1]
                channel = db.find("channel", admin=admin, name=name)

            if isinstance(channel, db.Channel):
                state = dict([("off", False), ("on", True)]).get(content.args[0].lower(), None)
                if state is not None:
                    channel.up = state
                    db.update(channel)
                    self.updater.bot.send_message(chat_id=update.message.chat_id, text=strings.up(state=state))
                    logging.info("set: channel {} {}".format(channel.name, content.args[0]))

            elif isinstance(channel, list):
                self.updater.bot.send_message(chat_id=admin,
                                              text="شما صاحب چندین نسخه از بات هستید لطفا نام کانال خود را نیز وارد کنید"
                                                   "مثال:\n"
                                                   "/set off @channel",
                                              reply_to_message_id=update.message.message_id)

        except Exception as E:
            logging.error("set: {}".format(E))

    def error_callback(self, _, __, error):
        try:
            logging.error(error)
            self.updater.bot.send_message(chat_id=cna, text="Heyyy {}".format(JalaliDatetime().now().strftime("%x")))
        except BaseException as E:
            logging.error("TelegramError {}".format(E))

    def task(self, update, content):
        try:
            now = JalaliDatetime().now()
            channels = db.find('channel')

            if now.minute == 0:
                content.bot.send_message(chat_id=cna, text=str(psutil.virtual_memory()[2]))

            for channel in channels:
                if util.time_is_in(now=now, channel=channel):
                    self.send_to_ch(channel=channel)
                if now.hour == now.minute == 0:
                    self.add_member(channel=channel)

        except Exception as E:
            logging.error('Task {}'.format(E))

    def mid_night(self, update, content):
        now = JalaliDatetime().now()
        channels = db.find('channel')
        content.bot.send_document(document=open('bot_db.db', 'rb'), caption=now.strftime("%x"), chat_id=cna)

        text = "channel           expire_date\n"
        for ch in channels:
            expire = JalaliDatetime().from_date(ch.expire)
            now = JalaliDatetime().now()
            diff = expire - now
            if diff.days < 7:
                text += "{} {} 🔴\n\n".format(ch.name, expire.strftime("%A %d %B"))
            else:
                text += "{} {} ⚪️\n\n".format(ch.name, expire.strftime("%A %d %B"))

        content.bot.send_message(chat_id=cna, text=text)

    def run(self):
        try:
            dpa = self.updater.dispatcher.add_handler
            job = self.updater.job_queue
            self.updater.start_polling()
            self.updater.dispatcher.add_error_handler(self.error_callback)

            conv.conversation(self.updater)

            dpa(CommandHandler(command="admin", filters=Filters.user([cna, rhn]), callback=self.admin, pass_args=True))
            dpa(CommandHandler(command="state", filters=Filters.private, callback=self.state, pass_args=True))
            dpa(CommandHandler(command="set", filters=Filters.private, callback=self.set, pass_args=True))

            # to get group id
            dpa(MessageHandler(filters=Filters.status_update.new_chat_members, callback=self.send_info))
            dpa(MessageHandler(filters=Filters.group, callback=self.save, edited_updates=True))

            first = 60 - JalaliDatetime().now().second
            job.run_repeating(callback=self.task, interval=60, first=first)
            job.run_daily(callback=self.mid_night, time=time(hour=0, minute=0))

            user_name = self.updater.bot.name
            print("{}".format(user_name))
            logging.info("{} started".format(user_name))
            self.updater.bot.send_message(chat_id=cna, text="started")

            self.updater.idle()
        except telegram.error.NetworkError as E:
            self.updater.stop()
            logging.error("NETWORK ERROR !!! {}".format(E))
            exit()


timer = SSP(var.TOKEN)
timer.run()
