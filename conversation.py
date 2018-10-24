from telegram.ext import ConversationHandler, CallbackQueryHandler, CommandHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton as Inline
import database
import logging

logging.basicConfig(filename='report.log', level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s')

# region setting


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
                lst = [[Inline(i.name, callback_data=i.name)] for i in channels]
                bot.send_message(chat_id=admin,
                                 text="شما صاحب چندین کانال هستید\nمایل به مشاهده تنظیمات کدام یک هستید؟",
                                 reply_markup=InlineKeyboardMarkup(lst))
                return self.setting

    except Exception as E:
        logging.error("setting {}".format(E))


def setting(self, bot, update):
    try:
        if update.callback_query:
            name = update.callback_query.data
            channel = database.find('channel', name=name)
            chat_id = update.callback_query.message.chat_id
            admin = update.callback_query.message.from_user
            message_id = update.callback_query.message.message_id

            remaining, date = self.remain(admin, channel)
            if not remaining == 0:
                text = 'پیام های باقیمانده {} کانال تا {} تامین خواهد بود'.format(remaining, date)
            else:
                text = 'هیچ پیامی در صف نیست'

            bot.edit_message_text(chat_id=chat_id,
                                  text=(f'میزان وقفه ⏳= {channel.interval}\n'
                                        f'ساعت توقف 🕰= {channel.bed}\n'
                                        f'ساعت شروع 🕰= {channel.wake}\n'
                                        f'{text}'),
                                  message_id=message_id,
                                  reply_markup=InlineKeyboardMarkup(
                                      [[Inline('وقفه', callback_data='interval'),
                                        Inline('ساعت توقف', callback_data='bed'),
                                        Inline('ساعت شروع', callback_data='wake')],
                                       ]
                                  ))
            return self.select
        else:
            um = update.message
            admin = um.from_user
            channel = database.find('channel', admin=admin)

            remaining, date = self.remain(admin, channel)
            if not remaining == 0:
                text = 'پیام های باقیمانده {} کانال تا {} تامین خواهد بود'.format(remaining, date)
            else:
                text = 'هیچ پیامی در صف نیست'

            bot.send_message(chat_id=admin.id,
                             text=(f'میزان وقفه ⏳= {channel.interval}\n'
                                   f'ساعت توقف 🕰= {channel.bed}\n'
                                   f'ساعت شروع 🕰= {channel.wake}\n'
                                   f'{text}'),
                             reply_markup=InlineKeyboardMarkup(
                                 [[Inline('وقفه', callback_data='interval'),
                                   Inline('ساعت توقف', callback_data='bed'),
                                   Inline('ساعت شروع', callback_data='wake')],
                                  ]
                             ))
            return self.select
    except Exception as E:
        logging.error("setting {}".format(E))


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
            if self.sleep(step.hour * 10000):
                step += timedelta(hours=channel.wake / 10000 - step.hour)
            if step.minute in channel.interval and not step.minute == 0:
                remaining -= 1
            step += timedelta(minutes=1)

        logging.info("remain by {}".format(user.first_name))
        if rem > 0:
            return rem, step.strftime('%y-%m-%d -> %H:%M')
        else:
            return 0, 0
        pass
    except Exception as E:
        logging.error("Could't get remaining time by {} Error: {}".format(user.first_name, E))


def cancel(self, _, update):
    return ConversationHandler.END# endregion