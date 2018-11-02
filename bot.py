from telegram.ext import Updater, MessageHandler, CommandHandler, Filters, ConversationHandler, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton as Inline
from khayyam3.tehran_timezone import JalaliDatetime, timedelta
from khayyam3 import JalaliDate
from datetime import datetime
import numpy as np
import matplotlib
import telegram
import strings
import logging
import psutil
import editor
import pytz
import time
# import var
import db
import os

matplotlib.use('AGG', force=True)
import matplotlib.pyplot as plt

sina, lili = 103086461, 303962908
logging.basicConfig(filename='report.log', level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s')

# todo edit media
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
    def current_time():
        utc = pytz.utc
        u = time.gmtime()
        utc_dt = datetime(u[0], u[1], u[2], u[3], u[4], u[5], tzinfo=utc)
        eastern = pytz.timezone('Asia/Tehran')
        loc_dt = utc_dt.astimezone(eastern)
        return JalaliDatetime().now(), loc_dt

    def sleep(self, entry: datetime = None, bed=None, wake=None):
        entry = self.current_time()[1].strftime('%H%M') if not entry else entry.strftime('%H%M')

        if bed == 'off' and wake == 'off':
            return False

        if entry >= bed > wake < entry or entry >= bed < wake > entry:
            return True

        return False

    def time_is_in(self, now, channel: db.Channel):
        interval: str = channel.interval
        if interval.endswith('r'):
            if interval[-2] == 'm':
                interval: int = int(interval[:-2])
                minute = tuple(range(interval, 61, interval))
                if now.minute in minute and not self.sleep(bed=channel.bed, wake=channel.wake):
                    return True

            elif interval[-2] == 'h':
                interval: int = int(interval[:-2])
                hour = tuple(range(interval, 24, interval))
                if now.hour in hour and now.minute == 0 and not self.sleep(bed=channel.bed, wake=channel.wake):
                    return True

        elif interval.endswith('f'):
            if interval[-2] == 'm':
                minute = int(interval[:-2])

                if now.minute == minute and not self.sleep(bed=channel.bed, wake=channel.wake):
                    return True
            elif interval[-2] == 'h':
                hour = int(interval[:-2])
                if now.hour == hour and now.minute == 0 and not self.sleep(bed=channel.bed, wake=channel.wake):
                    return True
        return False

    def status(self, bot, update):
        try:
            um = update.message
            admin = um.from_user.id
            channels = db.find('channel', admin=admin)
            if channels:
                if isinstance(channels, db.Channel):
                    channel = channels
                    chat_id = um.chat_id
                    message_id = um.message_id
                    keyboard = [[Inline('وقفه', callback_data=f'interval;{channel.name}'),
                                 Inline('ساعت توقف', callback_data=f'bed;{channel.name}'),
                                 Inline('ساعت شروع', callback_data=f'wake;{channel.name}')],
                                [Inline('مشاهده نمودار', callback_data=f"graph;{channel.name}"),
                                 Inline('تنظیم لوگو', callback_data=f"logo;{channel.name}")],
                                [Inline('تمدید', callback_data=f'up;{channel.name}')]]
                    bot.send_message(chat_id=chat_id,
                                     text=strings.status(channel),
                                     reply_to_message_id=message_id,
                                     reply_markup=InlineKeyboardMarkup(keyboard))
                    return self.select

                elif isinstance(channels, list):
                    lst = [[Inline(i.name, callback_data=f"_;{i.name}")] for i in channels]
                    bot.send_message(chat_id=admin,
                                     text="شما صاحب چندین کانال هستید\nمایل به مشاهده تنظیمات کدام یک هستید؟",
                                     reply_markup=InlineKeyboardMarkup(lst))
                    return self.setting

        except Exception as E:
            logging.error("status {}".format(E))

    def setting(self, bot, update):
        try:
            if update.callback_query:
                data: str = update.callback_query.data
                admin, name = data.split(';')
                if not admin == '_':
                    channel = db.find("channel", admin=admin, name=name)
                else:
                    channel = db.find('channel', name=name)
                chat_id = update.callback_query.message.chat_id
                message_id = update.callback_query.message.message_id

                keyboard = [[Inline('وقفه', callback_data=f'interval;{channel.name}'),
                             Inline('ساعت توقف', callback_data=f'bed;{channel.name}'),
                             Inline('ساعت شروع', callback_data=f'wake;{channel.name}')],
                            [Inline('مشاهده نمودار', callback_data=f"graph;{channel.name}"),
                             Inline('تنظیم لوگو', callback_data=f"logo;{channel.name}")],
                            [Inline('تمدید', callback_data=f'up;{channel.name}')]]
                bot.edit_message_text(chat_id=chat_id,
                                      text=strings.status(channel),
                                      message_id=message_id,
                                      reply_markup=InlineKeyboardMarkup(keyboard))
                return self.select
            else:
                um = update.message
                admin = um.from_user
                channel: db.Channel = db.find('channel', admin=admin)

                bot.send_message(chat_id=admin.id,
                                 text=strings.status(channel),
                                 reply_markup=InlineKeyboardMarkup(
                                     [[Inline('وقفه', callback_data=f'interval;{channel.name}'),
                                       Inline('ساعت توقف', callback_data=f'bed;{channel.name}'),
                                       Inline('ساعت شروع', callback_data=f'wake;{channel.name}'),
                                       [Inline('مشاهده نمودار', callback_data=f"graph;{channel.name}"),
                                        Inline('تنظیم لوگو', callback_data=f"logo;{channel.name}")],
                                       ]]
                                 ))
                return self.select
        except Exception as E:
            logging.error("setting {}".format(E))

    def select(self, _, update):
        try:
            um = update.callback_query
            data: str = um.data
            data: list = data.split(';')
            chat_id = um.message.chat_id
            message_id = um.message.message_id
            if data[0] == 'interval':
                keyboard = [[Inline('01M', callback_data=f'01m;{data[1]}')]]
                for i in range(5, 60, 5):
                    keyboard.append(
                        [Inline("{}M".format(str(i).zfill(2)), callback_data=f"{str(i).zfill(2)}m;{data[1]}")])
                for i in range(0, 24):
                    keyboard.append(
                        [Inline("{}H".format(str(i).zfill(2)), callback_data=f'{str(i).zfill(2)}h;{data[1]}')])
                keyboard = np.array(keyboard).reshape((-1, 6)).tolist()
                keyboard.append([Inline('بازگشت به منوی تنظیمات', callback_data=f'setting;{data[1]}')])
                self.robot.edit_message_text(chat_id=chat_id,
                                             message_id=message_id,
                                             text="گام اول:\n"
                                                  "زمانبدی مورد نظر خود را انتخاب کنید\n تنها درصورتی که مایل "
                                                  "به تغییر دقایق به صورت دلخواه هستید "
                                                  "برای مثال:\n"
                                                  "13m -> برابر با هر 13 دقیقه\n"
                                                  "از این روش استفاده کنید:\n"
                                                  "/delay 13m @name-e-channel"
                                                  "\n اگر دچار مشکلی شده اید از ما کمک بگیرید\n"
                                                  "@s_for_cna",
                                             reply_markup=InlineKeyboardMarkup(keyboard))
                return self.step2
            elif data[0] == 'wake':
                keyboard = []
                for i in range(1, 25):
                    keyboard.append(
                        [Inline('{}:00'.format(str(i).zfill(2)), callback_data=f"{str(i).zfill(2)}w;{data[1]}")])
                keyboard = np.array(keyboard).reshape((6, -1)).tolist()
                keyboard.append([Inline('بازگشت به منوی تنظیمات', callback_data=f'setting;{data[1]}')])
                self.robot.edit_message_text(chat_id=chat_id,
                                             message_id=message_id,
                                             text="بات از چه ساعتی شروع به کار کند؟",
                                             reply_markup=InlineKeyboardMarkup(keyboard))
                return self.done
            elif data[0] == 'bed':
                keyboard = []
                for i in range(1, 25):
                    keyboard.append(
                        [Inline('{}:00'.format(str(i).zfill(2)), callback_data=f"{str(i).zfill(2)}b;{data[1]}")])
                keyboard = np.array(keyboard).reshape((6, -1)).tolist()
                keyboard.append([Inline('بازگشت به منوی تنظیمات', callback_data=f'setting;{data[1]}')])
                self.robot.edit_message_text(chat_id=chat_id,
                                             message_id=message_id,
                                             text="بات در چه ساعتی خاموش شود؟",
                                             reply_markup=InlineKeyboardMarkup(keyboard))
                return self.done
            elif data[0] == 'graph':
                self.robot.edit_message_text(chat_id=chat_id,
                                             message_id=message_id,
                                             text="نمودار در چه بازه زمانی باشد؟",
                                             reply_markup=InlineKeyboardMarkup(
                                                 [[Inline('یک هفته', callback_data=f"1w;{data[1]}"),
                                                   Inline('یک ماه', callback_data=f"1m;{data[1]}"),
                                                   Inline('یک سال', callback_data=f"1y;{data[1]}")]]
                                             ))
                return self.graph
            elif data[0] == 'logo':
                self.robot.edit_message_text(chat_id=chat_id,
                                             message_id=message_id,
                                             text="یک عکس با فرمت png بدون پس زمینه برام بفرست در ابعاد مربع\n"
                                                  "اگر نمیتونی یا بلد نیستی اینکار رو بکنی"
                                                  " میتونم از اسم کانال به عنوان لوگو استفاده کنم",
                                             reply_markup=InlineKeyboardMarkup(
                                                 [[Inline('استفاده از نام کانال', callback_data=f"logo;{data[1]}")]]))
                return self.set_logo
            elif data[0] == 'up':
                channel = db.find('channel', name=data[1])
                self.robot.edit_message_text(chat_id=chat_id,
                                             message_id=message_id,
                                             text=strings.status_upgrade(channel.plan))
                return ConversationHandler.END
        except Exception as E:
            logging.error("select {}".format(E))

    def step2(self, _, update):
        if update.callback_query:
            um = update.callback_query
            data = um.data.split(';')
            interval: str = data[0]
            ch_name: str = data[1]

            if interval.endswith('m'):
                interval: int = int(interval[:-1])
                if 1 <= interval <= 30:
                    self.robot.edit_message_text(chat_id=um.message.chat_id,
                                                 message_id=um.message.message_id,
                                                 text="گام دوم:\n"
                                                      "1️⃣ پیام ها هر {0} دقیقه ارسال شوند. برای مثال بصورت 01:{0}, "
                                                      "01:{1} و ...\n"
                                                      "2️⃣ پیام ها وقتی دقیقه شمار برابر {0} است ارسال شوند برای مثال "
                                                      "01:{0}, 02:{0}, 03:{0} و ...\n"
                                                      "کدام یک مورد پسند شماست؟\n"
                                                      "از ما کمک بگیرید:\n"
                                                      "@s_for_cna".format(str(interval).zfill(2),
                                                                          str(interval * 2).zfill(2)),
                                                 reply_markup=InlineKeyboardMarkup(
                                                     [[Inline('حالت  1️⃣', callback_data=f'{interval}mr;{ch_name}'),
                                                       Inline('حالت  2️⃣', callback_data=f'{interval}mf;{ch_name}')],
                                                      [Inline('لغو، بازگشت', callback_data=f'_;{ch_name}')]])
                                                 )
                else:
                    self.robot.edit_message_text(chat_id=um.message.chat_id,
                                                 message_id=um.message.message_id,
                                                 text="گام دوم:\n"
                                                      "پیام ها در ساعاتی مانند 01:{0}, 02:{0} ارسال میشوند\n"
                                                      "از ما کمک بگیرید:\n"
                                                      "@s_for_cna".format(str(interval).zfill(2)),
                                                 reply_markup=InlineKeyboardMarkup(
                                                     [[Inline('تایید', callback_data=f'{interval}mr;{ch_name}')],
                                                      [Inline('لغو، بازگشت', callback_data=f'_;{ch_name}')]])
                                                 )

                return self.done
            elif interval.endswith('h'):
                interval: int = int(interval[:-1])
                if 1 <= interval < 13:
                    self.robot.edit_message_text(chat_id=um.message.chat_id,
                                                 message_id=um.message.message_id,
                                                 text="گام دوم:\n"
                                                      "1️⃣ پیام ها هر {0} ساعت ارسال شوند. برای مثال بصورت {0}:00, "
                                                      " {1}:00 و ... "
                                                      "2️⃣ پیام ها هر روز راس ساعت {0}:00 ارسال شوند"
                                                      "کدام یک مورد پسند شماست؟\n"
                                                      "از ما کمک بگیرید:\n"
                                                      "@s_for_cna".format(str(interval).zfill(2),
                                                                          str(interval * 2).zfill(2)),
                                                 reply_markup=InlineKeyboardMarkup(
                                                     [[Inline('حالت  1️⃣', callback_data=f'{interval}hr;{ch_name}'),
                                                       Inline('حالت  2️⃣', callback_data=f'{interval}hf;{ch_name}')],
                                                      [Inline('لغو، بازگشت', callback_data=f'_;{ch_name}')]])
                                                 )
                else:
                    self.robot.edit_message_text(chat_id=um.message.chat_id,
                                                 message_id=um.message.message_id,
                                                 text="گام دوم:\n"
                                                      "پیام ها هر روز راس ساعت {0}:00 ارسال شوند"
                                                      "کدام یک مورد پسند شماست؟\n"
                                                      "از ما کمک بگیرید:\n"
                                                      "@s_for_cna".format(str(interval).zfill(2)),
                                                 reply_markup=InlineKeyboardMarkup(
                                                     [[Inline('تایید', callback_data=f'{interval}mr;{ch_name}')],
                                                      [Inline('لغو، بازگشت', callback_data=f'_;{ch_name}')]])
                                                 )
                return self.done

    def done(self, _, update):
        try:
            if update.callback_query:
                um = update.callback_query
                data: str = um.data
                part1, channel_name = data.split(';')
                chat_id = um.message.chat_id
                message_id = um.message.message_id

                channel: db.Channel = db.find('channel', name=channel_name)

                if part1 == '_':
                    pass
                elif part1.endswith('b'):
                    bed = part1[:-1]
                    channel.bed = bed
                    db.update(channel)
                elif part1.endswith('w'):
                    wake = part1[:-1]
                    channel.wake = wake
                    db.update(channel)
                else:
                    interval = part1
                    channel.interval = interval
                    db.update(channel)

                keyboard = [[Inline('وقفه', callback_data=f'interval;{channel.name}'),
                             Inline('ساعت توقف', callback_data=f'bed;{channel.name}'),
                             Inline('ساعت شروع', callback_data=f'wake;{channel.name}')],
                            [Inline('مشاهده نمودار', callback_data=f"graph;{channel.name}"),
                             Inline('تنظیم لوگو', callback_data=f"logo;{channel.name}")],
                            [Inline('تمدید', callback_data=f'up;{channel.name}')]]
                self.robot.edit_message_text(chat_id=chat_id,
                                             message_id=message_id,
                                             text=strings.status(channel),
                                             reply_markup=InlineKeyboardMarkup(keyboard))
                return self.select

        except Exception as E:
            logging.error("done {}".format(E))

    def graph(self, _, update):
        try:
            if update.callback_query:
                um = update.callback_query
                admin = um.message.chat_id
                data = um.data
                domain, ch_name = data.split(';')
                save_in = f"plot/{ch_name}.png"

                d = {'1w': 7, '1m': 31, '1y': 365}
                domain = d.get(domain)
                now = JalaliDatetime().now().to_date()
                from_ = now - timedelta(days=domain)

                out = db.find('member', admin=admin, name=ch_name, from_=from_, til=now)

                y = out[:, 0]
                y = np.append(y, self.robot.get_chat_members_count(ch_name))
                diff = np.mean(np.diff(y), dtype=int)

                d = [now + timedelta(days=i) for i in range(domain + 1)]
                for i, j in enumerate(d):
                    if len(out) >= i + 1:
                        if not out[i, 1] == j:
                            out[i] = [out[i - 1, 0] + diff, j]

                x = np.arange(domain + 1, dtype=int)
                print(x, y, diff, out)

                plt.plot(x, y, marker='o', label='now', color='red', markersize=4)
                plt.plot(list(x)[:-1], y[:-1], marker='o', label='members', color='blue', markersize=4)

                plt.ticklabel_format(style='plain', axis='x', useOffset=False)
                plt.ticklabel_format(style='plain', axis='y', useOffset=False)
                plt.grid()
                plt.xlim(x.min(), x.max())
                plt.ylim(y.min(), y.max())
                plt.xlabel('days')
                plt.ylabel('members')
                plt.legend(loc=4)

                plt.savefig(save_in)
                plt.close()

                now = JalaliDate().from_date(now)
                from_ = JalaliDate().from_date(from_)
                self.robot.send_photo(chat_id=um.message.chat_id,
                                      photo=open(save_in, 'rb'),
                                      caption=f"از {now} تا {from_} در {domain} روز\n"
                                              f" کمترین میزان تعداد اعضا 🔻 {y.min()} و بیشترین 🔺 {y.max()}\n"
                                              f" میانگین سرعت عضو شدن اعضا در روز {diff}\n"
                                              f"پیش بینی برای {domain} روز آینده برابر {domain*diff}")
                os.remove(save_in)
                return ConversationHandler.END
        except Exception as E:
            print(E)

    def set_logo(self, _, update):
        try:
            um = update.message
            chat_id = um.chat_id
            if um.document:
                file_id = um.document.file_id
                mime: str = um.document.mime_type
                size = um.document.file_size
                name = um.caption if um.caption else None
                if name:
                    res = db.find('channel', admin=chat_id, name=name)
                else:
                    res = db.find('channel', admin=chat_id)
                if isinstance(res, db.Channel) and mime.startswith('image') and size < (8 * 1025 * 1024):
                    channel = res
                    self.robot.get_file(file_id=file_id).download(f'logo/{channel.name}.png')
                    channel.logo = True
                    db.update(channel)
                    keyboard = []
                    for i in range(1, 10):
                        keyboard.append([Inline(str(i), callback_data=f"{i};{channel.name}")])
                    keyboard = np.array(keyboard).reshape((3, 3)).tolist()
                    keyboard.append([Inline('هیچکدام', callback_data=f'0;{channel.name}')])

                    self.robot.send_photo(chat_id=chat_id,
                                          reply_to_message_id=um.message_id,
                                          photo=open('info.png', 'rb'),
                                          caption='خب لوگو تایید شد. محل پیش فرض قرارگیری لوگو رو حالا انتخاب کن\n'
                                                  'اگر میخوای بصورت پیش فرض لوگو روی عکس ها و گیف ها گذاشته نشه '
                                                  '"هیچکدام" رو انتخاب کن\n'
                                                  'پشتیبانی\n'
                                                  '@s_for_cna',
                                          reply_markup=InlineKeyboardMarkup(keyboard))
                    return self.set_pos

                elif isinstance(res, list):
                    self.robot.send_message(chat_id=chat_id,
                                            reply_to_message_id=um.message_id,
                                            text=strings.set_logo_fail)
                    return self.set_logo
                else:
                    self.robot.send_message(chat_id=chat_id,
                                            reply_to_message_id=um.message_id,
                                            text=strings.set_logo_else)
                    return self.set_logo
        except Exception as E:
            logging.error("set_logo {}".format(E))

    def set_pos(self, _, update):
        try:
            um = update.callback_query
            admin = um.message.chat_id
            data = um.data
            pos, name = data.split(';')
            channel = db.find("channel", admin=admin, name=name)
            channel.pos = int(pos)
            db.update(channel)
            self.robot.send_message(chat_id=admin,
                                    reply_to_message_id=um.message.message_id,
                                    text="تغییرات اعمال شد",
                                    reply_markup=InlineKeyboardMarkup(
                                        [[Inline('وضعیت', callback_data=f'{admin};{name}')]]
                                    ))
            return self.setting
        except Exception as E:
            logging.error("set_pos {}".format(E))

    def set_interval(self, _, update, args):
        try:
            um = update.message
            admin = um.from_user
            if args:
                if len(args) == 2:
                    interval = args[0]
                    ch_name = args[1]
                    channel = db.find('channel', name=ch_name, admin=admin.id)
                    if channel:
                        if interval.endswith('m') and interval[:-1].isdigit():
                            interval = int(interval[:-1])
                            if 1 < interval <= 30:
                                self.robot.send_message(chat_id=um.chat_id,
                                                        reply_to_message_id=um.message_id,
                                                        text="گام دوم:\n"
                                                             "1️⃣ پیام ها هر {0} دقیقه ارسال شوند."
                                                             " برای مثال بصورت 01:{0}, "
                                                             "01:{1} و ...\n"
                                                             "2️⃣ پیام ها وقتی دقیقه شمار برابر {0} است"
                                                             " ارسال شوند برای مثال "
                                                             "01:{0}, 02:{0}, 03:{0} و ...\n"
                                                             "کدام یک مورد پسند شماست؟\n"
                                                             "از ما کمک بگیرید:\n"
                                                             "@s_for_cna".format(str(interval).zfill(2),
                                                                                 str(interval * 2).zfill(2)),
                                                        reply_markup=InlineKeyboardMarkup(
                                                            [[Inline('حالت  1️⃣',
                                                                     callback_data=f'{interval}mr;{ch_name}'),
                                                              Inline('حالت  2️⃣',
                                                                     callback_data=f'{interval}mf;{ch_name}')],
                                                             [Inline('لغو، بازگشت',
                                                                     callback_data=f'_;{ch_name}')]])
                                                        )
                            else:
                                self.robot.send_message(chat_id=um.chat_id,
                                                        reply_to_message_id=um.message_id,
                                                        text="گام دوم:\n"
                                                             "پیام ها در ساعاتی مانند 01:{0}, 02:{0} ارسال میشوند\n"
                                                             "از ما کمک بگیرید:\n"
                                                             "@s_for_cna".format(str(interval).zfill(2)),
                                                        reply_markup=InlineKeyboardMarkup(
                                                            [[Inline('تایید',
                                                                     callback_data=f'{interval}mr;{ch_name}')],
                                                             [Inline('لغو، بازگشت',
                                                                     callback_data=f'_;{ch_name}')]])
                                                        )

                            return self.done

        except Exception as E:
            logging.error("set_interval: {}".format(E))

    def remain(self, admin, channel):
        try:
            remaining = db.remain(channel.name)
            step = JalaliDatetime().now()
            rem = remaining

            while remaining > 0:
                if self.sleep(step, bed=channel.bed, wake=channel.wake):
                    step += timedelta(hours=channel.wake / 10000 - step.hour)
                if step.minute in channel.interval and not step.minute == 0:
                    remaining -= 1
                step += timedelta(minutes=1)

            logging.info("remain by {}".format(admin))
            if rem > 0:
                rem, date = rem, step.strftime('%y-%m-%d -> %H:%M')
                text = 'پیام های باقیمانده {} کانال تا {} تامین خواهد بود'.format(remaining, date)
            else:
                text = 'هیچ پیامی در صف نیست'

            return text
        except Exception as E:
            logging.error("Could't get remaining time by {} Error: {}".format(admin, E))

    @staticmethod
    def cancel(_, __):
        return ConversationHandler.END

    def start(self, bot, update):
        try:
            chat_id = update.message.chat_id
            message_id = update.message.message_id

            bot.send_message(chat_id=chat_id,
                             text=strings.start,
                             reply_to_message_id=message_id,
                             reply_markup=InlineKeyboardMarkup(
                                 [[Inline('خرید', callback_data="buy")],
                                  [Inline('تست (رایگان)', callback_data="test")],
                                  [Inline('راهنما', callback_data="guide")]]
                             ))
            return self.start_select
        except Exception as E:
            logging.error("start {}".format(E))

    def start_select(self, bot, update):
        um = update.callback_query
        message_id = um.message.message_id
        data = um.data
        chat_id = um.message.chat_id

        if data == "buy":
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=message_id,
                                  text=strings.start_buy)
            return self.start_register
        elif data == "test":
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=message_id,
                                  text=strings.start_select_test)
            return self.start_register
        elif data == "guide":
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=message_id,
                                  text=strings.start_select_guide,
                                  reply_markup=InlineKeyboardMarkup(
                                      [[Inline('خرید', callback_data='buy')],
                                       [Inline('تست (رایگان)', callback_data='test')]]
                                  ))
        return self.start_select

    def start_register(self, bot, update):
        try:
            um = update.message
            message_id = um.message_id
            chat_id = um.chat_id
            admin = um.from_user.id

            text: str = um.text
            text = text.split()

            group_id: str = text[0]
            name: str = text[1]
            if group_id.startswith('-') and group_id[1:].isnumeric() and name.startswith('@'):
                channel = db.Channel(name=name, admin=admin, group_id=int(group_id), plan=3,
                                     expire=timedelta(days=7))
                db.add(channel)
                bot.send_message(chat_id=chat_id,
                                 text=strings.start_test_register_true,
                                 reply_to_message_id=message_id)
                return ConversationHandler.END
            else:
                bot.send_message(chat_id=chat_id,
                                 text=strings.start_test_register_false)
                return self.start_register
        except Exception as E:
            logging.error("start_register {}".format(E))

    def add_member(self, channel):
        try:
            current_date = JalaliDatetime().now().to_date()
            num = self.robot.get_chat_members_count(channel.name)
            member = db.Member(number=num, channel_name=channel.name, calendar=current_date)
            db.add(member)
        except Exception as E:
            logging.error('add_members {}'.format(E))

    @staticmethod
    def save(bot, update):
        try:
            um = update.message
            ue = update.edited_message
            message = None
            # edited
            if ue:
                from_gp = ue.chat_id
                msg_gp_id = ue.message_id
                channel = db.find('channel', group_id=from_gp)
                message: db.Message = db.find(table='message', msg_gp_id=msg_gp_id, gp_id=from_gp)
                if ue.text and message.sent:
                    text = editor.id_remove(text=ue.text, channel=channel)
                    bot.edit_message_text(chat_id=message.to_channel, message_id=message.msg_ch_id, text=text)
                    message.sent = message.ch_a = True
                    message.txt = text
                elif ue.caption and message.sent:
                    text = editor.id_remove(text=ue.caption, channel=channel)
                    bot.edit_message_caption(chat_id=message.to_channel, message_id=message.msg_ch_id, caption=text)
                    message.sent = message.ch_a = True
                    message.txt = text
                elif ue.text:
                    message.txt = ue.text
                    message.sent = message.ch_a = False
                elif ue.caption:
                    message.txt = ue.caption
                    message.sent = message.ch_a = False
                db.update(message)
            # regular
            elif um:
                channel: db.Channel = db.find(table='channel', group_id=um.chat_id)
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
                        file_id = um.video.file_id
                    elif um.animation:
                        kind = 'animation'
                        size = um.animation.file_size / (1024 * 1024)

                        if um.animation.mime_type in ('video/mp4', 'image/gif') and size < 10:
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
            logging.info("save {}".format(message.__str__()))
        except Exception as E:
            logging.error('save {}'.format(E))

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
                logging.info('edit_msg msg_ID_in_db {}'.format(message.id))

            # regular
            elif not message.ch_a:
                txt = editor.id_remove(text=message.txt, channel=channel)
                parse_mode = 'HTML' if message.other == 'url' else None

                if message.kind == 'text':
                    message.msg_ch_id = self.robot.send_message(chat_id=message.to_channel, text=txt,
                                                                parse_mode=parse_mode).message_id
                elif message.kind == 'video':
                    form = message.mime
                    dir_ = f"./vid/{channel.name}.{form}"
                    out = f'./vid/{channel.name}_out.mp4'

                    if message.size < 2:
                        self.robot.getFile(message.file_id).download(dir_, timeout=10)
                        txt = editor.vid_watermark(vid=dir_, out=out, kind=message.kind,
                                                   caption=message.txt, channel=channel)
                        try:
                            message.msg_ch_id = self.robot.send_video(chat_id=message.to_channel,
                                                                      video=open(out, 'rb'),
                                                                      caption=txt).message_id
                            os.remove(out)
                        except Exception as _:
                            message.msg_ch_id = self.robot.send_video(chat_id=message.to_channel,
                                                                      video=message.file_id,
                                                                      caption=txt).message_id
                    else:
                        txt = editor.id_remove(text=message.txt, channel=channel)
                        message.msg_ch_id = self.robot.send_video(chat_id=message.to_channel,
                                                                  video=message.file_id,
                                                                  caption=txt).message_id

                elif message.kind == 'photo':
                    dir_ = f"./image/{channel.name}.jpg"
                    out = f'./image/{channel.name}_out.jpg'
                    self.robot.getFile(message.file_id).download(dir_)
                    txt = editor.image_watermark(photo=dir_, out=out, caption=message.txt, channel=channel)
                    message.msg_ch_id = self.robot.send_photo(chat_id=message.to_channel, photo=open(out, 'rb'),
                                                              caption=txt).message_id
                    os.remove(out)

                elif message.kind == 'animation':
                    form = message.mime
                    dir_ = f"./gif/{channel.name}.{form}"
                    out = f'./gif/{channel.name}_out.mp4'

                    if message.size < 2:
                        self.robot.getFile(message.file_id).download(dir_, timeout=10)
                        txt = editor.vid_watermark(vid=dir_, out=out, kind=message.kind,
                                                   caption=message.txt, channel=channel)
                        try:
                            message.msg_ch_id = self.robot.send_animation(chat_id=message.to_channel,
                                                                          animation=open(out, 'rb'),
                                                                          caption=txt).message_id
                            os.remove(out)
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

                logging.info('send_to_ch message ID {}'.format(message.id))
                message.sent = True
                message.ch_a = True
                db.update(message)

        except IndexError:
            pass
        except AttributeError:
            pass
        except Exception as E:
            logging.error('send_to_ch attempt {} Error: {}'.format(attempt, E))
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

        dpa(MessageHandler(Filters.status_update.new_chat_members, self.send_info))

        # start
        dpa(ConversationHandler(entry_points=[CommandHandler(command='start',
                                                             callback=self.start,
                                                             filters=Filters.private)],
                                states={
                                    self.start_select: [CallbackQueryHandler(callback=self.start_select)],
                                    self.start_register: [CallbackQueryHandler(callback=self.start_register),
                                                          MessageHandler(filters=Filters.private,
                                                                         callback=self.start_register, )]
                                },
                                fallbacks=[CommandHandler(command='cancel',
                                                          callback=self.cancel)],
                                conversation_timeout=timedelta(hours=1)))

        # status
        dpa(ConversationHandler(entry_points=[CommandHandler(command='status',
                                                             callback=self.status,
                                                             filters=Filters.private)],
                                states={
                                    self.setting: [CallbackQueryHandler(self.setting)],
                                    self.select: [CallbackQueryHandler(self.select)],
                                    self.step2: [CallbackQueryHandler(self.step2)],
                                    self.done: [CallbackQueryHandler(self.done)],
                                    self.graph: [CallbackQueryHandler(self.graph)],
                                    self.set_pos: [CallbackQueryHandler(self.set_pos)],
                                    self.set_logo: [MessageHandler(filters=Filters.private, callback=self.set_logo)]
                                },
                                fallbacks=[CommandHandler(command='cancel',
                                                          callback=self.cancel)],
                                conversation_timeout=timedelta(hours=1)))

        # delay
        dpa(ConversationHandler(entry_points=[CommandHandler(command='delay',
                                                             callback=self.set_interval,
                                                             filters=Filters.private,
                                                             pass_args=True)],
                                states={
                                    self.done: [CallbackQueryHandler(callback=self.done)]
                                },
                                fallbacks=[CommandHandler(command='cancel',
                                                          callback=self.cancel)],
                                conversation_timeout=timedelta(hours=1)))

        dpa(MessageHandler(filters=Filters.group, callback=self.save, edited_updates=True))

        first = 60 - JalaliDatetime().now().second
        job.run_repeating(callback=self.task, interval=60, first=first)

        print('started')
        self.updater.idle()


timer = SSP('410818874:AAEU8gHdOmurgJBf_N_p-58qVW94Rc_vgOc')
timer.run()
