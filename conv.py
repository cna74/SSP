from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, CommandHandler, Updater, Filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton as Inline
from khayyam3.tehran_timezone import timedelta, JalaliDatetime
import numpy as np
import matplotlib
import logging
import strings
import editor
import db
import os

matplotlib.use('AGG', force=True)
import matplotlib.pyplot as plt

logging.basicConfig(filename='report.log', level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s')


def sleep(entry=None, bed=None, wake=None):
    entry = JalaliDatetime().now().strftime('%H%M') if not entry else entry.strftime('%H%M')

    if "off" in (bed, wake):
        return False

    if entry >= bed > wake < entry or entry >= bed < wake > entry:
        return True

    return False


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


def remain(admin, channel):
    try:
        remaining = db.remain(channel)
        step = JalaliDatetime().now()
        rem = remaining

        while remaining > 0:
            if sleep(step, bed=channel.bed, wake=channel.wake):
                step += timedelta(hours=channel.wake / 10000 - step.hour)

            if time_is_in(now=step, channel=channel):
                remaining -= 1
            step += timedelta(minutes=1)

        if rem > 0:
            date = step.strftime('%A %d %B %H:%M')
            text = 'پیام های باقیمانده: {0}\nکانال تا {1} تامین خواهد بود'.format(rem, date)
        else:
            text = 'هیچ پیامی در صف نیست'

        logging.info("remain by {}".format(admin))
        return text
    except Exception as E:
        logging.error("Could't get remaining time by {} Error: {}".format(admin, E))


# region status
def status(bot, update):
    try:
        um = update.message
        admin = um.from_user.id
        channels = db.find('channel', admin=admin)
        if channels:
            if isinstance(channels, db.Channel):
                channel = channels
                chat_id = um.chat_id
                message_id = um.message_id
                text, keyboard = strings.status(channel=channel, remain=remain(admin=admin, channel=channel))
                bot.send_message(chat_id=chat_id,
                                 text=text,
                                 reply_to_message_id=message_id,
                                 reply_markup=keyboard)
                return select

            elif isinstance(channels, list):
                lst = [[Inline(i.name, callback_data=f"_;{i.name}")] for i in channels]
                bot.send_message(chat_id=admin,
                                 text="شما صاحب چندین کانال هستید\nمایل به مشاهده تنظیمات کدام یک هستید؟",
                                 reply_markup=InlineKeyboardMarkup(lst))
                return setting

    except Exception as E:
        logging.error("status {}".format(E))


def setting(bot, update):
    try:
        if update.callback_query:
            data = update.callback_query.data
            admin, name = data.split(';')
            if not admin == '_':
                channel = db.find("channel", admin=admin, name=name)
            else:
                channel = db.find('channel', name=name)
            chat_id = update.callback_query.message.chat_id
            message_id = update.callback_query.message.message_id
            text, keyboard = strings.status(channel=channel, remain=remain(admin=admin, channel=channel))
            bot.edit_message_text(chat_id=chat_id, text=text, message_id=message_id, reply_markup=keyboard)
            return select
        else:
            um = update.message
            admin = um.from_user
            channel = db.find('channel', admin=admin)
            text, keyboard = strings.status(channel=channel, remain=remain(admin=admin, channel=channel))
            bot.send_message(chat_id=admin.id, text=text, reply_markup=keyboard)
            return select
    except Exception as E:
        logging.error("setting {}".format(E))


def select(bot, update):
    try:
        um = update.callback_query
        data = um.data
        data = data.split(';')
        chat_id = um.message.chat_id
        message_id = um.message.message_id
        if data[0] == 'interval':
            keyboard = [[Inline('01M', callback_data='01m;{}'.format(data[1]))]]
            for i in range(5, 60, 5):
                keyboard.append(
                    [Inline("{}M".format(str(i).zfill(2)), callback_data="{}m;{}".format(str(i).zfill(2), data[1]))])
            for i in range(0, 24):
                keyboard.append(
                    [Inline("{}H".format(str(i).zfill(2)), callback_data='{}h;{}'.format(str(i).zfill(2), data[1]))])
            keyboard = np.array(keyboard).reshape((-1, 6)).tolist()
            keyboard.append([Inline('بازگشت به منوی تنظیمات', callback_data='setting;{}'.format(data[1]))])
            bot.edit_message_text(chat_id=chat_id,
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
            return step2
        elif data[0] == 'wake':
            keyboard = []
            for i in range(1, 25):
                keyboard.append(
                    [Inline('{}:00'.format(str(i).zfill(2)), callback_data="{}w;{}".format(str(i).zfill(2), data[1]))])
            keyboard = np.array(keyboard).reshape((6, -1)).tolist()
            keyboard.append([Inline('off', callback_data="offw;{}".format(data[1]))])
            keyboard.append([Inline('بازگشت به منوی تنظیمات', callback_data='setting;{}'.format(data[1]))])
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=message_id,
                                  text="بات از چه ساعتی شروع به کار کند؟",
                                  reply_markup=InlineKeyboardMarkup(keyboard))
            return done
        elif data[0] == 'bed':
            keyboard = []
            for i in range(1, 25):
                keyboard.append(
                    [Inline('{}:00'.format(str(i).zfill(2)), callback_data="{}b;{}".format(str(i).zfill(2), data[1]))])
            keyboard = np.array(keyboard).reshape((6, -1)).tolist()
            keyboard.append([Inline('off', callback_data="offw;{}".format(data[1]))])
            keyboard.append([Inline('بازگشت به منوی تنظیمات', callback_data='setting;{}'.format(data[1]))])
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=message_id,
                                  text="بات در چه ساعتی خاموش شود؟",
                                  reply_markup=InlineKeyboardMarkup(keyboard))
            return done
        elif data[0] == 'graph':
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=message_id,
                                  text="نمودار در چه بازه زمانی باشد؟",
                                  reply_markup=InlineKeyboardMarkup(
                                      [[Inline('یک هفته', callback_data="1w;{}".format(data[1])),
                                        Inline('یک ماه', callback_data="1m;{}".format(data[1])),
                                        Inline('یک سال', callback_data="1y;{}".format(data[1]))]]
                                  ))
            return graph
        elif data[0] == 'logo':
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=message_id,
                                  text="یک عکس با فرمت png بدون پس زمینه برام بفرست در ابعاد مربع\n"
                                       "اگر نمیتونی یا بلد نیستی اینکار رو بکنی"
                                       " میتونم از اسم کانال به عنوان لوگو استفاده کنم",
                                  reply_markup=InlineKeyboardMarkup(
                                      [[Inline('استفاده از نام کانال', callback_data="name;{}".format(data[1]))]]))
            return set_logo
        elif data[0] == 'up':
            channel = db.find('channel', name=data[1])
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=message_id,
                                  text=strings.status_upgrade(channel))
            return ConversationHandler.END
    except Exception as E:
        logging.error("select {}".format(E))


