from khayyam3.tehran_timezone import JalaliDatetime, timedelta
from utils import db
import numpy as np


def sleep(entry=None, bed=None, wake=None):
    entry = JalaliDatetime().now().strftime('%H%M') if not entry else entry.strftime('%H%M')

    if "off" in (bed, wake):
        return False

    if entry >= bed > wake < entry or entry >= bed < wake > entry:
        return True

    return False


def time_is_in(now, channel):
    if not channel.up:
        return False

    interval = (int(channel.interval[:-2]),)
    if channel.interval.endswith("mr"):
        interval = np.arange(0, 60, interval[0], dtype=np.uint8)
    elif channel.interval.endswith("hr"):
        interval = np.arange(0, 24, interval[0], dtype=np.uint8)

    if (channel.interval[-2] == "m" and now.minute in interval) or \
            (channel.interval[-2] == "h" and now.hour in interval):
        return True

    return False


def remain(channel):
    remaining = db.remain(channel)
    step = JalaliDatetime().now()
    rem = remaining

    if channel.up:
        while remaining > 0:
            if sleep(step, bed=channel.bed, wake=channel.wake):
                step += timedelta(hours=channel.wake / 10000 - step.hour)

            if time_is_in(now=step, channel=channel):
                remaining -= 1
            step += timedelta(minutes=1)

    if rem > 0 :
        date = step.strftime("%A %d %B %H:%M")
        if channel.up:
            text = "پیام های باقیمانده: {0}\nکانال تا {1} تامین خواهد بود".format(rem, date)
        else:
            text = "پیام های باقیمانده: {0}\nموقتا بات غیر فعال است".format(rem)

    else:
        text = "هیچ پیامی در صف نیست"

    return text
