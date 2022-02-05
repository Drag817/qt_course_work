# Импорт системных библиотек
import sys

# Импорт скачиваемых библиотек
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QDialog, QApplication, QMainWindow, QTableWidgetItem, QListWidgetItem

from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg

# Импорт самописных функций
from functions import *


## Основной класс программы
class MainWindow(QMainWindow):

    # Инициализация основного класса
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi("ui/main_window.ui", self) # подгрузка шаблона, созданного в QT Creator

        # Равнение ширины столбцов главного окна
        self.tableWidget.setColumnWidth(0, 50)
        self.tableWidget.setColumnWidth(2, 200)
        self.tableWidget.setColumnWidth(3, 150)
        self.tableWidget.setColumnWidth(5, 70)
        self.tableWidget.setColumnWidth(6, 70)
        self.tableWidget.setColumnWidth(8, 70)

        # Присвоение функций кнопкам интерфейса
        self.addNewJob.clicked.connect(self.new_job)
        self.changeUser.clicked.connect(self.auth)
        self.Stats.clicked.connect(self.show_stats)
        self.servicesForClient.clicked.connect(self.services_by_client)
        self.tableWidget.cellDoubleClicked.connect(self.detailed_job)
        self.cur_date = datetime.now().timetuple()
        self.yearList.setCurrentText(str(self.cur_date[0]))
        self.monthList.setCurrentIndex(self.cur_date[1] - 1)
        self.adm_clients.triggered.connect(self.admin_clients)
        self.adm_categories.triggered.connect(self.admin_categories)
        self.setEnabled(False)
        self.by_client = ByClient()

    # Метод основного класса, который инициализирует класс авторизации в программе
    def auth(self):
        self.auth_dialog = Auth()
        self.auth_dialog.show() # отображение окна авторизации

    # Метод записи текущего пользователя после авторизации
    def set_user(self, user):
        self.user = user

    # Метод записи роли текущего пользователя после авторизации
    def set_role(self, role):
        self.role = role

    # Метод, вызываемый после успешной авторизации пользователя
    def authorized(self):
        self.show() # отображение главного окна программы
        self.activeList.currentTextChanged.connect(self.all_services)
        self.monthList.currentTextChanged.connect(self.all_services)
        self.yearList.currentTextChanged.connect(self.all_services)
        self.setEnabled(True)
        self.all_services()

    # Метод запроса и вывода активных и завершенных работ
    def all_services(self):
        self.username.setText(self.user)
        if self.role != 'admin':
            self.menu_3.setEnabled(True)
        if self.activeList.currentText() == 'Активные':
            self.status = 1
            self.yearList.setCurrentText(str(self.cur_date[0]))
            self.monthList.setCurrentIndex(self.cur_date[1] - 1)
            self.yearList.setEnabled(False)
            self.monthList.setEnabled(False)
            self.items = prepare_services(global_request(self.status))
            self.fineshed_jobs = prepare_services(global_request(2, self.cur_date[0], self.cur_date[1]))
            self.profit_value = calc_profit(self.fineshed_jobs)

        else:
            self.status = 2
            self.yearList.setEnabled(True)
            self.monthList.setEnabled(True)

            self.items = prepare_services(global_request(
                self.status,
                int(self.yearList.currentText()),
                self.monthList.currentIndex() + 1)
            )

            self.profit_value = calc_profit(self.items)

        self.tableWidget.setRowCount(len(self.items))
        row = 0

        # Заполнение таблицы значениями, полученными из БД
        for el in self.items:
            self.tableWidget.setItem(row, 0, QTableWidgetItem(el['id']))
            self.tableWidget.setItem(row, 1, QTableWidgetItem(el['name']))
            self.tableWidget.setItem(row, 2, QTableWidgetItem(el['low']))
            self.tableWidget.setItem(row, 3, QTableWidgetItem(el['client']))
            self.tableWidget.setItem(row, 4, QTableWidgetItem(el['open_date']))
            self.tableWidget.setItem(row, 5, QTableWidgetItem(el['sum']))
            self.tableWidget.setItem(row, 6, QTableWidgetItem(el['gain']))
            self.tableWidget.setItem(row, 7, QTableWidgetItem(el['close_date']))
            self.tableWidget.setItem(row, 8, self.colored_status(el['status']))
            row += 1

        self.tableWidget.resizeRowsToContents()
        self.profit.setText(f"{self.profit_value}")

    # Метод подсвечивания статусов ремонтов
    def colored_status(self, status):
        self.item = QTableWidgetItem(status)
        self.font = QFont()
        self.font.setBold(True)
        self.font.setPointSize(10)
        if status == 'Закрыт':
            self.item.setForeground(Qt.darkGreen)
            self.item.setFont(self.font)
        if status == 'Отменен':
            self.item.setForeground(Qt.red)
            self.item.setFont(self.font)
        return self.item

    # Метод, который инициализирует окно добавления новой работы
    def new_job(self):
        self.newJob = NewJob()
        self.newJob.update_clients()
        self.newJob.show()

    # Метод, который инициализирует окно с детальной информацией о работе
    def detailed_job(self):
        row = self.tableWidget.currentItem().row()
        id = self.items[row]['id']
        self.detail = Detailed()
        self.detail.fill_data(id)
        self.detail.show()

    # Метод, который инициализирует окно работы со списком клиентов
    def admin_clients(self):
        self.clients_dialog = Clients()
        self.clients_dialog.show()

    # Метод, который инициализирует окно работы со списком категорий
    def admin_categories(self):
        self.category_dialog = Categories()
        self.category_dialog.show()

    # Метод, который инициализирует окно вывода работ по каждому клиенту
    def services_by_client(self):
        self.by_client.show()

    # Метод, который инициализирует окно статистики
    def show_stats(self):
        self.stat = Statistics()
        self.stat.show()