def step2(bot, update):
    if update.callback_query:
        um = update.callback_query
        data = um.data.split(';')
        interval = data[0]
        ch_name = data[1]
        admin = um.message.chat_id
        message_id = um.message.message_id

        if interval.endswith('m'):
            interval = int(interval[:-1])
            if 1 <= interval <= 30:
                bot.edit_message_text(chat_id=um.message.chat_id,
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
                                          [[Inline('حالت  1️⃣', callback_data='{}mr;{}'.format(interval, ch_name)),
                                            Inline('حالت  2️⃣', callback_data='{}mf;{}'.format(interval, ch_name))],
                                           [Inline('لغو، بازگشت', callback_data='_;{}'.format(ch_name))]])
                                      )
            else:
                bot.edit_message_text(chat_id=um.message.chat_id,
                                      message_id=um.message.message_id,
                                      text="گام دوم:\n"
                                           "پیام ها در ساعاتی مانند 01:{0}, 02:{0} ارسال میشوند\n"
                                           "از ما کمک بگیرید:\n"
                                           "@s_for_cna".format(str(interval).zfill(2)),
                                      reply_markup=InlineKeyboardMarkup(
                                          [[Inline('تایید', callback_data='{}mr;{}'.format(interval, ch_name))],
                                           [Inline('لغو، بازگشت', callback_data='_;{}'.format(ch_name))]])
                                      )

            return done
        elif interval.endswith('h'):
            interval = int(interval[:-1])
            if 1 <= interval < 13:
                bot.edit_message_text(chat_id=um.message.chat_id,
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
                                          [[Inline('حالت  1️⃣', callback_data='{}hr;{}'.format(interval, ch_name)),
                                            Inline('حالت  2️⃣', callback_data='{}hf;{}'.format(interval, ch_name))],
                                           [Inline('لغو، بازگشت', callback_data='_;{}'.format(ch_name))]])
                                      )
            else:
                bot.edit_message_text(chat_id=um.message.chat_id,
                                      message_id=um.message.message_id,
                                      text="گام دوم:\n"
                                           "پیام ها هر روز راس ساعت {0}:00 ارسال شوند"
                                           "کدام یک مورد پسند شماست؟\n"
                                           "از ما کمک بگیرید:\n"
                                           "@s_for_cna".format(str(interval).zfill(2)),
                                      reply_markup=InlineKeyboardMarkup(
                                          [[Inline('تایید', callback_data='{}mr;{}'.format(interval, ch_name))],
                                           [Inline('لغو، بازگشت', callback_data='_;{}'.format(ch_name))]])
                                      )
            return done
        elif interval == "setting":
            channel = db.find("channel", name=ch_name)
            text, keyboard = strings.status(channel=channel, remain=remain(admin=admin, channel=channel))
            bot.edit_message_text(chat_id=admin, text=text, message_id=message_id, reply_markup=keyboard)
            return select


