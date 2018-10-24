from telegram.ext import Updater, MessageHandler, CommandHandler, Filters, ConversationHandler, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton as Inline
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
from khayyam import JalaliDate, JalaliDatetime
from datetime import datetime, timedelta
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


class SSP:
    def __init__(self, token):
        self.robot = telegram.Bot(token)
        self.updater = Updater(token)

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
        if interval.endswith('m'):
            interval: int = int(interval[:-1])
            interval = tuple(range(interval, 61, interval))

            if now.minute in interval and not self.sleep(bed=channel.bed, wake=channel.wake):
                return True

        elif interval.endswith('h'):
            interval: int = int(interval[:-1])
            interval = [datetime.strptime(str(i), '%H00') for i in range(channel.wake, interval, channel.bed)]
            if now.strftime('%H%M') in interval and not self.sleep(bed=channel.bed, wake=channel.wake):
                return True
        else:
            interval: list = interval.split(';')
            if now.strftime('%H%M') in interval and not self.sleep(bed=channel.bed, wake=channel.wake):
                return True
        return False

    # region status
    def entry(self, bot, update):
        try:
            name = None
            um = update.message
            admin = um.from_user.id
            channels = database.find('channel', admin=admin)
            if channels:
                if len(channels) == 1 and not name:
                    return self.setting

                elif len(channels) > 1:
                    lst = [[Inline(i.name, callback_data=f"_;{i.name}")] for i in channels]
                    bot.send_message(chat_id=admin,
                                     text="شما صاحب چندین کانال هستید\nمایل به مشاهده تنظیمات کدام یک هستید؟",
                                     reply_markup=InlineKeyboardMarkup(lst))
                    return self.setting

        except Exception as E:
            logging.error("setting {}".format(E))

    def setting(self, bot, update):
        try:
            if update.callback_query:
                data: str = update.callback_query.data
                _, name = data.split(';')
                channel = database.find('channel', name=name)
                chat_id = update.callback_query.message.chat_id
                message_id = update.callback_query.message.message_id

                bot.edit_message_text(chat_id=chat_id,
                                      text=(f'میزان وقفه ⏳= {channel.interval}\n'
                                            f'ساعت توقف 🕰= {channel.bed}\n'
                                            f'ساعت شروع 🕰= {channel.wake}\n\n'
                                            f'اعتبار شما = {channel.expire}'),
                                      message_id=message_id,
                                      reply_markup=InlineKeyboardMarkup(
                                          [[Inline('وقفه', callback_data=f'interval;{channel.name}'),
                                            Inline('ساعت توقف', callback_data=f'bed;{channel.name}'),
                                            Inline('ساعت شروع', callback_data=f'wake;{channel.name}')],
                                           [Inline('مشاهده نمودار', callback_data=f"graph;{channel.name}"),
                                            Inline('')]
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
                                     [[Inline('وقفه', callback_data='interval;{}'.format(channel.name)),
                                       Inline('ساعت توقف', callback_data='bed;{}'.format(channel.name)),
                                       Inline('ساعت شروع', callback_data='wake;{}'.format(channel.name))],
                                      ]
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
                for i in range(0, 24):
                    lst.append(
                        [Inline("{}H".format(str(i).zfill(2)), callback_data=f'{str(i).zfill(2)}h;{data[1]}')])
                lst = np.array(lst).reshape((-1, 6)).tolist()
                lst.append([Inline('بازگشت به منوی تنظیمات', callback_data=f'setting;{data[1]}')])
                self.robot.edit_message_text(chat_id=um.message.chat_id,
                                             message_id=um.message.message_id,
                                             text="گام اول:\nزمانبدی مورد نظر خود را انتخاب کنید\n تنها درصورتی که مایل "
                                                  "به تغییر دقایق به صورت دلخواه هستید "
                                                  "برای مثال:\n"
                                                  "13m -> برابر با هر 13 دقیقه\n"
                                                  "از دستور /delay"
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
            um = update.callback_query
            data: str = um.data
            part1, channel_name = data.split(';')
            chat_id = um.message.chat_id
            message_id = um.message.message_id

            channel: database.Channel = database.find('channel', name=channel_name)
            if part1 == '_':
                pass
            elif part1.endswith('b'):
                bed = part1
                channel.bed = bed
                database.update(channel)
            elif part1.endswith('w'):
                wake = part1
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
                                              ]
                                         ))
            return self.select
        except Exception as E:
            logging.error("done {}".format(E))

    # endregion

    @staticmethod
    def set_interval(bot, update, args):
        try:
            admin = update.message.from_user
            channel = database.find('channel', admin=admin)
            if channel:
                if len(channel) == 1:
                    if args and str(args[0][:-1]).isdecimal():
                        if 1 <= int(str(args[0])[:-1]) < 60:
                            channel.interval = str(args[0])
                            database.update(channel)
                            bot.send_message(chat_id=update.message.chat_id,
                                             text='delay = <b>{}</b> minute'.format(args[0]),
                                             parse_mode='HTML')
        except Exception as _:
            bot.send_message(chat_id=update.message.chat_id, text='اشتباه: یک عدد صحیح بین ۱ تا ۵۹ بفرستید')

    @staticmethod
    def set_bed(bot, update, args):
        try:
            admin = update.message.from_user
            channel: database.Channel = database.find('channel', admin=admin)
            if channel:
                if args:
                    bed = int(str(args[0]))
                    if 0 <= bed < 24:
                        channel.bed = bed
                        database.update(channel)
                        bot.send_message(chat_id=update.message.chat_id, parse_mode='HTML',
                                         text='<b>bed</b> time starts from <b>{}</b>'.format(str(args[0]) + ':00'))
        except Exception as _:
            bot.send_message(chat_id=update.message.chat_id, text='ERROR')

    @staticmethod
    def set_wake(bot, update, args):
        try:
            admin = update.message.from_user
            channel: database.Channel = database.find('channel', admin=admin)
            if channel:
                if args:
                    wake = int(str(args[0]))
                    if 0 <= wake < 24:
                        channel.wake = wake
                        database.update(channel)
                        bot.send_message(chat_id=update.message.chat_id, parse_mode='HTML',
                                         text='<b>wake</b> time starts from <b>{}</b>'.format(str(args[0]) + ':00'))
        except Exception as _:
            bot.send_message(chat_id=update.message.chat_id, text='ERROR')

    @staticmethod
    def state(bot, update):
        try:
            admin = update.message.from_user
            channel: database.Channel = database.find('channel', admin=admin)
            if channel:
                bot.send_message(chat_id=update.message.chat_id,
                                 text='<b>delay =</b> {}\n<b>bed =</b> {}\n<b>wake = </b>{}'.format(
                                     channel.interval, channel.bed, channel.wake),
                                 parse_mode='HTML')
            logging.info("/state by {}".format(update.message.from_user))
        except Exception as E:
            logging.error("/state {} by {}".format(E, update.message.from_user))

    def remain(self, user, channel):
        try:
            remaining = database.remain(channel.name)
            # channel = database.find('channel', name=channel_name)
            step = self.current_time()[0]
            rem = remaining

            while remaining > 0:
                # todo not gonna work, fix it
                if self.sleep(step, bed=channel.bed, wake=channel.wake):
                    step += timedelta(hours=channel.wake / 10000 - step.hour)
                if step.minute in channel.interval and not step.minute == 0:
                    remaining -= 1
                step += timedelta(minutes=1)

            logging.info("remain by {}".format(user.first_name))
            if rem > 0:
                return rem, step.strftime('%y-%m-%d -> %H:%M')
            else:
                return 0, 0

            if not remaining == 0:
                text = 'پیام های باقیمانده {} کانال تا {} تامین خواهد بود'.format(remaining, date)
            else:
                text = 'هیچ پیامی در صف نیست'
        except Exception as E:
            logging.error("Could't get remaining time by {} Error: {}".format(user.first_name, E))

    def cancel(self, _, update):
        return ConversationHandler.END

    # @staticmethod
    # def _before(year=None, months=None, plot='plot') -> list:
    #     out = None
    #     if year and months:
    #         before = JalaliDate().strptime(year + months, '%Y%m') - timedelta(days=1)
    #         if plot == 'plot':
    #             out = [db_connect.execute("SELECT * FROM Mem_count WHERE ddd = '{}'".format(str(before))).fetchone()]
    #             out.extend([i for i in db_connect.execute(
    #                 "SELECT * FROM Mem_count WHERE ddd LIKE '{}-{}%'".format(year, months)).fetchall()])
    #         elif plot == 'pie':
    #             out = [i[0] for i in db_connect.execute(
    #                 "SELECT from_ad FROM Queue WHERE ch_a=1 AND out_date LIKE '{}-{}%'".format(
    #                     year, months)).fetchall()]
    #     return out

    # def report_members(self, bot, update, args):
    #     try:
    #         param = days = out = months = year = title = plus = predict = None
    #         if args:
    #             param = str(args[0]).lower()
    #             year_month = re.compile(r"(?P<year>\d{,4})-(?P<month>\d{,2})")
    #             if re.fullmatch(r'd\d*', param):
    #                 days = param[1:]
    #                 out = [i for i in
    #                        db_connect.execute("SELECT * FROM Mem_count ORDER BY ID DESC LIMIT {}".format(days))]
    #                 out = [j for j in reversed(out)]
    #                 title = '{} days'.format(days)
    #                 plus = True
    #             elif re.fullmatch(r'm\d{,2}', param):
    #                 months = param[1:].zfill(2)
    #                 year = self.current_time()[0][:4]
    #                 out = self._before(year, months)
    #                 title = 'graph of {}-{}'.format(year, months)
    #                 if year + months == str(self.current_time()[0].replace('-', '')[:6]):
    #                     plus = predict = True
    #             elif re.fullmatch(r'y\d{,2}', param):
    #                 year = '13' + param[1:] if len(param) == 3 else param[1:]
    #                 out = [i for i in db_connect.execute("SELECT * FROM Mem_count WHERE ddd LIKE '{}%'".format(year))]
    #                 title = 'graph of {}'.format(year)
    #                 if year == self.current_time()[0][:4]:
    #                     plus = True
    #             elif re.fullmatch(year_month, param):
    #                 date = re.fullmatch(year_month, param)
    #                 year = '13' + date.group('year') if len(date.group('year')) == 2 else date.group('year')
    #                 months = date.group('month')
    #                 out = self._before(year, months)
    #                 title = 'graph of 20{}-{}'.format(year, months)
    #                 if year + months == ''.join(self.current_time()[0].split('-'))[:6]:
    #                     plus = True
    #         else:
    #             out = db_connect.execute("SELECT * FROM Mem_count").fetchall()
    #             title = "starts from {}".format(out[0][1])
    #             plus = True
    #         if out:
    #             members = [i for i in [j[3] for j in out]]
    #             balance = [i for i in [j[2] for j in out]]
    #             average = sum(balance) / len(balance)
    #             caption = '{}\nbalance = {}\naverage = {:.2f}\nfrom {} till {}'.format(
    #                 title, members[-1] - members[0], average, members[0], members[-1])
    #             if plus:
    #                 now = self.robot.get_chat_members_count(self.channel_name)
    #                 balance.append(now - members[-1])
    #                 members.append(now)
    #                 average = sum(balance) / len(balance)
    #                 caption = '{}\nbalance = {}\naverage = {:.2f}\nfrom {} till {}'.format(
    #                     title, members[-1] - members[0], average, members[0], members[-1])
    #                 days_of_this_month = JalaliDatetime.now().daysinmonth
    #                 if predict and not (average * (days_of_this_month - len(members))) <= 0:
    #                     pdt = int(members[-1] + (average * (days_of_this_month - len(members))))
    #                     caption += '\npredict of month = {}'.format(pdt)
    #                 plt.plot(range(1, len(members) + 1), members, marker='o', label='now', color='red', markersize=4)
    #                 plt.plot(range(1, len(members)), members[:-1], marker='o', label='members', color='blue',
    #                          markersize=4)
    #             else:
    #                 plt.plot(range(1, len(members) + 1), members, marker='o', label='members', color='blue',
    #                          markersize=4)
    #             plt.grid()
    #             plt.xlim(1, )
    #             plt.xlabel('days')
    #             plt.ylabel('members')
    #             plt.title(title)
    #             plt.legend(loc=4)
    #             plt.savefig('plot/plot.png')
    #             bot.send_photo(chat_id=update.message.chat_id, photo=open('plot/plot.png', 'rb'), caption=caption)
    #             plt.close()
    #         logging.info('plot:: args {} -- by: {}'.format(args, update.message.from_user))
    #     except TimeoutError:
    #         pass
    #     except Exception as E:
    #         self.robot.send_message(chat_id=update.message.chat_id,
    #                                 text='**ERROR {}**'.format(update.message.text),
    #                                 parse_mode='Markdown')
    #         logging.error("Could't get plot:: args {} -- {} - by: {}".format(args, E, update.message.from_user))
    #
    # def report_admins(self, bot, update, args):
    #     try:
    #         param = out = title = None
    #         if args:
    #             pattern = re.compile(r"(?P<year>\d{,4})-(?P<month>\d{,2})")
    #             param = str(args[0]).lower()
    #             if re.fullmatch(r'm\d{,2}', param):
    #                 months = param[1:].zfill(2)
    #                 year = self.current_time()[0][:4]
    #                 out = self._before(year, months, plot='pie')
    #                 title = 'graph of {}-{}'.format(year, months)
    #             elif re.fullmatch(pattern, param):
    #                 date = re.fullmatch(pattern, param)
    #                 year = '13' + date.group('year') if len(date.group('year')) == 2 else date.group('year')
    #                 months = date.group('month').zfill(2)
    #                 out = self._before(year, months, plot='pie')
    #                 title = 'graph of {}-{}'.format(year, months)
    #         else:
    #             out = [i[0] for i in db_connect.execute("SELECT from_ad FROM Queue WHERE ch_a=1").fetchall()]
    #             title = 'graph of all time'
    #         tmp = set(out.copy())
    #         admins = {}
    #         for i in tmp:
    #             admins[str(i)] = out.count(i)
    #         for k in admins.keys():
    #             try:
    #                 j = self.robot.get_chat(k).to_dict()
    #                 if j.get('first_name') and j.get('last_name'):
    #                     count = admins[k]
    #                     del admins[k]
    #                     admins[(' '.join([j['first_name']] + [j['last_name']]))] = count
    #                 elif j.get('first_name'):
    #                     count = admins[k]
    #                     del admins[k]
    #                     admins[j['first_name']] = count
    #             except Exception as E:
    #                 pass
    #         ex = [[x, y] for x, y in admins.items()]
    #         data = [x[1] for x in ex]
    #         labels = ["{}\n{}".format(x[0], x[1]) for x in ex]
    #         explode = [0.1 for _ in labels]
    #         plt.figure(figsize=(12.80, 7.20))
    #         plt.title(title)
    #         plt.axes(aspect=1)
    #         plt.pie(x=data, labels=labels, explode=explode, startangle=90,
    #                 autopct='%1.1f%%', radius=1.25, labeldistance=1.14, pctdistance=.9)
    #         plt.savefig('plot/pie.jpg')
    #         bot.send_photo(photo=open('plot/pie.jpg', 'rb'), chat_id=update.message.chat_id)
    #         plt.close()
    #         os.remove('./plot/pie.jpg')
    #     except Exception as E:
    #         logging.error('report admins {}'.format(E))
    #

    def add_member(self):
        try:
            channels = [channel.channel_id for channel in database.find('channel')]
            current_date = self.current_time()[0]
            for channel_id in channels:
                num = self.robot.get_chat_members_count(channel_id)
                member = database.Member(number=num, channel_id=channel_id, calendar=current_date)
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
                elif message.kind == 'audio':
                    message.msg_ch_id = self.robot.send_audio(chat_id=message.to_ch, audio=message.file_id,
                                                              caption=txt).message_id
                elif message.kind == 'animation':
                    message.msg_ch_id = self.robot.send_animation(chat_id=message.to_ch, animation=message.file_id,
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
                elif message.kind == 'vid':
                    form = message.other
                    txt = self.gif_watermark(gif=message.file_id, format_=form, caption=message.txt,
                                             channel_name=message.to_ch)
                    message.msg_ch_id = self.robot.send_document(chat_id=message.to_ch,
                                                                 document=open('vid/out.mp4', 'rb'),
                                                                 caption=txt).message_id
                    os.remove('./vid/out.mp4')
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
            t1 = self.current_time()[1]
            channels = database.find('channel')

            if int(t1.strftime('%H%M')) == 0:
                self.add_member()

            if t1.minute == 0:
                bot.send_message(chat_id=sina, text=str(psutil.virtual_memory()[2]))

            for channel in channels:
                if self.time_is_in(now=t1, channel=channel):
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
        print('started')

        dpa(MessageHandler(Filters.status_update.new_chat_members, self.send_info))
        # dpa(CommandHandler('remain', self.remain, Filters.private)))
        # dpa(CommandHandler('member', self.report_members, Filters.private), pass_args=True))
        # dpa(CommandHandler('admin', self.report_admins, Filters.private), pass_args=True))
        dpa(CommandHandler('state', self.state, Filters.private))
        dpa(CommandHandler('delay', self.set_interval, Filters.private, pass_args=True))
        dpa(CommandHandler('bed', self.set_bed, Filters.private, pass_args=True))
        dpa(CommandHandler('wake', self.set_wake, Filters.private, pass_args=True))
        dpa(ConversationHandler(entry_points=[CommandHandler(command='status',
                                                             callback=self.entry,
                                                             filters=Filters.private)],
                                states={
                                    self.setting: [CallbackQueryHandler(self.setting)],
                                    self.select: [CallbackQueryHandler(self.select)],
                                    self.step2: [CallbackQueryHandler(self.step2)],
                                    self.done: [CallbackQueryHandler(self.done)],
                                    # self.graph: [CallbackQueryHandler(self.graph)]
                                },
                                fallbacks=[CommandHandler(command='cancel',
                                                          callback=self.cancel)]))

        # todo finish this
        dpa(ConversationHandler(entry_points=[CommandHandler(command='member',
                                                             callback=self.member,
                                                             filters=Filters.private)],
                                states={
                                    self.member_range: [CallbackQueryHandler(callback=self.member_range)],
                                },
                                fallbacks=[CommandHandler(command='cancel',
                                                          callback=self.cancel)]))
        # todo add conver.. delay

        dpa(MessageHandler(filters=Filters.group, callback=self.save, edited_updates=True))
        job.run_repeating(callback=self.task, interval=60, first=0)
        self.updater.idle()


timer = SSP('410818874:AAEU8gHdOmurgJBf_N_p-58qVW94Rc_vgOc')
timer.start()
