# Импорт встроенных модулей
import hashlib
from datetime import datetime
from sql import connection

from config import statuses


# Функция получения категорий из БД
def get_catigories():
    catigories = {} # Инициализация словаря (json) под запись данных из БД

    with connection.cursor() as cursor: # Инициализация соединения с базой данных
        cursor.execute(
            '''SELECT * FROM category;''' # SQL запрос
        )

        # Заполнение словаря полученными данными из БД
        for el in cursor.fetchall():
            catigories.update({
                el[0]: {
                    cursor.description[0][0]: el[0],
                    cursor.description[1][0]: el[1],
                    cursor.description[2][0]: el[2],
                    cursor.description[3][0]: el[3],
                }
            })

    # Вывод заполненого словаря
    return catigories


# Фунция получения клиентов из БД (аналогично - категории)
def get_clients():
    clients = {}

    with connection.cursor() as cursor:
        cursor.execute(
            '''SELECT * FROM client;'''
        )

        for el in cursor.fetchall():
            clients.update({
                el[0]: {
                    cursor.description[0][0]: el[0],
                    cursor.description[1][0]: el[1],
                    cursor.description[2][0]: el[2],
                }
            })

    return clients


# Подготовка полученных данных о категориях, приведение данных к удобочитаемому виду, объединение в список
def prepare_catList(cat):
    list_for_ui = []

    for key in cat:
        list_for_ui.append(f"{cat[key]['name']} ({cat[key]['price']}р.) [{cat[key]['percent']}%]")

    return list_for_ui


# Подготовка полученных данных о клиентах, приведение данных к удобочитаемому виду, объединение в список
def prepare_clients(clients):
    list_for_ui = []

    for key in clients:
        list_for_ui.append(f"{clients[key]['name']} [{clients[key]['phone']}]")

    return list_for_ui


# Вспомогательная функция для приведения списка категорий в работе, к формату для записи в БД
def cat_list_to_db(LoW):
    cat_list = []
    for el in LoW:
        cat_list.append(el.split(' (')[0])

    return cat_list


# Вспомогательная функция для подсчета стоимости и заработка по работе для записи в БД
def catigories_to_db(cat_list):
    catigories = get_catigories()
    cost = 0
    gain = 0

    cat_id_list = []
    for cat in catigories:
        if catigories[cat]['name'] in cat_list:
            cat_id_list.append(catigories[cat]['id'])
            cost += catigories[cat]['price']
            gain += int(catigories[cat]['price'] / 100 * catigories[cat]['percent'])

    return cost, gain, cat_id_list

# Вспомогательная функция для приведения клиента в работе, к формату для записи в БД
def client_to_db(client):
    clients = get_clients()
    for key in clients:
        if client.split(' [')[0] == clients[key]['name']:
            client_id = clients[key]['id']

    return client_id


# Функция для добавления работы в БД
def pull_job_to_db(name, client, LoW, comment):
    open_date = datetime.now() # Дата и время открытия заявки формируется на основании текущих
    status = 1 # Присваивается статус 1 ("В работе") для созданной работы
    cat_list = cat_list_to_db(LoW) # формирование списка категорий с помощью вспомогательной функции
    cost, gain, cat_id_list = catigories_to_db(cat_list) # расчет стимости и заработка с помощью вспомогательной функции
    client_id = client_to_db(client) # приведение данных о клиенте с помощью вспомогательной функции

    with connection.cursor() as cursor:
        cursor.execute(
            # Отправка подготовленных данных в БД
            f'''INSERT INTO service (name, cost, gain, open_date, comment, client_id, status) VALUES 
            ('{name}', {cost}, {gain}, '{open_date}', '{comment}', {client_id}, {status});'''
        )

        # Получение id добавленной работы для занесения категорий в таблицу "многие ко многоим"
        cursor.execute(
            f'''SELECT id FROM service ORDER BY id DESC LIMIT 1'''
        )
        current_service_id = cursor.fetchone()[0]

        exec_ids = ''
        for id in cat_id_list:
            exec_ids += f"({current_service_id}, {id}), "

        # Добавление категорий к новой работе
        cursor.execute(
            f'''INSERT INTO service_category (service_id, category_id) VALUES {exec_ids[:-2]};'''
        )

    # Вызов функции полного обновления данных для запелнения интерфейса программы
    global_request(1)