# Класс новой работы
class NewJob(QDialog):

    # Инициализация
    def __init__(self):
        super(NewJob, self).__init__()
        loadUi("ui/newJob.ui", self) # подгрузка шаблона

        # Получение списка категорий
        Categories = prepare_catList(get_catigories())
        self.LoW.addItems(Categories)

        # Присвоение функций кнопкам интерфейса
        self.newClientButton.clicked.connect(self.new_client)
        self.AddJob.clicked.connect(lambda: self.add_job())
        self.Cancel.clicked.connect(lambda: self.close())

    # Метод обновления списка клиентов
    def update_clients(self, added_client=None):
        if added_client:
            Clients = prepare_clients(get_clients())
            self.clientBox.addItem(Clients[-1])
            self.clientBox.setCurrentIndex(len(Clients))
        else:
            Clients = prepare_clients(get_clients())
            self.clientBox.addItems(Clients)

    # Метод добавления нового клиента, инициализирует форму для добавления
    def new_client(self):
        self.newClient = NewClient()
        self.newClient.show()

    # Метод добавления новой работы с минимальной валидацией введенных данных
    def add_job(self):
        if not self.newJobName.text():
            self.label_2.setStyleSheet('color: red')
            self.newJobName.setPlaceholderText('Пропущено значение!')
        if self.clientBox.currentText() == 'Выбрать':
            self.label_4.setStyleSheet('color: red')
        if not self.LoW.selectedItems():
            self.label_3.setStyleSheet('color: red')
        if self.newJobName.text() and self.clientBox.currentText() != 'Выбрать' and self.LoW.selectedItems():
            name = self.newJobName.text()
            client = self.clientBox.currentText()
            LoW = []
            for el in self.LoW.selectedItems():
                LoW.append(el.text())
            comment = self.comment.toPlainText()

            pull_job_to_db(name, client, LoW, comment) # Функция добавления работы в базу данных
            main_window.activeList.setCurrentIndex(0)
            main_window.all_services()
            self.close()