def done(bot, update):
    try:
        if update.callback_query:
            um = update.callback_query
            data = um.data
            part1, channel_name = data.split(';')
            chat_id = um.message.chat_id
            message_id = um.message.message_id

            channel = db.find('channel', name=channel_name)

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
            elif part1.endswith("r") or part1.endswith("f"):
                interval = part1
                channel.interval = interval
                db.update(channel)
            elif part1 == "off":
                channel.bed = part1
                channel.wake = part1
                db.update(channel)

            text, keyboard = strings.status(channel=channel, remain=remain(admin=chat_id, channel=channel))
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=keyboard)
            return select

    except Exception as E:
        logging.error("done {}".format(E))


def graph(self, _, update):
    try:
        if update.callback_query:
            um = update.callback_query
            admin = um.message.chat_id
            data = um.data
            domain, ch_name = data.split(';')
            save_in = "plot/{}.png".format(ch_name)

            d = {'1w': 7, '1m': 31, '1y': 365}
            domain = d.get(domain)
            now = JalaliDatetime().now().to_date()
            from_ = now - timedelta(days=domain)

            out = db.find('member', admin=admin, name=ch_name, from_=from_, til=now)

            y = out[:, 0]
            if len(out) < 3:
                self.robot.edit_message_text(chat_id=admin,
                                             message_id=um.message.message_id,
                                             text="حداقل باید سه روز از ثبت نام گذشته باشد")
                return ConversationHandler.END

            y = np.append(y, self.robot.get_chat_members_count(ch_name))
            x = np.arange(len(y), dtype=int)

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

            days = len(y) - 1
            diff = np.mean(np.diff(y))
            prediction = round(y[-1] + domain * diff)
            diff = format(diff, '.2f')
            now = JalaliDatetime().from_date(now)
            til = now + timedelta(days=days)

            self.robot.send_photo(chat_id=um.message.chat_id,
                                  photo=open(save_in, 'rb'),
                                  caption="از {} تا {} در {} روز\n" \
                                          " کمترین میزان تعداد اعضا 🔻 {}\n" \
                                          " بیشترین تعداد اعضا🔺 {}\n" \
                                          " میانگین سرعت عضو شدن اعضا در روز {}\n" \
                                          "پیش بینی برای {} روز آینده برابر {}".format(
                                      days, til, now, y.min(), y.max(), diff, prediction, domain))
            os.remove(save_in)
            return ConversationHandler.END
    except Exception as E:
        logging.error("graph {}".format(E))