# Функция полного обновления данных для запелнения интерфейса программы
def global_request(status, year=None, month=None):
    catigories = get_catigories() # Получение спсика категорий
    if year and month: # Оператор для указания временных промежутков (для статистики и пр.)
        date = datetime(year, month, 1)
    else:
        date = datetime.now()

    services = {} # Инициализация словаря (json) под запись данных из БД
    with connection.cursor() as cursor:
        if status == 1:

            # SQL запрос для получения комплексных данных о работах
            cursor.execute(
                f'''SELECT s.id, s.name, STRING_AGG(CAST(cat.id AS VARCHAR), ' ') AS low,
                    CONCAT_WS(' - ', cl.name, cl.phone) AS client, s.open_date, SUM(cat.price),
                    SUM(cat.price / 100 * cat.percent) AS gain, s.close_date, s.status
                    FROM service s LEFT JOIN client cl
                    ON cl.id = s.client_id LEFT JOIN service_category sc
                    ON s.id = sc.service_id LEFT JOIN category cat
                    ON cat.id = sc.category_id
                    WHERE s.status = {status} 
                    GROUP BY s.id, cl.name, cl.phone
                    ORDER BY s.id DESC;'''
            )
        else:

            # Шаблон SQL запроса при работе с временными промежутками
            cursor.execute(
                f"""SELECT s.id, s.name, STRING_AGG(CAST(cat.id AS VARCHAR), ' ') AS low,
                    CONCAT_WS(' - ', cl.name, cl.phone) AS client, s.open_date, SUM(cat.price),
                    SUM(cat.price / 100 * cat.percent) AS gain, s.close_date, s.status 
                    FROM service s LEFT JOIN client cl
                    ON cl.id = s.client_id LEFT JOIN service_category sc
                    ON s.id = sc.service_id LEFT JOIN category cat
                    ON cat.id = sc.category_id
                    WHERE close_date >= date_trunc('month', timestamp '{date}')
                    AND close_date < date_trunc('month', timestamp '{date}' + interval '1' month)
                    AND s.status != 1
                    GROUP BY s.id, cl.name, cl.phone
                    ORDER BY s.id DESC;"""
            )

        # Разбор и занесение полученных из БД данных в словарь
        for el in cursor.fetchall():
            low = []
            sum = 0
            gain = 0
            if el[2]:
                for cat in el[2].split(' '):
                    low.append(int(cat))
                    sum += catigories[int(cat)]['price']
                    gain += catigories[int(cat)]['price'] / 100 * catigories[int(cat)]['percent']

            services.update({
                el[0]: {
                    cursor.description[0][0]: el[0],
                    cursor.description[1][0]: el[1],
                    cursor.description[2][0]: low,
                    cursor.description[3][0]: el[3],
                    cursor.description[4][0]: el[4],
                    cursor.description[5][0]: sum,
                    cursor.description[6][0]: gain,
                    cursor.description[7][0]: el[7],
                    cursor.description[8][0]: el[8],
                }
            })

    return services


# Функция приведения полученных из БД данных для вывода в интерфейс программы
def prepare_services(services):
    catigories = get_catigories()
    serv_list = []

    for key in services:
        close_date = 'Открыта'
        low = ''

        for el in services[key]['low']:
            low += f"- {catigories[el]['name']}\n"

        if services[key]['close_date']:
            close_date = str(services[key]['close_date'].strftime("%m/%d/%Y, %H:%M:%S"))


        serv_list.append({
            'id': str(services[key]['id']),
            'name': services[key]['name'],
            'low': low[:-1],
            'client': services[key]['client'].replace(' - ', '\n'),
            'open_date': str(services[key]['open_date'].strftime("%m/%d/%Y, %H:%M:%S")),
            'sum': str(services[key]['sum']),
            'gain': str(int(services[key]['gain'])),
            'close_date': close_date,
            'status': statuses[services[key]['status']]
        })

    return serv_list