# Класс вывода детальной информации о работе
class Detailed(QDialog):

    def __init__(self):
        super(Detailed, self).__init__()
        loadUi("ui/detailed.ui", self)

        self.changeJob.clicked.connect(lambda: self.apply_changes())
        self.finishJob.clicked.connect(lambda: self.finish_job())
        self.cancelJob.clicked.connect(lambda: self.cancel_job())

    # Метод валидации при редактировании работы
    def is_valid(self):
        if not self.JobName.text():
            self.label_2.setStyleSheet('color: red')
            self.JobName.setPlaceholderText('Пропущено значение!')
        if self.clientBox.currentText() == 'Выбрать':
            self.label_4.setStyleSheet('color: red')
        if not self.LoW.selectedItems():
            self.label_3.setStyleSheet('color: red')
        if self.JobName.text() and self.clientBox.currentText() != 'Выбрать' and self.LoW.selectedItems():
            return True

    # Метод наполнения шаблона формы
    def fill_data(self, id):
        data = get_serv_info(id)

        self.client_indexes = []
        for el in data['clients']:
            self.client_indexes.append(el)

        self.category_indexes = []
        for el in data['categories']:
            self.category_indexes.append(el)

        if data['status'] != 1 and main_window.role == 'admin':
            self.changeJob.setEnabled(False)
            self.finishJob.setEnabled(False)
            self.cancelJob.setEnabled(False)

        categories = prepare_catList(data['categories'])
        clients = prepare_clients(data['clients'])

        self.idLabel.setText(str(data['id']))
        self.JobName.setText(data['name'])

        for el in categories:
            cur_item = QListWidgetItem()
            cur_item.setText(el)
            self.LoW.addItem(cur_item)
            if data['categories'][self.category_indexes[categories.index(el)]]['selected']:
                self.LoW.setCurrentItem(cur_item)

        for el in clients:
            self.clientBox.addItem(el)
            if data['clients'][self.client_indexes[clients.index(el)]]['selected']:
                self.clientBox.setCurrentIndex(clients.index(el) + 1)

        self.comment.setText(data['comment'])

    # Метод внесения изменений в данные о работе
    def change_job(self, status):
        name = self.JobName.text()
        client = self.clientBox.currentText()
        LoW = []
        for el in self.LoW.selectedItems():
            LoW.append(el.text())
        comment = self.comment.toPlainText()
        job_id = int(self.idLabel.text())
        change_job(job_id, name, client, LoW, comment, status)
        main_window.activeList.setCurrentIndex(0)
        main_window.all_services()
        main_window.by_client.fill_data()
        self.close()

    # Метод применеия изменений и возврата работы из "ваплненного" в "активное" состояние
    def apply_changes(self):
        if self.is_valid():
            self.status = 1
            self.change_job(self.status)
            if main_window.role != 'admin':
                job_id = int(self.idLabel.text())
                clear_close_date(job_id)
                main_window.all_services()

    # Метод завершения работы
    def finish_job(self):
        if self.is_valid():
            self.status = 2
            self.change_job(self.status)

    # Метод отмены работы
    def cancel_job(self):
        if self.is_valid():
            self.status = 3
            self.change_job(self.status)


# Класс создания нового клиента
class NewClient(QDialog):

    def __init__(self):
        super(NewClient, self).__init__()
        loadUi("ui/newClient.ui", self)

        self.AddClient.clicked.connect(lambda: self.add_client())
        self.Cancel.clicked.connect(lambda: self.close())

    # Метод добавления нового клиента с валидацией введенных данных
    def add_client(self):
        if not self.newClientName.text():
            self.label_2.setStyleSheet('color: red')
            self.newClientName.setPlaceholderText('Пропущено значение!')
        if not self.newClientPhone.text():
            self.label_3.setStyleSheet('color: red')
            self.newClientPhone.setPlaceholderText('Пропущено значение!')
        if self.newClientName.text() and self.newClientPhone.text():
            self.client_name = self.newClientName.text()
            self.client_phone = self.newClientPhone.text()
            pull_client_to_db(self.client_name, self.client_phone)
            main_window.newJob.update_clients(1)
            self.close()


