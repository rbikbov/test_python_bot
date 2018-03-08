# -*- coding: utf-8 -*-

import datetime, time

import sys
from telegram.ext import Updater

from bot import run_bot

# телеграм-бот
token = sys.argv[1]
chat_id = sys.argv[2]
updater = Updater(token=token)
dispatcher = updater.dispatcher

# настройки биржи
my_utc = 5 # мой часовой пояс +5
true_weekdays = [1, 2, 3, 4, 5] # понедельник, вторник, среда, четверг, пятница
start = datetime.time(8) # начало работы биржи с учетом utc
end = datetime.time(16) # завершение работы биржи с учетом utc
add_link = True # добавлять в сообщение ссылку на инструмент

# интервал запросов
interval = int(sys.argv[3])


def time_in_range(start, end, time):
    if start <= end:
        return start <= time <= end
    else:
        return start <= time or time <= end


def check_day_and_time():
    now = datetime.datetime.now()
    cur_weekday = now.isoweekday()
    utc_datetime = now - datetime.timedelta(hours=my_utc)
    utc_time = utc_datetime.time()
    true_time = time_in_range(start, end, utc_time)
    true_weekday = cur_weekday in true_weekdays
    return true_time and true_weekday


def send_total_stat():
    total_stat_str = 'Итоги торгов на "Газовый конденсат" было совершено сделок {0} в "ОБЪЕМЕ"({1}т.) по "СРЕДНЯЯ ЦЕНА"({2}р.).' \
        .format(total_stat['count'], total_stat['amount'], total_stat['average_price'])

    dispatcher.bot.send_message(
        chat_id=chat_id,
        text=total_stat_str
    )

    print(total_stat_str)


# хранилище инструментов
positions = {}

# хранилище итоговых результатов
total_stat = {
    'count': 0,
    'amount': 0,
    'total_price': 0,
    'average_price': 0
}

# открывалась ли биржа после запуска скрипта
opened = False

# интервал минута
while True:
    if check_day_and_time():
        opened = True
        run_bot(positions, total_stat, dispatcher, chat_id, add_link)
    else:
        print('Биржа закрыта')
        if opened:
            opened = False
            send_total_stat()
            break
    time.sleep(interval)