# Функция для подготовки данных для вывода в шаблон детализированой информации по работе
def get_serv_info(id):
    data = {}
    service = []
    low_list = []
    catigories = get_catigories()
    clients = get_clients()

    with connection.cursor() as cursor:
        cursor.execute(
            f'''SELECT s.id, s.name, STRING_AGG(CAST(cat.id AS VARCHAR), ' ') AS low,
                cl.id AS client, s.status, s.comment
                FROM service s LEFT JOIN client cl
                ON cl.id = s.client_id LEFT JOIN service_category sc
                ON s.id = sc.service_id LEFT JOIN category cat
                ON cat.id = sc.category_id
                GROUP BY s.id, cl.id
                HAVING s.id = {id};'''
        )

        for el in cursor.fetchone():
            service.append(el)

    for el in service[2].split(' '):
        low_list.append(int(el))

    # Запись ключей категорий для подсвечивания при выводе в шаблон
    for key in catigories:
        if key in low_list:
            catigories[key].update({
                'selected': True
            })
        else:
            catigories[key].update({
                'selected': False
            })

    # Запись ключа клиента для отображения при выводе в шаблон
    for key in clients:
        if key == service[3]:
            clients[key].update({
                'selected': True
            })
        else:
            clients[key].update({
                'selected': False
            })

    # Запись данных в словарь
    data.update({
        'id': service[0],
        'name': service[1],
        'categories': catigories,
        'clients': clients,
        'status': service[4],
        'comment': service[5]
    })

    return data


# Функция для применения изменений выбранных категорий в работе
def finalize_changes(job_id, cat_id_list):
    with connection.cursor() as cursor:
        cursor.execute(
            f'''DELETE FROM service_category WHERE service_id = {job_id};'''
        )

        exec_ids = ''
        for id in cat_id_list:
            exec_ids += f"({job_id}, {id}), "

        cursor.execute(
            f'''INSERT INTO service_category (service_id, category_id) VALUES {exec_ids[:-2]};'''
        )

    global_request(2)


# Функция для применения изменений в работе
def change_job(job_id, name, client, LoW, comment, status):
    cat_list = cat_list_to_db(LoW)
    cost, gain, cat_id_list = catigories_to_db(cat_list)
    client_id = client_to_db(client)
    values = "name, cost, gain, comment, client_id, status"
    update_values = f"'{name}', {cost}, {gain}, '{comment}', {client_id}, {status}"

    if status != 1:
        close_date = datetime.now()
        values += ", close_date"
        update_values += f", '{close_date}'"

    with connection.cursor() as cursor:
        cursor.execute(
            f'''UPDATE service SET ({values}) = 
                ({update_values}) 
                WHERE id = {job_id};'''
        )

    finalize_changes(job_id, cat_id_list)


# Функция для посчета прибыли по завершенной работе
def calc_profit(jobs):
    profit = 0
    for job in jobs:
        if job['status'] == 'Закрыт':
            profit += int(job['gain'])
    return profit


# Функция добавления клиента в БД
def pull_client_to_db(name, phone):
    with connection.cursor() as cursor:
        cursor.execute(
            f"""INSERT INTO client (name, phone) VALUES ('{name}', '{phone}');"""
        )


# Функция валидации логина при авторизации
def valid_login(login):
    with connection.cursor() as cursor:
        cursor.execute(
            f"""SELECT login FROM users WHERE login = '{login}';"""
        )

        for el in cursor.fetchall():
            if el[0] == login:
                return True


# Функция валидации логина и пароля при авторизации
def valid_pass(login, password):
    key = hashlib.md5(password.encode('utf-8'))

    with connection.cursor() as cursor:
        cursor.execute(
            f"""SELECT pass_hash, name, login FROM users WHERE login = '{login}';"""
        )
        for el in cursor.fetchall():
            if el[0] == key.hexdigest():
                user, role = el[1], el[2]

    return user, role