# Класс авторизации
class Auth(QDialog):
    def __init__(self):
        super(Auth, self).__init__()
        loadUi("ui/auth.ui", self)

        self.Signin.clicked.connect(lambda: self.try_to_auth())
        self.Clear.clicked.connect(lambda: self.clear_inputs())

    # Метод попытки авторизации с валидацией
    def try_to_auth(self):
        if self.Login_field.text():
            if self.Passord_field.text():
                if valid_login(self.Login_field.text()): # Валидация по логину
                    try:
                        self.user, self.role = (valid_pass(self.Login_field.text(), self.Passord_field.text()))
                        if self.role:
                            main_window.set_user(self.user) # объявление пользователя
                            main_window.set_role(self.role) # и его роли
                            self.close()
                            main_window.authorized() # переход в главное окно программы после успешной авторизации

                    except:
                        self.warn_msg.setText('Неверный пароль')
                else:
                    self.warn_msg.setText('Неверный логин')
            else:
                self.warn_msg.setText('Введите пароль!')
        else:
            self.warn_msg.setText('Введите логин!')

    # Очистка полей
    def clear_inputs(self):
        self.Login_field.clear()
        self.Passord_field.clear()


# Класс работы с клиентами
class Clients(QDialog):
    def __init__(self):
        super(Clients, self).__init__()
        loadUi("ui/clients.ui", self)

        self.update_client_list()
        self.clients_list.itemClicked.connect(self.client_data)
        self.addClient.clicked.connect(self.add_client)
        self.changeClient.clicked.connect(self.change_client)
        self.deleteClient.clicked.connect(self.delete_client)

    # Получение из БД и систематизация данных о клиентах
    def update_client_list(self):
        self.clients_list.clear()
        self.clients = get_clients()

        self.client_indexes = []
        for el in self.clients:
            self.client_indexes.append(el)

        self.list_of_clients = prepare_clients(self.clients)
        self.clients_list.addItems(self.list_of_clients)
        self.client_name.clear()
        self.client_name.setPlaceholderText('')
        self.client_phone.clear()
        self.changeClient.setEnabled(False)
        self.deleteClient.setEnabled(False)

    # Метод вывода данных о клиенте
    def client_data(self):
        self.changeClient.setEnabled(True)
        self.deleteClient.setEnabled(True)
        self.client_id = self.clients_list.currentRow()
        self.client_name.setText(self.clients[self.client_indexes[self.client_id]]['name'])
        self.client_phone.setText(self.clients[self.client_indexes[self.client_id]]['phone'])

    # Метод добавления нового клиента
    def add_client(self):
        if self.is_valid():
            self.some_client_name = self.client_name.text()
            self.some_client_phone = self.client_phone.text()
            pull_client_to_db(self.some_client_name, self.some_client_phone)
            self.update_client_list()

    # Метод изменения данных о клиенте
    def change_client(self):
        if self.is_valid():
            self.id = self.client_indexes[self.clients_list.currentRow()]
            self.name = self.client_name.text()
            self.phone = self.client_phone.text()
            change_client_to_db(self.id, self.name, self.phone)
            self.update_client_list()

    # Удаление клиента из БД
    def delete_client(self):
        self.id = self.client_indexes[self.clients_list.currentRow()]
        if delete_client_from_db(self.id):
            self.update_client_list()
        else:
            self.by_client = ByClient()
            self.by_client.fill_data()
            self.by_client.set_client(self.id)
            self.by_client.show()

    # Валидация данных при работе с клиентом
    def is_valid(self):
        if not self.client_name.text():
            self.label.setStyleSheet('color: red')
            self.client_name.setPlaceholderText('Пропущено значение!')
        else:
            self.label.setStyleSheet('color: black')
            return True