def set_logo(bot, update):
    try:
        if update.callback_query:
            um = update.callback_query
            comm, name = um.data.split(';')
            chat_id = um.message.chat_id
            channel = db.find('channel', admin=chat_id, name=name)
            editor.logo_by_name(channel)
            channel.logo = True
            keyboard = []
            for i in range(1, 10):
                keyboard.append([Inline(str(i), callback_data="{};{}".format(i, channel.name))])
            keyboard = np.array(keyboard).reshape((3, 3)).tolist()
            keyboard.append([Inline('هیچکدام', callback_data='0;{}'.format(channel.name))])

            bot.send_photo(chat_id=chat_id,
                           reply_to_message_id=um.message_id,
                           photo=open('info.png', 'rb'),
                           caption='خب لوگو تایید شد. محل پیش فرض قرارگیری لوگو رو حالا انتخاب کن\n'
                                   'اگر میخوای بصورت پیش فرض لوگو روی عکس ها و گیف ها گذاشته نشه '
                                   '"هیچکدام" رو انتخاب کن\n'
                                   'پشتیبانی\n'
                                   '@s_for_cna',
                           reply_markup=InlineKeyboardMarkup(keyboard))
            return set_pos

        elif update.message.document:
            um = update.message
            chat_id = um.chat_id
            file_id = um.document.file_id
            mime = um.document.mime_type
            size = um.document.file_size
            name = um.caption if um.caption else None
            if name:
                res = db.find('channel', admin=chat_id, name=name)
            else:
                res = db.find('channel', admin=chat_id)
            if isinstance(res, db.Channel) and mime.startswith('image') and size < (8 * 1025 * 1024):
                channel = res
                bot.get_file(file_id=file_id).download('logo/{}.png'.format(channel.name))
                channel.logo = True
                db.update(channel)

                keyboard = []
                for i in range(1, 10):
                    keyboard.append([Inline(str(i), callback_data="{};{}".format(i, channel.name))])
                keyboard = np.array(keyboard).reshape((3, 3)).tolist()
                keyboard.append([Inline('هیچکدام', callback_data='0;{}'.format(channel.name))])

                bot.send_photo(chat_id=chat_id,
                               reply_to_message_id=um.message_id,
                               photo=open('info.png', 'rb'),
                               caption='خب لوگو تایید شد. محل پیش فرض قرارگیری لوگو رو حالا انتخاب کن\n'
                                       'اگر میخوای بصورت پیش فرض لوگو روی عکس ها و گیف ها گذاشته نشه '
                                       '"هیچکدام" رو انتخاب کن\n'
                                       'پشتیبانی\n'
                                       '@s_for_cna',
                               reply_markup=InlineKeyboardMarkup(keyboard))
                return set_pos

            elif isinstance(res, list):
                bot.send_message(chat_id=chat_id,
                                 reply_to_message_id=um.message_id,
                                 text=strings.set_logo_fail)
                return set_logo
            else:
                bot.send_message(chat_id=chat_id,
                                 reply_to_message_id=um.message_id,
                                 text=strings.set_logo_else)
                return set_logo
    except Exception as E:
        logging.error("set_logo {}".format(E))


def set_pos(bot, update):
    try:
        um = update.callback_query
        admin = um.message.chat_id
        data = um.data
        pos, name = data.split(';')
        channel = db.find("channel", admin=admin, name=name)
        channel.pos = int(pos)
        db.update(channel)
        bot.send_message(chat_id=admin,
                         reply_to_message_id=um.message.message_id,
                         text="تغییرات اعمال شد",
                         reply_markup=InlineKeyboardMarkup(
                             [[Inline('وضعیت', callback_data='{};{}'.format(admin, name))]]
                         ))
        return setting
    except Exception as E:
        logging.error("set_pos {}".format(E))


# endregion


# region start
def start(bot, update):
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
        return start_select
    except Exception as E:
        logging.error("start {}".format(E))


