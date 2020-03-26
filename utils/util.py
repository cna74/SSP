from khayyam3.tehran_timezone import JalaliDatetime, timedelta
from utils import db
import numpy as np
import logging


def sleep(now=None, bed=None, wake=None):
    try:
        now = JalaliDatetime().now().hour if not now else now.hour

        if -1 in (bed, wake):
            return False

        elif now >= bed > wake < now or now >= bed < wake > now:
            return True

        else:
            return False
    except Exception as E:
        logging.error("sleep {}".format(E))


def time_is_in(now, channel: db.Channel):
    try:
        if not channel.up:
            return False

        if sleep(now=now, bed=channel.bed, wake=channel.wake):
            return False
        else:
            # if endswith hf or mf
            interval = (int(channel.interval[:-2]),)
            if channel.interval.endswith("mr"):
                interval = np.arange(0, 60, interval[0], dtype=np.uint8)
            elif channel.interval.endswith("hr"):
                interval = np.arange(0, 24, interval[0], dtype=np.uint8)

            if (channel.interval[-2] == "m" and now.minute in interval) or \
                    (channel.interval[-2] == "h" and now.hour in interval and now.minute == 0):
                return True
    except Exception as E:
        logging.error("time_is_in {}".format(E))


def remain(channel):
    try:
        remaining = db.remain(channel)
        step = JalaliDatetime().now()
        rem = remaining
        if channel.up:
            while remaining > 0:

                # assume to send
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

    except Exception as E:
        logging.error("remain {}".format(E))