# Класс категорий
class Categories(QDialog):
    def __init__(self):
        super(Categories, self).__init__()
        loadUi("ui/categories.ui", self)

        self.update_category_list()
        self.categoryList.itemClicked.connect(self.category_data)
        self.addCategory.clicked.connect(self.add_category)
        self.changeCategory.clicked.connect(self.change_category)
        self.deleteCategory.clicked.connect(self.delete_category)

    # Основной метод получения из БД и систематизиции данных о категориях работ
    def update_category_list(self):
        self.categoryList.clear()
        self.categories = get_catigories()

        self.category_indexes = []
        for el in self.categories:
            self.category_indexes.append(el)

        self.list_of_categories = prepare_catList(self.categories)
        self.categoryList.addItems(self.list_of_categories)
        self.categoryName.clear()
        self.categoryName.setPlaceholderText('')
        self.categoryPrice.clear()
        self.categoryPercent.clear()
        self.changeCategory.setEnabled(False)
        self.deleteCategory.setEnabled(False)

    # Вывод информации по категории в шаблон
    def category_data(self):
        self.changeCategory.setEnabled(True)
        self.deleteCategory.setEnabled(True)
        self.category_id = self.categoryList.currentRow()
        self.categoryName.setText(self.categories[self.category_indexes[self.category_id]]['name'])
        self.categoryPrice.setText(str(self.categories[self.category_indexes[self.category_id]]['price']))
        self.categoryPercent.setText(str(self.categories[self.category_indexes[self.category_id]]['percent']))

    # Метод добавления новой категории
    def add_category(self):
        if self.is_valid():
            self.name = self.categoryName.text()
            self.price = self.categoryPrice.text()
            self.percent = self.categoryPercent.text()
            pull_category_to_db(self.name, self.price, self.percent)
            self.update_category_list()

    # Метод внесения изменений в категорию
    def change_category(self):
        if self.is_valid():
            self.id = self.category_indexes[self.categoryList.currentRow()]
            self.name = self.categoryName.text()
            self.price = self.categoryPrice.text()
            self.percent = self.categoryPercent.text()
            change_category_to_db(self.id, self.name, self.price, self.percent)
            self.update_category_list()

    # Метод удаления категории с валидацией
    def delete_category(self):
        self.id = self.category_indexes[self.categoryList.currentRow()]
        if delete_category_from_db(self.id):
            self.update_category_list()
        else:
            self.deleteCategory.setText('Нельзя удалить элемент!')
            self.deleteCategory.setStyleSheet('color: red')

    # Метод валидации данных при работе с категориями
    def is_valid(self):
        if not self.categoryName.text():
            self.label.setStyleSheet('color: red')
            self.categoryName.setPlaceholderText('Пропущено значение!')
        if not self.categoryPrice.text():
            self.label_2.setStyleSheet('color: red')
        if not self.categoryPercent.text():
            self.label_3.setStyleSheet('color: red')
        if self.categoryName.text() and self.categoryPrice.text() and self.categoryPercent.text():
            self.label.setStyleSheet('color: black')
            self.label_2.setStyleSheet('color: black')
            self.label_3.setStyleSheet('color: black')
            return True


# Класс вывода работ по клиенту
class ByClient(QDialog):
    def __init__(self):
        super(ByClient, self).__init__()
        loadUi("ui/clientServices.ui", self)

        self.tableWidget.setColumnWidth(0, 50)
        self.tableWidget.setColumnWidth(2, 200)
        self.tableWidget.setColumnWidth(3, 150)
        self.tableWidget.setColumnWidth(5, 70)
        self.tableWidget.setColumnWidth(6, 70)
        self.tableWidget.setColumnWidth(8, 70)

        self.tableWidget.cellDoubleClicked.connect(self.detailed_job)
        self.clientBox.currentTextChanged.connect(self.fill_data)
        self.self_get_clients()

    # Метод получения из БД информации о клиентах
    def self_get_clients(self):
        self.clients = get_clients()

        self.clients_id_list = []
        for el in self.clients:
            self.clients_id_list.append(el)

        self.clients_list = prepare_clients(self.clients)
        self.clientBox.addItems(self.clients_list)

    # Метод вывода работ по клиенту
    def set_client(self, on_delete_id):
        self.clientBox.setCurrentIndex(self.clients_id_list.index(on_delete_id) + 1)

        # При переходе в данное окно при уделении клиента,
        # на котором числятся работы - будет выведено предупреждающее сообщение
        self.warn.setText('Не возможно удалить данного клиента,\nт.к. на нем висят следующие работы')

    # Метод заподнения шаблона формы
    def fill_data(self):
        self.warn.clear()
        self.services = get_services_by_client(self.clients_id_list[self.clientBox.currentIndex() - 1])

        self.items = prepare_services(self.services)

        self.tableWidget.setRowCount(len(self.items))
        row = 0
        for el in self.items:
            self.tableWidget.setItem(row, 0, QTableWidgetItem(el['id']))
            self.tableWidget.setItem(row, 1, QTableWidgetItem(el['name']))
            self.tableWidget.setItem(row, 2, QTableWidgetItem(el['low']))
            self.tableWidget.setItem(row, 3, QTableWidgetItem(el['client']))
            self.tableWidget.setItem(row, 4, QTableWidgetItem(el['open_date']))
            self.tableWidget.setItem(row, 5, QTableWidgetItem(el['sum']))
            self.tableWidget.setItem(row, 6, QTableWidgetItem(el['gain']))
            self.tableWidget.setItem(row, 7, QTableWidgetItem(el['close_date']))
            self.tableWidget.setItem(row, 8, QTableWidgetItem(el['status']))
            row += 1

        self.tableWidget.resizeRowsToContents()

        self.gain = 0
        self.profit = 0

        for el in self.services:
            if self.services[el]['status'] == 2:
                self.gain += self.services[el]['sum']
                self.profit += self.services[el]['gain']

        self.Sum.setText(str(self.gain))
        self.Profit.setText(str(int(self.profit)))

    # Метод вывода детальной информации по выбранной работе из списка работ по клиенту
    def detailed_job(self):
        self.row = self.tableWidget.currentItem().row()
        self.id = self.items[self.row]['id']
        self.detail = Detailed()
        self.detail.fill_data(self.id)
        self.detail.show()


