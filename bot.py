# -*- coding: utf-8 -*-

import random
import re

import requests
from bs4 import BeautifulSoup


# Заголовки столбцов таблицы
titles = [
    'Биржевой инструмент', # 0
    'Предл.', # 1
    'Спрос', # 2
    'Ср.вз. цена', # 3
    'Объем договоров', # 4
    'Кол - во дог.', # 5
    'НПЗ' # 6
]

# для очистки текста от лишних символов
remove_pattern = r"[^(a-z)(A-Z)(0-9)(р.)(т.)(+)(-)(%)]"

# для добавления данных сделки в итог
def add_trade_in_total_stat(data, old_data, new_trades, total_stat):
    total_stat['count'] += new_trades
    total_stat['amount'] += get_trade_amount(data=data, old_data=old_data)
    price = data[titles[3]]['price']
    if total_stat['average_price']:
        total_stat['average_price'] += price
        total_stat['average_price'] /= 2
    else:
        total_stat['average_price'] = price

# нахождение объема
def get_trade_amount(data, old_data):
    amount = get_number(data[titles[4]]['amount']) - get_number(old_data[titles[4]]['amount'])
    return amount

# получение текста без лишних символов
def get_clear_text(dirty_text):
    # price = children[1].find('span', class_="red").get_text().replace(u'\xa0', u' ')
    return re.sub(remove_pattern, '', dirty_text)

# получение числа
def get_number(string):
    if isinstance(string, int):
        return string

    num = int(re.sub(r"\D", '', string))
    return num

# получение данных из строки
def get_data(tr):
    data = {}
    data['id'] = tr['id']

    # children = [child.get_text(strip=True) for child in tr.find_all('td', recursive=False)]
    children = tr.find_all('td', recursive=False)

    # Биржевой инструмент 0
    data[titles[0]] = children[0].find('a').get_text() # Конденсат газовый стабильный, ст. Пурпе (ст. отпр.)

    # Предл. 1
    try:
        supply = {}
        supply['price'] = children[1].find('span', class_="red").get_text()
        supply['price'] = get_clear_text(supply['price'])
        supply['amount'] = children[1].find('span', class_="gray").get_text()
        supply['amount'] = get_clear_text(supply['amount'])
        data[titles[1]] = supply
    except AttributeError:
        data[titles[1]] = { 'price': 0, 'amount': 0 }

    # Спрос 2
    try:
        demand = {}
        demand['price'] = children[2].find('span', class_="green").get_text()
        demand['price'] = get_clear_text(demand['price'])
        demand['amount'] = children[2].find('span', class_="gray").get_text()
        demand['amount'] = get_clear_text(demand['amount'])
        data[titles[2]] = demand
    except AttributeError:
        data[titles[2]] = { 'price': 0, 'amount': 0 }

    # Ср.вз. цена 3
    try:
        average = {}
        average['percent'] = children[3].find('span', class_="green").get_text()
        average['percent'] = get_clear_text(average['percent'])
        average['price'] = children[3].find(text=True)
        average['price'] = get_number(get_clear_text(average['price']))
        data[titles[3]] = average
    except AttributeError:
        data[titles[3]] = { 'percent': 0, 'price': 0 }

    # Объем договоров 4
    try:
        size = {}
        size['amount'] = children[4].find('span', class_="gray").get_text()
        size['amount'] = get_clear_text(size['amount'])
        size['cost'] = children[4].find(text=True)
        size['cost'] = get_clear_text(size['cost'])
        data[titles[4]] = size
    except AttributeError:
        data[titles[4]] = { 'amount': 0, 'cost': 0 }

    # Кол - во дог. 5
    try:
        trades_count = children[5].find(text=True)
        trades_count = get_clear_text(trades_count)
        data[titles[5]] = int(trades_count)
    except ValueError:
        data[titles[5]] = 0

    # НПЗ 6
    try:
        company_name = children[6].find(text=True)
        company_name = get_clear_text(company_name)
        data[titles[6]] = company_name
    except ValueError:
        data[titles[6]] = '-'

    return data['id'], data

# проверка на наличие новых сделок
def check_new_trades(data, old_data):
    return (get_number(data[titles[5]]) - get_number(old_data[titles[5]]))

