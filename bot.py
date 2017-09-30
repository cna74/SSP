from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.error import BadRequest
import matplotlib.pyplot as plt
from PIL import Image
import telegram
import logging
import sqlite3
import time
import re

updater = Updater("Token")
robot = telegram.Bot("Token")

hour = (203000, 213000, 223000, 233000, 3000, 13000, 23000, 33000, 43000, 53000, 63000, 73000, 83000,
        93000, 103000, 113000, 123000, 133000, 143000, 153000, 163000, 173000, 183000, 193000)

gp_channel, channel = '-1001125799090', '@crazy_mind3'


def current_time():
    return int(str(time.gmtime()[3]).zfill(2) + str(time.gmtime()[4]).zfill(2) + str(time.gmtime()[5]).zfill(2))


def current_date():
    return int(str(time.gmtime()[0])[-2:]+str(time.strftime('%m'))+str(time.strftime('%d')))


def current_mood():
    x = current_time()
    if 203000 <= x < 235900 or 0 <= x < 13000:
        return 900
    elif 130 <= x < 53000:
        return 3600
    else:
        return 600
        

def id_remove(text):
    pattern = re.compile(r'(@[a-z0-9_]*)', re.I)
    if re.search(pattern, text):
        state = re.findall(pattern, text)
        for state in state:
            if state == '@crazy_mind3' or state == '@crazy_miind3' or state == '@mmd_bt':
                continue
            text = re.sub(state, '', text)
        return text
    else:
        return text


def echo(bot, update):
    if str(update.message.chat.id) == gp_channel:
        if str(update.message.text).startswith('.'):
            pass
        else:
            caption = id_remove(text=update.message.text)
            bot.send_message(chat_id=channel, text=caption + '\n' + '@Crazy_mind3')

            time.sleep(current_mood())


def put(coor):
    lg = Image.open('CC.png')
    bg = Image.open('tmp.jpg')
    res = bg.size
    lg_sz = lg.size
    deaf_l, deaf_p, box_deaf = (1920, 1080), (1080, 1920), (2000, 2000)

    if res[0] > res[1]:
        if not res[0] == deaf_l[0] and not res[1] == deaf_l[1]:
            n_deaf = [int((lg_sz[0] * res[0]) / deaf_l[0]), int((lg_sz[1] * res[1]) / deaf_l[1])]
            if res[0] > deaf_l[0] or res[1] > deaf_l[1]:
                print(res, 'HIGH RESOLUTION')
            lg.thumbnail(n_deaf)

    elif res[0] == res[1]:
        if not res == box_deaf:
            n_deaf = [int((lg_sz[0] * res[0]) / box_deaf[0]), int((lg_sz[1] * res[1]) / box_deaf[1])]
            lg.thumbnail(n_deaf)

    else:
        if not res[0] == deaf_p[0] and not res[1] == deaf_p[1]:
            n_deaf = [int((lg_sz[0] * res[0]) / deaf_p[0]), int((lg_sz[1] * res[1]) / deaf_p[1])]
            if res[0] > deaf_p[0] or res[1] > deaf_p[1]:
                print(res, 'HIGH RESOLUTION')
            lg.thumbnail(n_deaf)
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
        bg.paste(lg, dict1.get(coor), lg)
        bg.save('output.jpg')
    else:
        bg.paste(lg, dict1.get('sw'), lg)
        bg.save('output.jpg')


def photo_send(bot, update):
    caption = id_remove(text=update.message.caption) if update.message.caption else ' '
    if not caption.startswith('.') or not update.message.chat_id == gp_channel:
        (bot.getFile(update.message.photo[-1].file_id)).download('tmp.jpg')
        pattern = re.compile(r'(coor)(.)?([=:])(.)?([a-z]{1,2})', re.I)
        coor_pt = re.compile(r'(nw|ne|nc|cw|cc|ce|sw|sc|se|e|n|w|s)', re.I)
        if re.search(pattern, caption):
            i_cor = ''.join(re.findall(pattern, caption)[0]).lower()
            cor = re.findall(coor_pt, i_cor)[0] if re.findall(coor_pt, i_cor)[0] else 'sw'
            put(coor=cor)
            with open('output.jpg', 'rb') as photo:
                bot.send_photo(chat_id=channel, photo=photo,
                               caption=re.sub(pattern, '', caption) + '\n@Crazy_mind3')
        else:
            tel_caption = id_remove(text=caption)
            put(coor='sw')
            with open('output.jpg', 'rb') as photo:
                bot.send_photo(chat_id=channel, photo=photo,
                               caption=tel_caption + '\n@Crazy_mind3')
        time.sleep(current_mood())
    else:
        pass


def video_send(bot, update):
    if str(update.message.chat.id) == gp_channel:
        file_id = str(update.message.video.file_id)
        caption = id_remove(text=update.message.caption) if update.message.caption else ' '
        bot.send_video(chat_id=channel, video=file_id,
                       caption=caption + '\n' + '@Crazy_mind3')
        time.sleep(current_mood())


def gif(bot, update):
    if str(update.message.chat.id) == gp_channel:
        file_id = str(update.message.document.file_id)
        caption = id_remove(text=update.message.caption) if update.message.caption else ' '
        bot.send_document(chat_id=channel, document=file_id,
                          caption=caption + '\n' + '@Crazy_mind3')
        time.sleep(current_mood())


def voice(bot, update):
    if str(update.message.chat.id) == gp_channel:
        file_id = str(update.message.voice.file_id)
        caption = id_remove(text=update.message.caption) if update.message.caption else ' '
        bot.send_voice(chat_id=channel, voice=file_id,
                       caption=caption + '\n' + '@Crazy_mind3')
        time.sleep(current_mood())


def audio_send(bot, update):
    if str(update.message.chat.id) == gp_channel:
        file_id = str(update.message.audio.file_id)
        caption = id_remove(text=update.message.caption) if update.message.caption else ' '
        bot.send_audio(chat_id=channel, audio=file_id,
                       caption=caption + '\n''@Crazy_mind3')
        time.sleep(current_mood())

dp = updater.dispatcher
updater.start_polling()

while True:
    time.sleep(1)
    ct = current_time()
    for i in range(0, len(hour)):
        if ct == hour[i]:
            print(str(ct) + ' ' + str(robot.get_chat_members_count(chat_id=channel)))

    if ct == 113000:
        print(time.ctime(), str(robot.get_chat_members_count(chat_id=channel)))

    if ct == 203000:
        with open('daylog.txt', 'a') as dlog:
            dlog.write(str(current_date()) + ' ' + str(robot.get_chat_members_count(chat_id=channel)) + '\n')

    dp.add_handler(MessageHandler(Filters.text, echo))
    dp.add_handler(MessageHandler(Filters.photo, photo_send))
    dp.add_handler(MessageHandler(Filters.video, video_send))
    dp.add_handler(MessageHandler(Filters.document, gif))
    dp.add_handler(MessageHandler(Filters.voice, voice))
    dp.add_handler(MessageHandler(Filters.audio, audio_send))