# Класс статистики
class Statistics(QMainWindow):

    def __init__(self):
        super(Statistics, self).__init__()
        loadUi("ui/stat.ui", self)

        self.monthList.currentTextChanged.connect(self.month_stat)
        self.yearList.currentTextChanged.connect(self.year_stat)
        self.monthRadioButton.toggled.connect(self.month_stat)
        self.yearRadioButton.toggled.connect(self.year_stat)

        self.cur_date = datetime.now().timetuple()
        self.yearList.setCurrentText(str(self.cur_date[0]))
        self.monthList.setCurrentIndex(self.cur_date[1] - 1)

        # Настройка модуля graphWidget
        self.graphWidget.setBackground('w')
        self.graphWidget.showGrid(x=True, y=True)
        self.graphWidget.addLegend()

        self.month_stat()

    # Метод вывода статистики за месяц
    def month_stat(self):
        self.graphWidget.clear()
        self.monthList.setEnabled(True)

        self.month = self.monthList.currentIndex() + 1
        self.year = int(self.yearList.currentText())

        styles = {'color': 'r', 'font-size': '14px'}
        self.graphWidget.setLabel('bottom', 'День', **styles)
        self.graphWidget.setXRange(0, 32, padding=0)

        # Получение данных о днях, суммам выполненных работ и заработку
        self.days, self.earns, self.gains = get_services_for_statistics(self.year, self.month)
        self.plot(self.days, self.earns, "Работ на сумму", 'b')
        self.plot(self.days, self.gains, "Заработок", 'r')

        self.Sum.setText(str(int(self.earns[-1])))
        self.Profit.setText(str(int(self.gains[-1])))

    # Метод вывода статистики за год
    def year_stat(self):
        if self.monthRadioButton.isChecked():
            self.month_stat()
        else:
            self.graphWidget.clear()
            self.monthList.setEnabled(False)
            self.year = int(self.yearList.currentText())

            styles = {'color': 'r', 'font-size': '14px'}
            self.graphWidget.setLabel('bottom', 'Месяц', **styles)
            self.graphWidget.setXRange(0, 13, padding=0)

            self.months, self.earns, self.gains = get_services_for_statistics(self.year)

            self.stringaxis = pg.AxisItem(orientation='bottom')
            self.stringaxis.setTicks(self.months)

            self.plot(self.months, self.earns, "Работ на сумму", 'b')
            self.plot(self.months, self.gains, "Заработок", 'r')

            self.Sum.setText(str(int(sum(self.earns))))
            self.Profit.setText(str(int(sum(self.gains))))

    # Метод создания полотна для рисования графиков
    def plot(self, x, y, plotname, color):
        self.pen = pg.mkPen(color, width=3)
        self.graphWidget.plot(x, y, name=plotname, pen=self.pen, symbol='o', symbolSize=8)


# Проверка точки входа и инициализация работы программы
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.auth()
    sys.exit(app.exec_())
