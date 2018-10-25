from telegram.ext import Updater, MessageHandler, CommandHandler, Filters, ConversationHandler, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton as Inline
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
from khayyam3.tehran_timezone import JalaliDatetime, timedelta
from khayyam3 import JalaliDate
from datetime import datetime
from PIL import Image
import numpy as np
import matplotlib
import telegram
import database
import logging
import psutil
import pytz
import time
# import var
import re
import os

matplotlib.use('AGG', force=True)
import matplotlib.pyplot as plt

sina, lili = 103086461, 303962908
logging.basicConfig(filename='report.log', level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s')


# noinspection PyBroadException
class SSP:
    def __init__(self, token):
        self.robot = telegram.Bot(token)
        self.updater = Updater(token)
        try:
            for i in ['vid', 'plot', 'logo', 'image']:
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

    def time_is_in(self, now, channel: database.Channel):
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

    def entry(self, bot, update):
        try:
            um = update.message
            admin = um.from_user.id
            channels = database.find('channel', admin=admin)
            if channels:
                if len(channels) == 1:
                    channel = channels[0]
                    chat_id = um.chat_id
                    message_id = um.message_id
                    expire = JalaliDatetime().from_datetime(channel.expire).strftime("%x")

                    bot.send_message(chat_id=chat_id,
                                     text=(f'میزان وقفه ⏳= {channel.interval}\n'
                                           f'ساعت توقف 🕰= {channel.bed}\n'
                                           f'ساعت شروع 🕰= {channel.wake}\n\n'
                                           f'اعتبار شما تا {expire}'),
                                     reply_to_message_id=message_id,
                                     reply_markup=InlineKeyboardMarkup(
                                         [[Inline('وقفه', callback_data=f'interval;{channel.name}'),
                                           Inline('ساعت توقف', callback_data=f'bed;{channel.name}'),
                                           Inline('ساعت شروع', callback_data=f'wake;{channel.name}')],
                                          [Inline('مشاهده نمودار', callback_data=f"graph;{channel.name}"),
                                           Inline('تنظیم لوگو', callback_data=f"logo;{channel.name}")],
                                          ]
                                     ))
                    return self.select

                elif len(channels) > 1:
                    print(channels)
                    lst = [[Inline(i.name, callback_data=f"_;{i.name}")] for i in channels]
                    bot.send_message(chat_id=admin,
                                     text="شما صاحب چندین کانال هستید\nمایل به مشاهده تنظیمات کدام یک هستید؟",
                                     reply_markup=InlineKeyboardMarkup(lst))
                    return self.setting

        except Exception as E:
            logging.error("entry {}".format(E))

    def setting(self, bot, update):
        try:
            if update.callback_query:
                data: str = update.callback_query.data
                admin, name = data.split(';')
                if not admin == '_':
                    channel = database.find("channel", admin=admin, name=name)
                else:
                    channel = database.find('channel', name=name)
                chat_id = update.callback_query.message.chat_id
                message_id = update.callback_query.message.message_id
                expire = JalaliDatetime().from_datetime(channel.expire).strftime("%x")

                bot.edit_message_text(chat_id=chat_id,
                                      text=(f'میزان وقفه ⏳= {channel.interval}\n'
                                            f'ساعت توقف 🕰= {channel.bed}\n'
                                            f'ساعت شروع 🕰= {channel.wake}\n\n'
                                            f'اعتبار شما تا {expire}'),
                                      message_id=message_id,
                                      reply_markup=InlineKeyboardMarkup(
                                          [[Inline('وقفه', callback_data=f'interval;{channel.name}'),
                                            Inline('ساعت توقف', callback_data=f'bed;{channel.name}'),
                                            Inline('ساعت شروع', callback_data=f'wake;{channel.name}')],
                                           [Inline('مشاهده نمودار', callback_data=f"graph;{channel.name}"),
                                            Inline('تنظیم لوگو', callback_data=f"logo;{channel.name}")],
                                           ]
                                      ))
                return self.select
            else:
                um = update.message
                admin = um.from_user
                channel: database.Channel = database.find('channel', admin=admin)

                bot.send_message(chat_id=admin.id,
                                 text=(f'میزان وقفه ⏳= {channel.interval}\n'
                                       f'ساعت توقف 🕰= {channel.bed}\n'
                                       f'ساعت شروع 🕰= {channel.wake}\n'),
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
            if data[0] == 'interval':
                lst = [[Inline('01M', callback_data='01m')]]
                for i in range(5, 60, 5):
                    lst.append(
                        [Inline("{}M".format(str(i).zfill(2)), callback_data=f"{str(i).zfill(2)}m;{data[1]}")])
                for i in range(0, 25):
                    lst.append(
                        [Inline("{}H".format(str(i).zfill(2)), callback_data=f'{str(i).zfill(2)}h;{data[1]}')])
                lst = np.array(lst).reshape((-1, 6)).tolist()
                lst.append([Inline('بازگشت به منوی تنظیمات', callback_data=f'setting;{data[1]}')])
                self.robot.edit_message_text(chat_id=um.message.chat_id,
                                             message_id=um.message.message_id,
                                             text="گام اول:\n"
                                                  "زمانبدی مورد نظر خود را انتخاب کنید\n تنها درصورتی که مایل "
                                                  "به تغییر دقایق به صورت دلخواه هستید "
                                                  "برای مثال:\n"
                                                  "13m -> برابر با هر 13 دقیقه\n"
                                                  "از این روش استفاده کنید:\n"
                                                  "/delay 13m @name-e-channel"
                                                  "\n اگر دچار مشکلی شده اید از ما کمک بگیرید\n"
                                                  "@s_for_cna",
                                             reply_markup=InlineKeyboardMarkup(lst))
                return self.step2
            elif data[0] == 'wake':
                lst = []
                for i in range(1, 25):
                    lst.append([Inline('{}:00'.format(str(i).zfill(2)), callback_data=f"{str(i).zfill(2)}w;{data[1]}")])
                lst = np.array(lst).reshape((6, -1)).tolist()
                lst.append([Inline('بازگشت به منوی تنظیمات', callback_data=f'setting;{data[1]}')])
                self.robot.edit_message_text(chat_id=um.message.chat_id,
                                             message_id=um.message.message_id,
                                             text="بات از چه ساعتی شروع به کار کند؟",
                                             reply_markup=InlineKeyboardMarkup(lst))
                return self.done
            elif data[0] == 'bed':
                lst = []
                for i in range(1, 25):
                    lst.append([Inline('{}:00'.format(str(i).zfill(2)), callback_data=f"{str(i).zfill(2)}b;{data[1]}")])
                lst = np.array(lst).reshape((6, -1)).tolist()
                lst.append([Inline('بازگشت به منوی تنظیمات', callback_data=f'setting;{data[1]}')])
                self.robot.edit_message_text(chat_id=um.message.chat_id,
                                             message_id=um.message.message_id,
                                             text="بات در چه ساعتی خاموش شود؟",
                                             reply_markup=InlineKeyboardMarkup(lst))
                return self.done
            elif data[0] == 'graph':
                self.robot.edit_message_text(chat_id=um.message.chat_id,
                                             message_id=um.message.message_id,
                                             text="نمودار در چه بازه زمانی باشد؟",
                                             reply_markup=InlineKeyboardMarkup(
                                                 [[Inline('یک هفته', callback_data=f"1w;{data[1]}"),
                                                   Inline('یک ماه', callback_data=f"1m;{data[1]}"),
                                                   Inline('یک سال', callback_data=f"1y;{data[1]}")]]
                                             ))
                return self.graph
            elif data[0] == 'logo':
                self.robot.edit_message_text(chat_id=um.message.chat_id,
                                             message_id=um.message.message_id,
                                             text="یک عکس با فرمت png بدون پس زمینه برام بفرست در ابعاد مربع\n"
                                                  "اگر نمیتونی یا بلد نیستی اینکار رو بکنی"
                                                  " میتونم از اسم کانال به عنوان لوگو استفاده کنم",
                                             reply_markup=InlineKeyboardMarkup(
                                                 [[Inline('استفاده از نام کانال', callback_data=f"logo;{data[1]}")]]))
                return self.set_logo
        except Exception as E:
            logging.error("select {}".format(E))

    def step2(self, _, update):
        if update.callback_query:
            um = update.callback_query
            data: str = um.data.split(';')
            interval: str = data[0]
            ch_name: str = data[1]

            if interval.endswith('m'):
                interval: int = int(interval[:-1])
                if 1 < interval <= 30:
                    self.robot.edit_message_text(chat_id=um.message.chat_id,
                                                 message_id=um.message.message_id,
                                                 text="گام دوم:\n"
                                                      "1️⃣ پیام ها هر {0} دقیقه ارسال شوند. برای مثال بصورت 01:{0}, "
                                                      "01:{1} و ...\n"
                                                      "2️⃣ پیام ها وقتی دقیقه شمار برابر {0} است ارسال شوند برای مثال "
                                                      "01:{0}, 02:{0}, 03:{0} و ...\n"
                                                      "کدام یک مورد پسند شماست؟\n"
                                                      "از ما کمک بگیرید:\n"
                                                      "@s_for_cna".format(
                                                     str(interval).zfill(2), str(interval * 2).zfill(2)),
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

                channel: database.Channel = database.find('channel', name=channel_name)

                if part1 == '_':
                    pass
                elif part1.endswith('b'):
                    bed = part1[:-1]
                    channel.bed = bed
                    database.update(channel)
                elif part1.endswith('w'):
                    wake = part1[:-1]
                    channel.wake = wake
                    database.update(channel)
                else:
                    interval = part1
                    channel.interval = interval
                    database.update(channel)

                self.robot.edit_message_text(chat_id=chat_id,
                                             message_id=message_id,
                                             text=f'تغییرات اعمال شد\n'
                                                  f'میزان وقفه ⏳= {channel.interval}\n'
                                                  f'ساعت توقف 🕰= {channel.bed[:-1]}:00\n'
                                                  f'ساعت شروع 🕰= {channel.wake[:-1]}:00\n',
                                             reply_markup=InlineKeyboardMarkup(
                                                 [[Inline('وقفه', callback_data='interval;{}'.format(channel.name)),
                                                   Inline('ساعت توقف', callback_data='bed;{}'.format(channel.name)),
                                                   Inline('ساعت شروع', callback_data='wake;{}'.format(channel.name))],
                                                  [Inline('مشاهده نمودار', callback_data=f"graph;{channel.name}"),
                                                   Inline('تنظیم لوگو', callback_data=f"logo;{channel.name}")]]))
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

                out = database.find('member', admin=admin, name=ch_name, from_=from_, til=now)

                y = out[:, 0]
                y = np.append(y, self.robot.get_chat_members_count(ch_name))
                x = np.arange(len(y))

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
                diff = np.mean(np.diff(y), dtype=int)
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
                mime = um.document.mime_type
                size = um.document.file_size
                name = um.caption
                if mime == 'image/png' and size < 80000:
                    channel = database.find("channel", admin=chat_id, name=name)
                    self.robot.get_file(file_id=file_id).download(f'logo/{name}.png')
                    channel.logo = True
                    database.update(channel)
                    lst = []
                    for i in range(1, 10):
                        lst.append([Inline(str(i), callback_data=f"{i};{name}")])
                    lst = np.array(lst).reshape((3, 3)).tolist()
                    lst.append([Inline('هیچکدام', callback_data=f'0;{name}')])

                    self.robot.send_photo(chat_id=chat_id,
                                          reply_to_message_id=um.message_id,
                                          photo=open('info.png', 'rb'),
                                          caption='خب لوگو تایید شد. محل پیش فرض قرارگیری لوگو رو حالا انتخاب کن\n'
                                                  'اگر میخوای بصورت پیش فرض لوگو روی عکس ها و گیف ها گذاشته نشه '
                                                  '"هیچکدام" رو انتخاب کن\n'
                                                  'پشتیبانی\n'
                                                  '@s_for_cna',
                                          reply_markup=InlineKeyboardMarkup(lst))

                    return self.set_pos
        except Exception as E:
            logging.error("set_logo {}".format(E))

    def set_pos(self, _, update):
        try:
            um = update.callback_query
            admin = um.message.chat_id
            data = um.data
            pos, name = data.split(';')
            channel = database.find("channel", admin=admin, name=name)
            channel.pos = int(pos)
            database.update(channel)
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
                    channel = database.find('channel', name=ch_name, admin=admin.id)
                    if channel:
                        if interval.endswith('m') and interval[:-1].isdigit():
                            interval = int(interval[:-1])
                            if 1 < interval <= 30:
                                self.robot.send_message(chat_id=um.chat_id,
                                                        reply_to_message_id=um.message_id,
                                                        text="گام دوم:\n"
                                                             "1️⃣ پیام ها هر {0} دقیقه ارسال شوند. برای مثال بصورت 01:{0}, "
                                                             "01:{1} و ...\n"
                                                             "2️⃣ پیام ها وقتی دقیقه شمار برابر {0} است ارسال شوند برای مثال "
                                                             "01:{0}, 02:{0}, 03:{0} و ...\n"
                                                             "کدام یک مورد پسند شماست؟\n"
                                                             "از ما کمک بگیرید:\n"
                                                             "@s_for_cna".format(
                                                            str(interval).zfill(2), str(interval * 2).zfill(2)),
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

    def state(self, bot, update, args):
        try:
            admin = update.message.from_user
            if args:
                name = args[0]
                channel: database.Channel = database.find('channel', admin=admin, name=name)
            else:
                channel: database.Channel = database.find('channel', admin=admin)
            if channel:
                bot.send_message(chat_id=update.message.chat_id,
                                 text='<b>delay =</b> {}\n<b>bed =</b> {}\n<b>wake = </b>{}\nremaining: {}'.format(
                                     channel.interval, channel.bed, channel.wake, self.remain(admin, channel.name)),
                                 parse_mode='HTML')
            logging.info("/state by {}".format(update.message.from_user))
        except Exception as E:
            logging.error("/state {} by {}".format(E, update.message.from_user))

    def remain(self, admin, channel):
        try:
            remaining = database.remain(channel.name)
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

    def add_member(self):
        try:
            channels = [channel.channel_id for channel in database.find('channel')]
            current_date = JalaliDatetime().now()
            for channel_name in channels:
                num = self.robot.get_chat_members_count(channel_name)
                member = database.Member(number=num, channel_name=channel_name, calendar=current_date)
                database.add(member)
            self.robot.send_document(document=open('bot_db.db', 'rb'),
                                     caption=current_date.strftime("%x"),
                                     chat_id=sina)
            logging.info('members{}'.format(', '.join(channels)))
        except Exception as E:
            logging.error('add members {}'.format(E))

    @staticmethod
    def id_remove(entry, channel_name):
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
                if state.lower() not in (channel_name,):
                    entry = re.sub(state, channel_name, entry)
            if entry.lower().strip()[len(channel_name) * (-2):].find(channel_name) == -1:
                entry = entry + '\n' + channel_name
            return entry
        else:
            return entry + '\n' + channel_name

    def image_watermark(self, photo, caption, channel_name) -> str:
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
                caption = self.id_remove(re.sub(pattern, '', caption), channel_name)
            else:
                caption = self.id_remove(caption, channel_name)
            return caption
        except Exception as E:
            logging.error("put {}".format(E))

    def gif_watermark(self, gif, format_, caption, channel_name) -> str:
        try:
            caption = str(caption)
            file = 'vid/tmp.' + format_
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
                caption = self.id_remove(re.sub(pattern, '', caption), channel_name)
            else:
                caption = self.id_remove(caption, channel_name)
            return caption
        except Exception as E:
            logging.error('vid_watermark {}'.format(E))

    def save(self, bot, update):
        try:
            um = update.message
            ue = update.edited_message
            if ue:
                from_gp = ue.chat_id
                msg_gp_id = ue.message_id
                channel = database.find('channel', group_id=from_gp)
                message: database.Message = database.find(table='message', msg_gp_id=msg_gp_id, gp_id=from_gp)
                if ue.text and message.sent:
                    text = self.id_remove(entry=ue.text, channel_name=channel.name)
                    bot.edit_message_text(chat_id=message.to_ch, message_id=message.msg_ch_id, text=text)
                    message.sent = message.ch_a = True
                    message.txt = text
                elif ue.caption and message.sent:
                    text = self.id_remove(entry=ue.caption, channel_name=channel.name)
                    bot.edit_message_caption(chat_id=message.to_ch, message_id=message.msg_ch_id, caption=text)
                    message.sent = message.ch_a = True
                    message.txt = text
                elif ue.text:
                    message.txt = ue.text
                    message.sent = message.ch_a = False
                elif ue.caption:
                    message.txt = ue.caption
                    message.sent = message.ch_a = False
                database.update(message)
            elif um:
                channel: database.Channel = database.find(table='channel', group_id=um.chat_id)
                if um.text:
                    message = database.Message(from_gp=um.chat_id, to_ch=channel.name,
                                               kind='text', msg_gp_id=um.message_id, txt=um.text)
                    database.add(message)
                else:
                    text = um.caption if um.caption else ''
                    file_id = kind = other = None
                    if um.photo:
                        kind = 'photo'
                        file_id = um.photo[-1].file_id
                    elif um.video:
                        kind = 'video'
                        file_id = um.video.file_id
                    elif um.animation:
                        kind = 'animation'
                        if um.animation.mime_type in (
                                'video/mp4', 'image/gif') and um.animation.file_size / 1000000 < 10:
                            other = str(um.document.mime_type).split('/')[1]
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

                    message = database.Message(from_gp=um.chat_id, to_ch=channel.name, msg_gp_id=um.message_id,
                                               kind=kind, txt=text, file_id=file_id, other=other)
                    database.add(message)

        except Exception as E:
            logging.error('save {}'.format(E))

    def send_to_ch(self, channel, attempt=0):
        message = database.get_last_msg(channel_name=channel.name)
        try:
            txt = self.id_remove(message.txt, channel.name)

            # edited
            if message.ch_a and not message.sent:
                if message.kind == 'text':
                    message.msg_ch_id = self.robot.edit_message_text(chat_id=message.to_ch, text=txt,
                                                                     message_id=message.msg_ch_id)
                else:
                    message.msg_ch_id = self.robot.edit_message_caption(chat_id=message.to_ch, caption=txt,
                                                                        message_id=message.msg_ch_id)

                database.update(message)
                logging.info('edit_msg msg_ID_in_db {}'.format(message.id))

            # regular
            elif not message.sent or not message.ch_a:

                if message.kind == 'text':
                    message.msg_ch_id = self.robot.send_message(chat_id=message.to_ch, text=txt).message_id

                elif message.kind == 'video':
                    # TODO set logo on videos
                    message.msg_ch_id = self.robot.send_video(chat_id=message.to_ch, video=message.file_id, caption=txt)

                elif message.kind == 'photo':
                    txt = self.image_watermark(photo=message.file_id, caption=message.txt, channel_name=message.to_ch)
                    message.msg_ch_id = self.robot.send_photo(chat_id=message.to_ch, photo=open('image/out.jpg', 'rb'),
                                                              caption=txt).message_id
                    os.remove('./image/out.jpg')

                elif message.kind == 'animation':
                    form = message.other
                    txt = self.gif_watermark(gif=message.file_id, format_=form, caption=message.txt,
                                             channel_name=message.to_ch)
                    message.msg_ch_id = self.robot.send_animation(chat_id=message.to_ch,
                                                                  animation=open('vid/out.mp4', 'rb'),
                                                                  caption=txt).message_id
                    os.remove('./vid/out.mp4')

                elif message.kind == 'audio':
                    message.msg_ch_id = self.robot.send_audio(chat_id=message.to_ch, audio=message.file_id,
                                                              caption=txt).message_id
                elif message.kind == 'document':
                    message.msg_ch_id = self.robot.send_document(chat_id=message.to_ch, document=message.file_id,
                                                                 caption=txt).message_id
                elif message.kind == 'v_note':
                    message.msg_ch_id = self.robot.send_video_note(chat_id=message.to_ch,
                                                                   video_note=message.file_id).message_id
                elif message.kind == 'voice':
                    message.msg_ch_id = self.robot.send_voice(chat_id=message.to_ch, voice=message.file_id,
                                                              caption=txt).message_id
                elif message.kind == 'sticker':
                    message.msg_ch_id = self.robot.send_sticker(chat_id=message.to_ch, sticker=message.file_id,
                                                                caption=txt).message_id

                logging.info('send_to_ch message ID {}'.format(message.id))
                message.sent = True
                message.ch_a = True
                database.update(message)
        except IndexError:
            pass
        except AttributeError:
            pass
        except Exception as E:
            logging.error('send_to_ch attempt {} Error: {}'.format(attempt, E))
            if attempt == 3:
                database.update(message)

    def task(self, bot, _):
        try:
            now = JalaliDatetime().now()
            channels = database.find('channel')

            if now.hour == now.minute == 0:
                self.add_member()

            if now.minute == 0:
                bot.send_message(chat_id=sina, text=str(psutil.virtual_memory()[2]))

            for channel in channels:
                if self.time_is_in(now=now, channel=channel):
                    self.send_to_ch(channel=channel)

        except Exception as E:
            logging.error('Task {}'.format(E))

    def send_info(self, _, update):
        try:
            um = update.message
            if len(list(um.new_chat_members)) > 0:
                chat_member = um.new_chat_members[0]
                channels = database.find('channel', admin=um.from_user.id)

                if chat_member.id == 410818874:

                    if um.chat.type == 'supergroup' and um.chat_id in [i.group_id for i in channels]:
                        self.robot.send_message(chat_id=um.chat_id, text="تبریک، بات با موفقیت در گروه ثبت شد")
                    else:
                        self.robot.send_message(chat_id=um.chat_id, text=um.chat_id)
                        self.robot.leave_chat(um.chat_id)
        except Exception as E:
            print(E)

    def start(self):
        dpa = self.updater.dispatcher.add_handler
        job = self.updater.job_queue
        self.updater.start_polling()

        dpa(MessageHandler(Filters.status_update.new_chat_members, self.send_info))
        dpa(CommandHandler('state', self.state, Filters.private))
        dpa(ConversationHandler(entry_points=[CommandHandler(command='status',
                                                             callback=self.entry,
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
                                                          callback=self.cancel)]))

        dpa(ConversationHandler(entry_points=[CommandHandler(command='delay',
                                                             callback=self.set_interval,
                                                             filters=Filters.private,
                                                             pass_args=True)],
                                states={self.done: [CallbackQueryHandler(callback=self.done)]},
                                fallbacks=[CommandHandler('cancel', self.cancel)]))

        dpa(MessageHandler(filters=Filters.group, callback=self.save, edited_updates=True))

        first = 60 - JalaliDatetime().now().second
        job.run_repeating(callback=self.task, interval=60, first=first)

        print('started')

        self.updater.idle()


timer = SSP('410818874:AAEU8gHdOmurgJBf_N_p-58qVW94Rc_vgOc')
timer.start()