# Функция для очистки "Даты закрытия" работы при возвращении её в работу
def clear_close_date(id):
    with connection.cursor() as cursor:
        cursor.execute(
            f"""UPDATE service SET close_date = NULL WHERE id = {id};"""
        )


# Функция изменения информации о клиенте
def change_client_to_db(id, name, phone):
    with connection.cursor() as cursor:
        cursor.execute(
            f"""UPDATE client SET name = '{name}', phone = '{phone}' WHERE id = {id};"""
        )


# Функция удаления пользователя из БД (валидация присходит автоматически на уровне БД)
def delete_client_from_db(id):
    cursor = connection.cursor()
    try:
        cursor.execute(
            f"""DELETE FROM client WHERE id = {id};"""
        )
        return True
    except:
        return False
    finally:
        cursor.close()


# Функция добавления новой категории
def pull_category_to_db(name, price, percent):
    with connection.cursor() as cursor:
        cursor.execute(
            f"""INSERT INTO category (name, price, percent) VALUES ('{name}', '{price}', '{percent}');"""
        )


# Функция изменения категории
def change_category_to_db(id, name, price, percent):
    with connection.cursor() as cursor:
        cursor.execute(
            f"""UPDATE category SET name = '{name}', price = '{price}' , percent = '{percent}' WHERE id = {id};"""
        )


# Функция удаления категории
def delete_category_from_db(id):
    cursor = connection.cursor()
    try:
        cursor.execute(
            f"""DELETE FROM category WHERE id = {id};"""
        )
        return True
    except:
        return False
    finally:
        cursor.close()


# Функция запроса работ по клиенту
def get_services_by_client(client_id):
    catigories = get_catigories()

    services = {}
    with connection.cursor() as cursor:
        cursor.execute(
            f"""SELECT s.id, s.name, STRING_AGG(CAST(cat.id AS VARCHAR), ' ') AS low,
                CONCAT_WS(' - ', cl.name, cl.phone) AS client, s.open_date, SUM(cat.price),
                SUM(cat.price / 100 * cat.percent) AS gain, s.close_date, s.status
                FROM service s LEFT JOIN client cl
                ON cl.id = s.client_id LEFT JOIN service_category sc
                ON s.id = sc.service_id LEFT JOIN category cat
                ON cat.id = sc.category_id
                WHERE cl.id = {client_id}
                GROUP BY s.id, cl.name, cl.phone
                ORDER BY s.id DESC;"""
        )

        for el in cursor.fetchall():
            low = []
            sum = 0
            gain = 0
            if el[2]:
                for cat in el[2].split(' '):
                    low.append(int(cat))
                    sum += catigories[int(cat)]['price']
                    gain += catigories[int(cat)]['price'] / 100 * catigories[int(cat)]['percent']

            services.update({
                el[0]: {
                    cursor.description[0][0]: el[0],
                    cursor.description[1][0]: el[1],
                    cursor.description[2][0]: low,
                    cursor.description[3][0]: el[3],
                    cursor.description[4][0]: el[4],
                    cursor.description[5][0]: sum,
                    cursor.description[6][0]: gain,
                    cursor.description[7][0]: el[7],
                    cursor.description[8][0]: el[8],
                }
            })

    return services