# генерация сообщения для бота
def generate_msg(data, old_data=None, new_trades=1):
    title = data[titles[0]]
    id = data['id']

    # На бирже ПРОИЗОШЛА!!! "СДЕЛКА!!!" на "ГАЗОВЫЙ КОНДЕНСАТ" по "ЦЕНЕ" в "ОБЪЁМЕ"
    if old_data:
        msg = 'На бирже ПРОИЗОШЛА!!! "СДЕЛКА!!!"'
        if new_trades > 1:
            msg = 'На бирже ПРОИЗОШЛИ!!! "СДЕЛКИ!!!" (%s)' % new_trades

        price = data[titles[3]]['price']
        amount = get_trade_amount(data, old_data)

        msg += ' на "{0}"(id={1}) по "ЦЕНЕ"({2}р.) в "ОБЪЁМЕ"({3}т.)' \
            .format(
            title,  # Биржевой инструмент
            id,
            price,  # Ср.вз. цена
            amount # Объем
        )
        return msg

    # На бирже появилось "ПРЕДЛОЖЕНИЕ" на "ГАЗОВЫЙ КОНДЕНСАТ" по "ЦЕНЕ" в "ОБЪЁМЕ"
    # На бирже появился "СПРОС" на "ГАЗОВЫЙ КОНДЕНСАТ" по "ЦЕНЕ" в "ОБЪЁМЕ"
    if data[titles[1]]['amount']:
        msg = 'На бирже появилось "ПРЕДЛОЖЕНИЕ"'
        price = data[titles[1]]['price']
        amount = get_number(data[titles[1]]['amount'])
    else:
        msg = 'На бирже появился "СПРОС"'
        price = data[titles[2]]['price']
        amount = get_number(data[titles[2]]['amount'])
    msg += ' на "{0}"(id={1}) по "ЦЕНЕ"({2}р.) в "ОБЪЁМЕ"({3}т.)' \
            .format(
            title,  # Биржевой инструмент
            id,
            price,  # Ср.вз. цена
            amount # Объем
        )
    return msg


def run_bot(positions, total_stat, dispatcher, chat_id, add_link=True):
    # На некоторых сайтах стоит минимальная защита и они не отдают контент без user-agent
    # headers = {'user-agent': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'}
    # чтобы избежать кэширования на любом уровне, на всякий случай добавим случайно число
    url = 'http://spimex.com/markets/oil_products/trades/?r=' + str(random.random())
    # url = 'http://spimex.com/markets/oil_products/trades/game/'
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')

    # # тестовая страничка
    # r = open('./example_page/Ход торгов в Секции «Нефтепродукты».html')
    # soup = BeautifulSoup(r, 'html.parser')

    # # попытка получить html с выполненным js
    # session = dryscrape.Session()
    # session.visit(url)
    # response = session.body()
    # soup = BeautifulSoup(response, "lxml")


    tds = soup.find_all('td', class_='td_name')
    search_pattern = re.compile(r"(конденсат газовый)|(газовый конденсат)", re.IGNORECASE)
    print('%s инструментов по url ' % tds, url)

    for td in tds:
        if not search_pattern.search(td.text):
            continue
        msg = ''

        # строка-родитель ячейки с нужным текстом
        tr = td.find_previous('tr')
        id, data = get_data(tr)

        if id in positions: # если позиция не новая
            old_data = positions[id]
            new_trades = check_new_trades(data=data, old_data=old_data)
            if new_trades > 0: # > 0 для тестов
                positions[id] = data
                msg = generate_msg(data=data, old_data=old_data, new_trades=new_trades)
                add_trade_in_total_stat(data=data, old_data=old_data, new_trades=new_trades, total_stat=total_stat)
        else:
            positions[id] = data
            msg = generate_msg(data=data)

        if msg:
            parse_mode = None
            disable_web_page_preview = None

            if add_link:
                parse_mode = 'HTML'
                disable_web_page_preview = True
                a = tr.find('a', attrs={"title": "Информация об инструменте"})
                msg += '\r\n'
                msg += str(a)

            print(msg)

            dispatcher.bot.send_message(
                chat_id=chat_id,
                text=msg,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview
            )

