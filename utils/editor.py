from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, TextClip, clips_array
import moviepy.config as mpy_conf
import multiprocessing
from PIL import Image
import warnings
import logging
import re
import os

warnings.simplefilter("ignore", category=Warning)
mpy_conf.change_settings({'FFMPEG_BINARY': '/usr/bin/ffmpeg', 'ImageMagick': '/usr/bin/convert'})
logging.basicConfig(filename='report.log', level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s')


def id_remove(text, channel) -> str:
    try:
        pattern_id = re.compile(r'(@\S+)', re.I)
        pattern_pos = re.compile(r'(:\S{1,2}:)', re.I)
        pattern_link = re.compile(r'https://t\.me\S*')

        if re.search(pattern_link, text):
            link = re.findall(pattern_link, text)
            for i in link:
                text = text.replace(i, '')

        if re.search(pattern_pos, text):
            logo = re.findall(pattern_pos, text)[0]
            text = re.sub(pattern_pos, '', text)
            text = logo + text

        if re.search(pattern_id, text):
            ids = re.findall(pattern_id, text)
            for id_ in ids:
                if not id_.lower() == channel.name.lower():
                    text = re.sub(id_, channel.name, text)
            if not text.lower().strip().endswith(channel.name.lower()):
                text += '\n' + channel.name
        else:
            text += '\n' + channel.name

        return text

    except Exception as E:
        logging.error("id_remove {}".format(E))


def logo_by_name(channel, logo_dir=None) -> ImageClip:
    if not logo_dir:
        logo_dir = 'logo/{}.png'.format(channel.name)

    lg1 = TextClip(txt=channel.name, size=(500, 100), color="white", stroke_color='white', stroke_width=1)
    lg2 = TextClip(txt=channel.name, size=(500, 100), color="grey", stroke_color='grey', stroke_width=1)
    lg3 = TextClip(txt=channel.name, size=(500, 100), color="black", stroke_color='black', stroke_width=1)
    lg = clips_array(array=[[lg1],
                            [lg2],
                            [lg3]])

    lg.save_frame(filename=logo_dir)

    return ImageClip(img=logo_dir)


def image_watermark(photo, out, caption, channel) -> str:
    try:
        logo_dir = 'logo/{}.png'.format(channel.name)
        pattern = re.compile(r':\S{,2}:', re.I)
        div = 5
        roi_pt = re.compile(r'\d', re.I)

        if re.search(pattern, caption):
            i_cor = ''.join(re.findall(pattern, caption)[0])
            roi = int(re.findall(roi_pt, i_cor)[0]) if re.findall(roi_pt, i_cor)[0] else channel.pos
        else:
            roi = channel.pos

        bg = Image.open(photo)
        if not roi == 0:
            if not os.path.exists('logo/{}.png'.format(channel.name)):
                logo_by_name(channel)

            lg = Image.open(logo_dir)

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

            if dict1.get(roi):
                bg.paste(lg, dict1.get(roi), lg)
                bg.save(out)
        else:
            bg.save(out)

        if re.search(pattern, caption):
            caption = id_remove(re.sub(pattern, '', caption), channel)
        else:
            caption = id_remove(caption, channel)
        return caption
    except Exception as E:
        logging.error("image_watermark {}".format(E))


def vid_watermark(vid, out, kind, caption, channel) -> str:
    try:
        logo_dir = "logo/{}.png".format(channel.name)
        pattern = re.compile(r':\d:')
        div = 5
        find = int(re.findall(pattern, caption)[0][1:-1]) if re.search(pattern, caption) else channel.pos
        audio = False if kind == 'animation' else True
        clip = VideoFileClip(vid, audio)
        w, h = clip.size

        pos = {1: ('left', 'top'), 2: ('center', 'top'), 3: ('right', 'top'),
               4: ('left', 'center'), 5: ('center', 'center'), 6: ('right', 'center'),
               7: ('left', 'bottom'), 8: ('center', 'bottom'), 9: ('right', 'bottom')}
        size = h // div if w > h else w // div

        if os.path.exists(logo_dir):
            logo = ImageClip(logo_dir) \
                .set_duration(clip.duration) \
                .resize(width=size, height=size) \
                .set_pos(pos.get(find))
        else:
            logo = logo_by_name(channel)\
                .set_duration(clip.duration)\
                .resize(width=size, height=size)\
                .set_pos(pos.get(find))

        final = CompositeVideoClip([clip, logo])
        final.write_videofile(filename=out, progress_bar=False, verbose=False, threads=multiprocessing.cpu_count())

        if re.search(pattern, caption):
            caption = id_remove(re.sub(pattern, '', caption), channel)
        else:
            caption = id_remove(caption, channel)
        return caption

    except Exception as E:
        logging.error('gif_watermark {}'.format(E))