# Функция запроса данных для построения графика статистики
def get_services_for_statistics(year, month=None):
    with connection.cursor() as cursor:

        # За месяц
        if month:
            date = datetime(year, month, 1)
            res ={}
            days = []
            earn_list = []
            gain_list = []
            earn = 0
            gain = 0

            cursor.execute(
                f"""SELECT  SUM(cat.price) AS earn, SUM(cat.price / 100 * cat.percent) AS gain, close_date
                    FROM service s LEFT JOIN service_category sc
                    ON s.id = sc.service_id LEFT JOIN category cat
                    ON cat.id = sc.category_id
                    WHERE close_date >= date_trunc('month', timestamp '{date}')
                    AND close_date < date_trunc('month', timestamp '{date}' + interval '1' month)
                    AND s.status = 2
                    GROUP BY close_date"""
            )

            for el in cursor.fetchall():
                if el[2].timetuple()[2] not in days:
                    days.append(el[2].timetuple()[2])

                    res.update({
                        el[2].timetuple()[2]: {
                            'earn': el[0],
                            'gain': el[1]
                        }
                    })

                else:
                    res[el[2].timetuple()[2]]['earn'] += el[0]
                    res[el[2].timetuple()[2]]['gain'] += el[1]

            days = sorted(days)

            for el in days:
                earn += res[el]['earn']
                earn_list.append(earn)
                gain += res[el]['gain']
                gain_list.append(gain)

            return days, earn_list, gain_list

        else:
            # За год
            date = datetime(year, 1, 1)
            res = {}
            months = []
            earn_list = []
            gain_list = []

            cursor.execute(
                f"""SELECT  SUM(cat.price) AS earn, SUM(cat.price / 100 * cat.percent) AS gain, close_date
                    FROM service s LEFT JOIN service_category sc
                    ON s.id = sc.service_id LEFT JOIN category cat
                    ON cat.id = sc.category_id
                    WHERE close_date >= date_trunc('year', timestamp '{date}')
                    AND close_date < date_trunc('year', timestamp '{date}' + interval '1' year)
                    AND s.status = 2
                    GROUP BY close_date"""
            )

            for el in cursor.fetchall():
                if el[2].timetuple()[1] not in months:
                    months.append(el[2].timetuple()[1])

                    res.update({
                        el[2].timetuple()[1]: {
                            'earn': el[0],
                            'gain': el[1]
                        }
                    })
                else:
                    res[el[2].timetuple()[1]]['earn'] += el[0]
                    res[el[2].timetuple()[1]]['gain'] += el[1]

            months = sorted(months)

            for el in months:
                earn_list.append(res[el]['earn'])
                gain_list.append(res[el]['gain'])

            return months, earn_list, gain_list


# Функция для автоматического наполнения заполнения БД данными для тестирования
def testing():
    from random import randint # Импорт случайных чисел

    catigories = get_catigories() # Получаю список категорий

    for year in [2021, 2022]: # Для каждого из 21 и 22 годов
        for month in range(1, 13): # Для каждого месяца
            for job in range(15): # Создаю 15 работ
                if month == 2: # Если февраль - дней 28
                    close_date = datetime(year, month, randint(1, 28))
                else:
                    close_date = datetime(year, month, randint(1, 30))

                cat_list = []

                # Выбираю от 2х до 5ти случайных категорий для одной работы
                for i in range(randint(2, 5)):
                    cat = randint(1, 12)
                    if cat not in cat_list:
                        cat_list.append(cat)

                cost = 0
                gain = 0

                # Подсчет суммы и заработка
                for el in cat_list:
                    cost += catigories[el]['price']
                    gain += int(catigories[el]['price'] / 100 * catigories[el]['percent'])

                # Вношу имя работы, дату открытия, одного из 2х клиентов, статус "Завершен", комментарий
                name = f"{cost}-{gain}"
                open_date = datetime.now()
                client_id = randint(1, 2)
                status = 2
                comment = f"Job #{job}-month #{month}-year #{year}"

                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""INSERT INTO service (name, cost, gain, open_date, close_date, comment, client_id, status) VALUES 
                        ('{name}', {cost}, {gain}, '{open_date}', '{close_date}', '{comment}', {client_id}, {status});"""
                    )

                    cursor.execute(
                        f'''SELECT id FROM service ORDER BY id DESC LIMIT 1'''
                    )

                    current_service_id = cursor.fetchone()[0]

                    exec_ids = ''
                    for id in cat_list:
                        exec_ids += f"({current_service_id}, {id}), "

                    cursor.execute(
                        f'''INSERT INTO service_category (service_id, category_id) VALUES {exec_ids[:-2]};'''
                    )

                # Вывожу лог о добавленной в БД работе в консоль
                print(f"Работа №{job}, месяц: {month}, год: {year}")


if __name__ == "__main__":
    # testing()
    pass
