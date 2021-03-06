from telegram import InlineKeyboardMarkup, InlineKeyboardButton as Inline
from khayyam3.tehran_timezone import JalaliDatetime
import numpy as np

admin = "\n➖   ➖   ➖   ➖   ➖   ➖   ➖   ➖\nAdmin: @Cna74\nChannel: @Elite_Manager_ch"


def status_upgrade(channel):
    payment = dict({0: 5000, 1: 10000, 2: 15000, 3: 20000}).get(channel.plan)

    return "برای تمدید مبلغ {} را به شماره حساب \n" \
           "`6037-9974-3866-3685`\n" \
           "به نام سینا علیزاده واریز کنید و سپس کد رهگیری را برای ادمین ارسال کنید".format(payment) + admin


def status(channel, remain, button=True):
    expire = JalaliDatetime().from_datetime(channel.expire).strftime("%x")
    logo = "استفاده از نام کانال" if not channel.logo else "✔️"
    plan = dict([(0, "پایه 🏅"), (1, "برنز 🥉"), (2, "نقره 🥈"), (3, "طلایی 🥇")]).get(channel.plan)
    bed = "off" if channel.bed == -1 else channel.bed
    wake = "off" if channel.wake == -1 else channel.wake

    text = "میزان وقفه ⏳= {}\nساعت توقف 🕰= {}\nساعت شروع 🕰= {}\nلوگو = {}\n\n طرح = {}\n{}\nاعتبار شما تا {}".format(
        channel.interval, bed, wake, logo, plan, remain, expire
    )
    if button:
        keyboard = [[Inline('وقفه ⏲️', callback_data='interval;{}'.format(channel.name)),
                     Inline('ساعت توقف 🕰️', callback_data='bed;{}'.format(channel.name)),
                     Inline('ساعت شروع 🕰️', callback_data='wake;{}'.format(channel.name))],
                    [Inline('مشاهده نمودار 📈', callback_data="graph;{}".format(channel.name)),
                     Inline('تنظیم لوگو 🖼️', callback_data="logo;{}".format(channel.name))],
                    [Inline('تمدید 📆', callback_data='up;{}'.format(channel.name))]]
        keyboard = InlineKeyboardMarkup(keyboard)

        return text, keyboard

    return text


def set_logo_ok(channel,):
    text = 'خب لوگو تایید شد. محل پیش فرض قرارگیری لوگو رو حالا انتخاب کن\n' \
              'اگر میخوای بصورت پیش فرض لوگو روی عکس ها و گیف ها گذاشته نشه "هیچکدام" رو انتخاب کن\n' + admin

    keyboard = []
    for i in range(1, 10):
        keyboard.append([Inline(str(i), callback_data="{};{}".format(i, channel.name))])

    keyboard = np.array(keyboard).reshape((3, 3)).tolist()
    keyboard.append([Inline('هیچکدام', callback_data='0;{}'.format(channel.name))])

    keyboard = InlineKeyboardMarkup(keyboard)

    return text, keyboard


def up(state):
    if state:
        return "بات روشن شد" + admin
    else:
        return "بات خاموش شد، ولی همچنان پیام های گروه را ذخیره میکند" + admin


