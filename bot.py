from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
from khayyam3.tehran_timezone import timedelta, JalaliDatetime
import numpy as np
import warnings
import telegram
import strings
import logging
import psutil
import editor
import conv
import var
import db
import os

warnings.simplefilter("ignore", category=Warning)

sina, lili = 103086461, 303962908
limit_size = 1
logging.basicConfig(filename='report.log', level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s')


# noinspection PyBroadException
class SSP:
    def __init__(self, token):
        self.robot = telegram.Bot(token)
        self.updater = Updater(token)
        try:
            for i in ['vid', 'plot', 'logo', 'image', 'gif']:
                dir_ = os.path.join(os.getcwd(), i)
                if not os.path.exists(dir_):
                    os.makedirs(dir_)
        except Exception as _:
            pass

    @staticmethod
    def time_is_in(now, channel):
        interval = (int(channel.interval[:-2]),)
        if channel.interval.endswith("mr"):
            interval = np.arange(0, 60, interval[0], dtype=np.uint8)
        elif channel.interval.endswith("hr"):
            interval = np.arange(0, 24, interval[0], dtype=np.uint8)

        if (channel.interval[-2] == "m" and now.minute in interval) or \
                (channel.interval[-2] == "h" and now.hour in interval):
            return True
        return False

    def save(self, _, update):
        try:
            um = update.message
            ue = update.edited_message
            message = None
            # edited
            if ue:
                from_gp = ue.chat_id
                msg_gp_id = ue.message_id
                channel = db.find('channel', group_id=from_gp)
                message = db.find(table='message', msg_gp_id=msg_gp_id, gp_id=from_gp)

                # after sent
                if ue.text and message.sent:
                    message.txt = editor.id_remove(text=ue.text, channel=channel)
                    if len(um.entities) > 0:
                        entities = um.entities
                        url = ''.join([entities[i].url if entities[i].url else '' for i in range(len(entities))])
                        message.txt += '\n<a href="{}">​​​​​​​​​​​</a>'.format(url)
                        message.other = 'url'
                    parse_mode = 'HTML' if message.other == 'url' else None
                    self.robot.edit_message_text(chat_id=message.to_channel, message_id=message.msg_ch_id,
                                                 text=message.txt,
                                                 parse_mode=parse_mode)
                    message.sent = message.ch_a = True
                elif message.sent:
                    media = out = None
                    text = ue.caption if ue.caption else ' '
                    text = editor.id_remove(text=text, channel=channel)

                    if ue.photo:
                        media = ue.photo[-1].file_id
                        dir_ = "./image/{}.jpg".format(channel.name)
                        out = './image/{}_out.jpg'.format(channel.name)
                        self.robot.getFile(media).download(dir_)

                        message.kind = "photo"
                        if channel.plan >= 1:
                            text = editor.image_watermark(photo=dir_, out=out, caption=text, channel=channel)
                            media = telegram.InputMediaPhoto(media=open(out, 'rb'), caption=text)
                        else:
                            text = editor.id_remove(text=text, channel=channel)
                            media = telegram.InputMediaPhoto(media=media, caption=text)

                    elif ue.animation:
                        media = ue.animation.file_id
                        mime = str(um.animation.mime_type).split('/')[1]
                        dir_ = "./gif/{}.{}".format(channel.name, mime)
                        out = "./gif/{}_out.mp4".format(channel.name)
                        size = ue.video.file_size / (1024 ** 2)

                        message.mime = mime
                        message.kind = 'animation'

                        if size <= limit_size and channel.plan >= 2:
                            self.robot.getFile(media).download(dir_)
                            text = editor.vid_watermark(vid=dir_, out=out, kind=message.kind,
                                                        caption=text, channel=channel)
                            media = telegram.InputMediaVideo(media=open(out, 'rb'), caption=text)
                        else:
                            text = editor.id_remove(text=text, channel=channel)
                            media = telegram.InputMediaAnimation(media=media, caption=text)

                    elif ue.video:
                        media = ue.video.file_id
                        mime = str(um.video.mime_type).split('/')[1]
                        dir_ = "./vid/{}.{}".format(channel.name, mime)
                        out = './vid/{}_out.mp4'.format(channel.name)
                        size = ue.video.file_size / (1024 ** 2)

                        message.mime = mime
                        message.kind = 'video'

                        if size < limit_size and channel.plan >= 3:
                            self.robot.getFile(media).download(dir_)
                            text = editor.vid_watermark(vid=dir_, out=out, kind=message.kind,
                                                        caption=text, channel=channel)
                            media = telegram.InputMediaVideo(media=open(out, 'rb'), caption=text)
                        else:
                            text = editor.id_remove(text=text, channel=channel)
                            media = telegram.InputMediaVideo(media=media, caption=text)

                    elif ue.document:
                        media = ue.document.file_id
                        media = telegram.InputMediaDocument(media=media, caption=text)

                    elif ue.audio:
                        media = ue.audio.file_id
                        media = telegram.InputMediaAudio(media=media, caption=text)

                    if media:
                        self.robot.edit_message_media(media=media, chat_id=message.to_channel,
                                                      message_id=message.msg_ch_id)

                    if out:
                        os.remove(out)
                    if ue.caption:
                        self.robot.edit_message_caption(chat_id=message.to_channel, message_id=message.msg_ch_id,
                                                        caption=text)

                    message.sent = message.ch_a = True
                    message.txt = text

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
                channel = db.find(table='channel', group_id=um.chat_id)
                if um.text:
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

                    db.add(
                        db.Message(from_group=um.chat_id, to_channel=channel.name, msg_gp_id=um.message_id, kind=kind,
                                   txt=text, file_id=file_id, size=size, mime=mime, other=other))

            logging.info("save {}".format(tuple(message.__dict__.items()))[1:])
        except Exception as E:
            logging.error('save {}'.format(E))

    def add_member(self, channel):
        try:
            current_date = JalaliDatetime().now().to_date()
            num = self.robot.get_chat_members_count(channel.name)
            member = db.Member(number=num, channel_name=channel.name, calendar=current_date)
            db.add(member)
        except Exception as E:
            logging.error('add_members {}'.format(E))

    def send_to_ch(self, channel, attempt=1):
        message = db.get_last_msg(channel_name=channel.name)
        try:
            if not message:
                pass

            # media_group
            elif isinstance(message, list):
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

                self.robot.send_media_group(chat_id=chat_id, media=media)
                for msg in new_message:
                    db.update(msg)
                logging.info('media_group sent {}'.format(tuple(message.__dict__.items())[1:]))

            # edited
            elif message.ch_a:
                txt = editor.id_remove(text=message.txt, channel=channel)

                if message.kind == 'text':
                    message.msg_ch_id = self.robot.edit_message_text(chat_id=message.to_channel, text=txt,
                                                                     message_id=message.msg_ch_id)
                else:
                    message.msg_ch_id = self.robot.edit_message_caption(chat_id=message.to_channel, caption=txt,
                                                                        message_id=message.msg_ch_id)

                db.update(message)
                logging.info('edit_msg {}'.format(tuple(message.__dict__.items())[1:]))

            # regular
            elif not message.ch_a:
                txt = editor.id_remove(text=message.txt, channel=channel)
                parse_mode = 'HTML' if message.other == 'url' else None

                if message.kind == 'text':
                    message.msg_ch_id = self.robot.send_message(chat_id=message.to_channel, text=txt,
                                                                parse_mode=parse_mode).message_id

                elif message.kind == 'photo':
                    dir_ = "./image/{}.jpg".format(channel.name)
                    out = "./image/{}_out.jpg".format(channel.name)
                    if channel.plan >= 1:
                        self.robot.getFile(message.file_id).download(dir_)
                        txt = editor.image_watermark(photo=dir_, out=out, caption=message.txt, channel=channel)
                        message.msg_ch_id = self.robot.send_photo(chat_id=message.to_channel, photo=open(out, 'rb'),
                                                                  caption=txt).message_id
                    else:
                        txt = editor.id_remove(message.txt, channel)
                        message.msg_ch_id = self.robot.send_photo(chat_id=message.to_channel, photo=message.file_id,
                                                                  caption=txt).message_id

                elif message.kind == 'video':
                    form = message.mime
                    dir_ = "./vid/{}.{}".format(channel.name, form)
                    out = "./vid/{}_out.mp4".format(channel.name)

                    if message.size <= limit_size and channel.plan >= 3:
                        self.robot.getFile(message.file_id).download(dir_, timeout=10)
                        try:
                            txt = editor.vid_watermark(vid=dir_, out=out, kind=message.kind,
                                                       caption=message.txt, channel=channel)

                            message.msg_ch_id = self.robot.send_video(chat_id=message.to_channel,
                                                                      video=open(out, 'rb'),
                                                                      caption=txt,
                                                                      timeout=30).message_id
                        except Exception as _:
                            message.msg_ch_id = self.robot.send_video(chat_id=message.to_channel,
                                                                      video=message.file_id,
                                                                      caption=txt).message_id
                    else:
                        txt = editor.id_remove(text=message.txt, channel=channel)
                        message.msg_ch_id = self.robot.send_video(chat_id=message.to_channel,
                                                                  video=message.file_id,
                                                                  caption=txt).message_id

                elif message.kind == 'animation':
                    form = message.mime
                    dir_ = "./gif/{}.{}".format(channel.name, form)
                    out = "./gif/{}_out.mp4".format(channel.name)

                    if message.size <= limit_size and channel.plan >= 2:
                        self.robot.getFile(message.file_id).download(dir_, timeout=10)
                        try:
                            txt = editor.vid_watermark(vid=dir_, out=out, kind=message.kind,
                                                       caption=message.txt, channel=channel)

                            message.msg_ch_id = self.robot.send_animation(chat_id=message.to_channel,
                                                                          animation=open(out, 'rb'),
                                                                          caption=txt).message_id
                        except Exception as _:
                            message.msg_ch_id = self.robot.send_animation(chat_id=message.to_channel,
                                                                          animation=message.file_id,
                                                                          caption=txt).message_id
                    else:
                        txt = editor.id_remove(text=message.txt, channel=channel)
                        message.msg_ch_id = self.robot.send_animation(chat_id=message.to_channel,
                                                                      animation=message.file_id,
                                                                      caption=txt).message_id

                elif message.kind == 'audio':
                    message.msg_ch_id = self.robot.send_audio(chat_id=message.to_channel, audio=message.file_id,
                                                              caption=txt).message_id

                elif message.kind == 'document':
                    message.msg_ch_id = self.robot.send_document(chat_id=message.to_channel, document=message.file_id,
                                                                 caption=txt).message_id

                elif message.kind == 'v_note':
                    message.msg_ch_id = self.robot.send_video_note(chat_id=message.to_channel,
                                                                   video_note=message.file_id).message_id

                elif message.kind == 'voice':
                    message.msg_ch_id = self.robot.send_voice(chat_id=message.to_channel, voice=message.file_id,
                                                              caption=txt).message_id

                elif message.kind == 'sticker':
                    message.msg_ch_id = self.robot.send_sticker(chat_id=message.to_channel, sticker=message.file_id,
                                                                caption=txt).message_id

                logging.info('send_to_ch {}'.format(tuple(message.__dict__.items())[1:]))
                message.sent = True
                message.ch_a = True
                db.update(message)

        except IndexError:
            pass
        except AttributeError:
            pass
        except Exception as E:
            logging.error('send_to_ch attempt {} Error: {}'.format(tuple(message.__dict__.items())[1:], E))
            if attempt < 2:
                self.send_to_ch(channel, attempt + 1)
            else:
                message.sent = True
                db.update(message)

    def task(self, bot, _):
        try:
            now = JalaliDatetime().now()
            channels = db.find('channel')

            if now.minute == 0:
                bot.send_message(chat_id=sina, text=str(psutil.virtual_memory()[2]))

            for channel in channels:
                if self.time_is_in(now=now, channel=channel):
                    self.send_to_ch(channel=channel)
                if now.hour == now.minute == 0:
                    self.add_member(channel=channel)

            if now.hour == now.minute == 0:
                self.robot.send_document(document=open('bot_db.db', 'rb'),
                                         caption=now.strftime("%x"),
                                         chat_id=sina)

        except Exception as E:
            logging.error('Task {}'.format(E))

    def admin(self, _, update, args):
        try:
            chat_id = update.message.chat_id
            message_id = update.message.message_id
            command = group_id = admin = channel_name = plan = expire = None
            if args:
                command = args.split()[0]
                if command == "add":
                    group_id, admin, channel_name, plan = args[1:]
                    if not db.find('channel', name=channel_name):
                        channel = db.Channel(name=channel_name, admin=int(admin), group_id=int(group_id), plan=int(plan))
                        db.add(channel)
                        self.robot.send_message(chat_id=chat_id,
                                                reply_to_message_id=message_id,
                                                text="ثبت شد \n\n{}".format(tuple(channel.__dict__.items())[1:]))
                elif command == "ren":
                    channel_name, expire = args[1:]
                    if db.find("channel", name=channel_name):
                        channel = db.find("channel", name=channel_name)
                        channel.expire + timedelta(days=int(expire))
                        db.update(channel)
                        self.robot.send_message(chat_id=chat_id,
                                                reply_to_message_id=message_id,
                                                text="ثبت شد \n\n{}".format(tuple(channel.__dict__.items())[1:]))
                elif command == "plan":
                    channel_name, plan = args[1:]
                    channel = db.find("channel", name=channel_name)
                    channel.plan = int(plan)
                    db.update(channel)
                    self.robot.send_message(chat_id=chat_id,
                                            reply_to_message_id=message_id,
                                            text="ثبت شد \n\n{}".format(tuple(channel.__dict__.items())[1:]))
            else:
                self.robot.send_message(chat_id=chat_id,
                                        text=strings.admin_hint)
        except Exception as E:
            logging.error("admin {}".format(E))

    def send_info(self, _, update):
        try:
            um = update.message
            if isinstance(um.new_chat_members, list):
                chat_member = um.new_chat_members[0]
                channels = db.find('channel', admin=um.from_user.id)

                if chat_member.id == self.robot.id:
                    if um.chat.type == 'supergroup' and um.chat_id in [i.group_id for i in channels]:
                        self.robot.send_message(chat_id=um.chat_id, text="تبریک، بات با موفقیت در گروه ثبت شد")
                    else:
                        self.robot.send_message(chat_id=um.chat_id, text=um.chat_id)
                        self.robot.leave_chat(um.chat_id)
        except Exception as E:
            print(E)

    def run(self):
        dpa = self.updater.dispatcher.add_handler
        job = self.updater.job_queue
        self.updater.start_polling()

        # conversations
        conv.conversation(self.updater)

        dpa(CommandHandler(command='admin', filters=Filters.user([sina, lili]), callback=self.admin, pass_args=True))
        dpa(MessageHandler(filters=Filters.status_update.new_chat_members, callback=self.send_info))
        dpa(MessageHandler(filters=Filters.group, callback=self.save, edited_updates=True))

        first = 60 - JalaliDatetime().now().second
        job.run_repeating(callback=self.task, interval=60, first=first)

        print('started')
        self.updater.idle()


timer = SSP(var.TOKEN)
timer.run()