def start_select(bot, update):
    um = update.callback_query
    message_id = um.message.message_id
    data = um.data
    chat_id = um.message.chat_id

    if data == "buy":
        bot.send_photo(chat_id=chat_id,
                       photo=open("./table.jpg", "rb"),
                       reply_to_message_id=message_id,
                       caption=strings.start_buy)
        return start_register
    elif data == "test":
        bot.edit_message_text(chat_id=chat_id,
                              message_id=message_id,
                              text=strings.start_select_test)
        return start_register
    elif data == "guide":
        bot.edit_message_text(chat_id=chat_id,
                              message_id=message_id,
                              text=strings.start_select_guide,
                              reply_markup=InlineKeyboardMarkup(
                                  [[Inline('خرید', callback_data='buy')],
                                   [Inline('تست (رایگان)', callback_data='test')]]
                              ))
    return start_select


def start_register(bot, update):
    try:
        um = update.message
        message_id = um.message_id
        chat_id = um.chat_id
        admin = um.from_user.id

        text = um.text
        text = text.split()

        group_id = text[0]
        name = text[1]
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
            return start_register
    except Exception as E:
        logging.error("start_register {}".format(E))


# endregion


# region interval
def set_interval(bot, update, args):
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
                            bot.send_message(
                                chat_id=um.chat_id,
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
                                    [[Inline('حالت  1️⃣', callback_data='{}mr;{}'.format(interval, ch_name)),
                                      Inline('حالت  2️⃣', callback_data='{}mf;{}'.format(interval, ch_name))],
                                     [Inline('لغو، بازگشت', callback_data='_;{}'.format(ch_name))]]))
                        else:
                            bot.send_message(
                                chat_id=um.chat_id,
                                reply_to_message_id=um.message_id,
                                text="گام دوم:\n"
                                     "پیام ها در ساعاتی مانند 01:{0}, 02:{0} ارسال میشوند\n"
                                     "از ما کمک بگیرید:\n"
                                     "@s_for_cna".format(str(interval).zfill(2)),
                                reply_markup=InlineKeyboardMarkup(
                                    [[Inline('تایید', callback_data='{}mr;{}'.format(interval, ch_name))],
                                     [Inline('لغو، بازگشت', callback_data='_;{}'.format(ch_name))]]))
                        return done

    except Exception as E:
        logging.error("set_interval: {}".format(E))


# endregion


def cancel(_, __):
    return ConversationHandler.END


def conversation(updater):
    # start
    updater.dispatcher.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler(command='start',
                                         callback=start,
                                         filters=Filters.private)],
            states={
                start_select: [CallbackQueryHandler(callback=start_select)],
                start_register: [CallbackQueryHandler(callback=start_register),
                                 MessageHandler(filters=Filters.private,
                                                callback=start_register, )]
            },
            fallbacks=[CommandHandler(command='cancel',
                                      callback=cancel)],
            conversation_timeout=timedelta(hours=1)))

    # status
    updater.dispatcher.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler(command='status',
                                         callback=status,
                                         filters=Filters.private)],
            states={
                setting: [CallbackQueryHandler(setting)],
                select: [CallbackQueryHandler(select)],
                step2: [CallbackQueryHandler(step2)],
                done: [CallbackQueryHandler(done)],
                graph: [CallbackQueryHandler(graph)],
                set_pos: [CallbackQueryHandler(set_pos)],
                set_logo: [CallbackQueryHandler(set_logo),
                           MessageHandler(filters=Filters.private, callback=set_logo)]
            },
            fallbacks=[CommandHandler(command='cancel',
                                      callback=cancel)],
            conversation_timeout=timedelta(minutes=5)))

    # delay
    updater.dispatcher.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler(command='delay',
                                         callback=set_interval,
                                         filters=Filters.private,
                                         pass_args=True)],
            states={
                done: [CallbackQueryHandler(callback=done)]
            },
            fallbacks=[CommandHandler(command='cancel',
                                      callback=cancel)],
            conversation_timeout=timedelta(minutes=5)))