start_1 = """سلام 🤓✋🏻
من یک بات مدیر کانال هستم با کلی امکانات عالی:
در روز چندتا پست میزاری تو کانالت؟

🌟 فرض کنیم ۲۰ تا خب همشونو که نمیتونی باهم یهویی بفرستی تو کانال. چون میخوای کانال تو لیست ممبر هات همیشه بالا بمونه. هم اینکه اگر ۲۰ تا رو باهم بفرستی ممبر ها معمولا میرن ۲ تا پیام آخر تو کانال رو میخونن.
بیا اینکارو کن, اون ۲۰ تا پیام رو همون اول روز بفرست برای من. من در طول روز اون ۲۰ تا رو با وقفه میفرستم تو کانالت. تو ام برو به عشق و حالت برس لازم نیست کل روز رو انلاین باشی و پست بزاری.

🌟 میتونی تایین کنی که هر چند وقت پست بزارم مثلا هر ۱۱ دقیقه یا اصلا هر ۲ ساعت.

🌟 تازه من میتونم روی عکس و گیف و ویدیو لوگوی اختصاصی کانالت رو بزارم. 

🌟 یه چیز دیگه هر وقت خواستی میتونی نمودار رشد کانال رو ببینی. اینجوری میتونی بفهمی چه روزهایی کمتر ممبر جذب کانالت شده یا پست هات خوب نبودن یا هر دلیل دیگه ای و میتونم پیش بینی کنم که تا هفته ی بعدش کانالت حدودا چنتا ممبر ممکنه داشته باشه.

اگر شک داری میتونی یک هفته رایگان تست کنی
حتما راهنما رو قبل از اضافه کردن به کانال بخون

🤓 اگر سوال یا ابهامی داری میتونی ازم بپرسی""" + admin

start_2 = "گزینه مورد نظر را انتخاب کنید" + admin

start_buy = """جدول طرح ها لطفا مبلغ مورد نظر را به شماره حساب:\n
6037-9974-3866-3685\n
به نام سینا علیزاده واریز کنید و سپس کد رهگیری را برای ادمین ارسال کنید""" + admin

start_select_test = """آیدی عددی ای که بات توی گروه ارسال کرد رو همراه آیدی کانال وارد کنید
مثال:
-102346765 @name-e-channel""" + admin

start_select_guide = """راهنما
مراحل زیر رو به ترتیب باید انجام بدی:
1️⃣ یه گروه درست کن و به سوپر گروه تبدیلش کن, تمام ادمین ها( یا هر کسی که میخوای تو کانال پست بزاره) رو ادد کن توش
2️⃣ منو ادد کن تو اون گروه. به محض اینکه ادد بشم یه پیامی توی گروه میفرستم و بعدش لفت میدم اون پیام رو یجایی ذخیره کن بعدا لازمت میشه
3️⃣ حالا توی پیوی من مراحل خرید یا تست رو انتخاب کن
4️⃣ توی تست من ازت دوتا چیز میخوام ۱. آیدی کانال ۲.اون پیامی که تو مرحله دو توی گروه فرستادم
5️⃣ حالا منو دوباره ادد کن تو گروه ادمین ها اگر مراحل رو درست انجام داده باشی یه پیام تبریک میفرستم توی گروه و کارم رو از همون لحظه شروع میکنم
➖""" + admin

start_test_register_true = "ثبت نام (رایگان) با موفقیت انجام شد, حالا بات رو توی گروه و کانال ادد کنید " \
                           "و مطمئن شوید که بات در گروه و کانال ادمین باشد." + admin

start_test_register_false = "ورودی صحیح نیست دوباره تلاش کنید." + admin

set_logo_fail = "بنظر می آید شما صاحب چند اشتراک از بات هستید\n" \
                "بار دیگر لوگوی مورد نظر را ارسال کنید اینبار " \
                "لطفا آیدی کانال خود را در بخش caption اضافه کنید وارد کنید" + admin

set_logo_else = "مقادیر وارده اشتباه است." + admin

admin_hint = "برای اضافه کردن کانال جدید\n" \
             "/admin add <gp_id> <admin_id> <ch_name> <plan> <exp>\n\n" \
             "برای تمدید کانال\n" \
             "/admin ren <ch_name> <days>\n\n" \
             "برای تغییر طرح \n" \
             "/admin plan <ch_name> <plan>\n\n" \
             "برای تغییر نام کانال\n" \
             "/admin edit <ch_name> <new_ch_name>\n\n" \
             "لیست کانال ها\n" \
             "/admin lst\n\n" \
             "جزییات یک کانال\n" \
             "/admin det <ch_name>\n\n" \
             "برای حدف کانال\n" \
             "/admin del <ch_name>\n\n" \

congrats = "تبریک، بات با موفقیت در گروه ثبت شد" + admin
