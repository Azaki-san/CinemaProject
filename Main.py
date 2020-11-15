import sys
import sqlite3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QWidget, QLabel, QTextEdit, QPushButton, \
    QPlainTextEdit, QLineEdit, QMessageBox, QInputDialog, QFileDialog, QHBoxLayout, QDialog, QVBoxLayout
from PyQt5 import QtWidgets

from first_window import Ui_first_window
from buy_tickets_interface import Ui_tickets_inter
from admin_mode import Ui_admin_window
from data_form import Ui_data_input


class ReadOnlyDelegate(QtWidgets.QStyledItemDelegate):  # блокиратор редактирования таблицы
    def createEditor(self, parent, option, index):  # пользователем
        return


class FirstWindow(QMainWindow, Ui_first_window):
    def __init__(self):
        super(FirstWindow, self).__init__()
        self.setupUi(self)
        self.setWindowTitle('Cinema')
        con = sqlite3.connect("cinema_films.db")
        cur = con.cursor()
        res = cur.execute("""SELECT * FROM films""").fetchall()
        self.res = res
        '''Настройка изначальной таблицы в user режиме'''
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setHorizontalHeaderLabels(['Название фильма', 'Дата и время показа',
                                                    'Жанр', 'Продолжительность',
                                                    'Стоимость билета'])
        self.tableWidget.setRowCount(0)
        # Заполняем таблицу элементами
        for i, row in enumerate(res):
            delegate = ReadOnlyDelegate(self.tableWidget)
            self.tableWidget.setItemDelegateForRow(i, delegate)  # убираем функцию изменения табл.
            self.tableWidget.setRowCount(
                self.tableWidget.rowCount() + 1)
            for j, elem in enumerate(row[1:]):
                self.tableWidget.setItemDelegateForColumn(j, delegate)
                self.tableWidget.setItem(
                    i, j, QTableWidgetItem(str(elem)))
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.clicked.connect(self.show_information)
        self.admin_btn.clicked.connect(self.check_password)

    def show_information(self):  # открытие виджета с постером и описанием фильма
        now_row = self.tableWidget.currentRow() + 1
        self.arg = InfoWindow()
        self.arg.show()
        self.arg.setWindowTitle(self.tableWidget.item(now_row - 1, 0).text())
        self.arg.add_info(now_row)

    def check_password(self):  # попытка входа в admin режим
        password, ok = QInputDialog.getText(self, 'Auth', 'Введите админ-пароль:', QLineEdit.Password)
        flag = False
        if password == '':
            QMessageBox.warning(None, 'Warning', 'Вы же ничего не ввели...')
            flag = True

        elif password != 'AdminModeOn':
            QMessageBox.warning(None, 'Warning', 'Неправильный пароль')
            flag = True
        if not flag:
            self.am = AdminMode()
            self.am.update_table()
            self.am.show()
            self.close()


class AdminMode(QMainWindow, Ui_admin_window):
    def __init__(self):
        super(AdminMode, self).__init__()
        self.setupUi(self)
        self.setWindowTitle('Admin Cinema')
        self.add_btn.clicked.connect(self.adding_film)
        self.upd_btn.clicked.connect(self.update_table)
        self.return_btn.clicked.connect(self.return_back)
        self.flag = False

    def return_back(self):  # функция возврата к user режиму
        self.normal_mode = FirstWindow()
        self.normal_mode.show()
        self.close()

    def update_table(self):
        """Избегаю проблем с выскакиванием сообщения о выборе следующей проверкой"""

        self.check_update = False
        if self.flag:
            self.tableWidget.doubleClicked.disconnect(self.choice_need)
        self.con = sqlite3.connect("cinema_films.db")
        self.cur = self.con.cursor()
        res = self.cur.execute("""SELECT * FROM films""").fetchall()

        self.tableWidget.setColumnCount(5)
        self.tableWidget.setHorizontalHeaderLabels(['Название фильма', 'Дата и время показа',
                                                    'Жанр', 'Продолжительность',
                                                    'Стоимость билета'])
        self.tableWidget.setRowCount(0)

        for i, row in enumerate(res):
            delegate = ReadOnlyDelegate(self.tableWidget)
            self.tableWidget.setItemDelegateForRow(i, delegate)
            self.tableWidget.setRowCount(
                self.tableWidget.rowCount() + 1)
            for j, elem in enumerate(row[1:]):
                self.tableWidget.setItemDelegateForColumn(j, delegate)
                self.tableWidget.setItem(
                    i, j, QTableWidgetItem(str(elem)))
        self.tableWidget.doubleClicked.connect(self.choice_need)
        self.flag = True
        self.tableWidget.resizeColumnsToContents()

    def adding_film(self):  # открытие окошка с добавлением фильма в базу
        self.form_active = DataInputForm()
        self.form_active.show()

    def choice_need(self):  # окошко с выбором, что сделать с фильмом
        self.reply = QDialog()
        vbox = QVBoxLayout()
        label_dialog = QLabel()
        label_dialog.setText('Выберите действие')
        btn_delete = QPushButton(self.reply)
        btn_delete.setText("Удалить")
        btn_delete.clicked.connect(self.deleting_film)
        btn_change = QPushButton(self.reply)
        btn_change.setText('Редактировать')
        btn_change.clicked.connect(self.editing_film)
        layout = QHBoxLayout()
        layout.addWidget(btn_delete)
        layout.addWidget(btn_change)
        vbox.addWidget(label_dialog)
        vbox.addSpacing(20)
        vbox.addLayout(layout)
        self.reply.setLayout(vbox)
        self.reply.exec()

    def editing_film(self):  # окно с редактированием фильма
        self.reply.hide()
        if not self.check_update:
            now_row = self.tableWidget.currentRow() + 1
            self.form_active = DataInputForm()
            self.form_active.show()
            self.check_update = True
            title = self.tableWidget.item(now_row - 1, 0).text()
            time = self.tableWidget.item(now_row - 1, 1).text()
            self.form_active.setWindowTitle(title)
            self.form_active.start_editing(title, time)
        else:
            self.update_table()

    def deleting_film(self):
        self.reply.hide()
        if not self.check_update:
            valid = QMessageBox.question(
                self, '', "Вы уверены?",
                QMessageBox.Yes, QMessageBox.No)
            if valid == QMessageBox.Yes:
                now_row = self.tableWidget.currentRow() + 1
                title = self.tableWidget.item(now_row - 1, 0).text()
                time = self.tableWidget.item(now_row - 1, 1).text()
                self.cur.execute("""DELETE FROM Films
                                WHERE title = ? AND date_time = ?""", (title, time))
                self.con.commit()

                res = self.cur.execute('''SELECT title, date_time FROM Films''').fetchall()
                save_for_halls = []
                save_normal = []
                for i in res:  # далее привожу дату к нужному формату (мой личный)
                    save_normal.append([i[0], i[1]])
                    old_n_date = '_'.join(i[0].split()) + '_' + '_'.join(i[1].split())
                    old_n_date = old_n_date.replace('.', '')
                    old_n_date = old_n_date.replace(':', '')
                    a = ''
                    for i in old_n_date:
                        if i.isalnum() or i == '_':
                            a += i
                    save_for_halls.append(a)
                need_in_request = f'id,{",".join(save_for_halls)}'

                '''Уделение фильма из базы с расстановкой мест'''
                request_first = 'CREATE TEMPORARY TABLE Hall_backup('
                request_two = 'INSERT INTO Hall_backup SELECT '
                request_three = 'CREATE TABLE Hall('
                request_fourth = 'INSERT INTO Hall SELECT '

                request_first += f'{need_in_request})'
                request_two += f'{need_in_request} FROM Hall'
                request_three += f'{need_in_request})'
                request_fourth += f'{need_in_request} FROM Hall_backup'

                self.cur.execute(request_first)
                self.cur.execute(request_two)
                self.cur.execute("DROP TABLE Hall")
                self.cur.execute(request_three)
                self.cur.execute(request_fourth)
                self.cur.execute('DROP TABLE Hall_backup')
                self.con.commit()

                for i in range(len(save_for_halls)):
                    self.cur.execute("""UPDATE Films
                                        SET id = ?
                                        WHERE title = ? AND date_time = ?""", (i + 1,
                                                                               save_normal[i][0],
                                                                               save_normal[i][1]))
                self.con.commit()

                QMessageBox.information(None, 'Ready', 'Успех')
        self.update_table()


class DataInputForm(QWidget, Ui_data_input):
    def __init__(self):
        super(DataInputForm, self).__init__()
        self.setupUi(self)

        self.poster_btn.clicked.connect(self.upload_poster)
        self.write_data.clicked.connect(self.writing_database)

    def upload_poster(self):
        self.fname = QFileDialog.getOpenFileName(self, 'Выбрать постер', '')[0]
        self.poster_btn.setText('Загружено')

    def writing_database(self):
        try:  # тут мы пытаемся добавить фильм
            flag = False
            self.poster_btn.setText('Image')
            self.title, self.genre = self.title_inp.text(), self.genre_inp.text()
            self.data_time, self.duration = self.data_time_inp.text(), int(self.duration_inp.text())
            self.price, self.director = int(self.price_inp.text()), self.director_inp.text()

            self.year, self.description = int(self.year_inp.text()),\
                                          self.description_inp.toPlainText()
            '''Проверка на формат изображения, жанр, название и т.д.'''
            if (self.fname[-3] + self.fname[-2] + self.fname[-1] not in ['jpg', 'png', 'bmp'] or
                self.title == '' or self.genre == '' or self.data_time == '' or self.duration == '' or
                self.price == '' or self.director == '' or self.year == '' or
                self.description == '') and len(self.fname) < 150:
                raise Exception

            con = sqlite3.connect("cinema_films.db")
            cur = con.cursor()
            res = cur.execute('''SELECT id FROM Films''').fetchall()

            new_id = res[-1][0] + 1

            '''Далее я пытаюсь перевести постер в бинарный код и затем уже обновляю таблицу'''
            if len(self.fname) < 150:
                fin = open(self.fname, "rb")
                img = fin.read()
                binary = sqlite3.Binary(img)
            else:
                binary = self.fname
                flag = True

            try:
                '''Это нужно уже для обновления таблицы и редактирования, функции связаны'''
                comm = f'DELETE FROM Films WHERE title = ? AND ' \
                       f'date_time = ? AND genre = ? AND' \
                       f' duration = ? ' \
                       f'AND price = ? AND photo = ? AND ' \
                       f'description = ? AND director = ?' \
                       f' AND year = ?'

                cur.execute(comm, (self.title_old, self.time_old, self.old_genre,
                                   self.old_duration,
                                   self.old_price, self.old_poster, self.old_description,
                                   self.old_director, self.old_year))
            except Exception:
                pass
            '''Добавление в базу'''
            q = f"INSERT INTO Films(id,title,date_time,genre,duration,price,photo,description," \
                f"director,year) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

            cur.execute(q, (new_id, self.title, self.data_time, self.genre, self.duration,
                            self.price, binary, self.description, self.director, self.year))

            self.changing_string()

            if not flag:
                try:
                    q = f"ALTER TABLE Hall ADD COLUMN '{self.a}' STRING"
                    cur.execute(q)

                    for i in range(1, 131):
                        q = f'UPDATE Hall SET "{self.a}" = "True" WHERE id = {i}'
                        cur.execute(q)
                    con.commit()
                except Exception:
                    pass
            else:

                new_name = self.a
                self.title = self.title_old
                self.data_time = self.time_old
                self.changing_string()

                cur.execute(f'ALTER TABLE Hall RENAME COLUMN {self.a} TO {new_name}')

            QMessageBox.information(None, 'Ready', 'Успех.')
            con.commit()
            res = cur.execute('SELECT title, date_time FROM Films').fetchall()
            for i in range(len(res)):
                cur.execute("""UPDATE Films
                                SET id = ?
                                WHERE title = ? AND date_time = ?""", (i + 1,
                                                                        res[i][0],
                                                                        res[i][1]))
            con.commit()
            self.hide()

        except Exception:
            QMessageBox.warning(None, 'Warning', 'Ошибка при загрузке.')

    def changing_string(self):
        """Преобразование в нужный формат"""
        old_n_date = '_'.join(self.title.split()) + '_' + '_'.join(self.data_time.split())
        old_n_date = old_n_date.replace('.', '')
        old_n_date = old_n_date.replace(':', '')

        self.a = ''

        for i in old_n_date:
            if i.isalnum() or i == '_':
                self.a += i

    def start_editing(self, title, time):
        """Редактирование фильма, загрузка информации в окно"""
        con = sqlite3.connect('cinema_films.db')
        self.title_old, self.time_old = title, time

        cur = con.cursor()
        res = cur.execute('''SELECT * FROM Films
                            WHERE title = ? AND date_time = ?''',
                          (self.title_old, self.time_old)).fetchone()

        self.title_inp.setText(res[1])

        self.old_date_time, self.old_genre = res[2], res[3]
        self.old_duration, self.old_price = str(res[4]), str(res[5])
        self.old_director, self.old_year = res[8], str(res[9])
        self.old_description, self.old_poster = res[7], res[6]

        self.data_time_inp.setText(res[2])
        self.genre_inp.setText(res[3])
        self.duration_inp.setText(str(res[4]))
        self.price_inp.setText(str(res[5]))
        self.director_inp.setText(res[8])
        self.year_inp.setText(str(res[9]))
        self.description_inp.setText(res[7])
        self.poster_btn.setText('Загружено')
        self.fname = res[6]


class InfoWindow(QWidget):
    def __init__(self):
        super(InfoWindow, self).__init__()
        '''Далее расставляю объекты по экрану'''
        self.setGeometry(300, 100, 600, 800)
        self.poster = QLabel(self)
        self.poster.resize(300, 450)
        self.poster.move(5, 5)

        self.description = QTextEdit(self)
        self.description.resize(590, 320)
        self.description.move(5, 470)
        self.description.setFontPointSize(10)
        self.description.setDisabled(True)

        self.director = QLabel(self)
        self.director.resize(250, 20)
        self.director.move(315, 90)
        self.director.setFont(QFont('Arial', 10))

        self.year = QLabel(self)
        self.year.resize(250, 20)
        self.year.move(315, 120)
        self.year.setFont(QFont('Arial', 10))

        self.btn = QPushButton(self)
        self.btn.resize(225, 140)
        self.btn.move(340, 200)
        self.btn.setStyleSheet(settings_cr)
        self.btn.setText('Выбор билетов')
        self.btn.setFont(QFont('Arial', 12))
        self.btn.clicked.connect(self.open_bilets)

    def add_info(self, id):
        self.id_need = id

        con = sqlite3.connect("cinema_films.db")
        cur = con.cursor()
        res = cur.execute("""SELECT * FROM Films
                            WHERE id = ?""", (id,)).fetchall()[0]

        self.name = res[1]  # название фильма
        self.data = res[2]  # дата и время проката

        fout = open(f'poster{id}.jpg', 'wb')

        fout.write(res[6])  # вытаскиваю изображение из базы данных
        self.poster.setScaledContents(True)  # размер изображения == размеру poster
        self.pixmap = QPixmap(f'poster{id}.jpg')
        self.poster.setPixmap(self.pixmap)

        self.description.setText(res[7])
        self.director.setText(f"Режиссёр: {res[8]}")
        self.year.setText(f'Год выпуска: {res[9]}')

    def open_bilets(self):
        self.hide()
        self.bilets = Main()
        self.bilets.show()
        self.bilets.get_id(self.id_need, self.name, self.data)
        self.bilets.start_loading()
        self.bilets.setWindowTitle(self.name)


class Main(QMainWindow, Ui_tickets_inter):
    def __init__(self):
        super(Main, self).__init__()
        self.setupUi(self)
        self.bilets = 0
        self.dict_buttons = {}  # словарь нужен для понимания, нажата ли кнопка
        self.save_bilets = []  # список для загрузки в него row счётчика места в зале
        self.next_btn.clicked.connect(self.buying)

    def button_clicked(self):
        sender = self.sender()
        '''Ниже изменяются цвета кнопок при ненажатом значении и нажатом соответственно'''
        ''' Проверяются количество выбранных билетов --> кнопка Далее включается и выключается'''
        if not self.dict_buttons[sender][0]:
            self.bilets -= 1
            sender.setStyleSheet(settings)
            self.save_bilets.remove(self.dict_buttons[sender])
            self.dict_buttons[sender][0] = True
        else:
            self.bilets += 1
            self.dict_buttons[sender][0] = False
            self.save_bilets.append(self.dict_buttons[sender])
            sender.setStyleSheet(settings_pressed)
        if self.bilets > 0 and not self.next_btn.isEnabled():
            self.next_btn.setEnabled(True)
        elif self.bilets == 0 and self.next_btn.isEnabled():
            self.next_btn.setEnabled(False)

    def changing_string(self):
        old_n_date = '_'.join(self.name.split()) + '_' + '_'.join(self.data_time.split())
        old_n_date = old_n_date.replace('.', '')
        old_n_date = old_n_date.replace(':', '')

        self.a = ''

        for i in old_n_date:
            if i.isalnum() or i == '_':
                self.a += i

    def start_loading(self):
        con = sqlite3.connect("cinema_films.db")
        cur = con.cursor()
        self.data_time = cur.execute("""SELECT date_time FROM Films
                                WHERE id = ?""", (int(self.need_id),)).fetchone()[0]
        self.changing_string()
        command = f'SELECT {self.a} FROM Hall'
        res = cur.execute(command).fetchall()
        '''Вытаскиваю цену, пришел к выводу, что легче все таки еще раз пройтись курсором'''
        '''Чем тащить через все классы'''
        self.price = cur.execute('''SELECT * FROM Films
                                WHERE id = ?''', (int(self.need_id),)).fetchall()[0][5]

        row, col = 1, 1  # столбец и номер кнопки
        col_correct = 1  # на вывод нужен, считает место в ряду
        a = []
        '''Три цикла далее вытаскивают и сортируют "места" (кнопки) в зале'''
        for i in range(11):
            a.append(self.first_row.itemAtPosition(0, i).widget())
        for i in range(13):
            a.append(self.second_row.itemAtPosition(0, i).widget())
        for i in range(7):
            for j in range(15):
                a.append(self.others_rows.itemAtPosition(i, j).widget())

        for i in a:
            '''Установка стилей, подводка курсора к кнопкам'''
            if res[col][0] == 'True':
                i.setStyleSheet(settings)
                i.clicked.connect(self.button_clicked)
                self.dict_buttons[i] = [True, row, col_correct, col]
            else:
                i.setStyleSheet(settings_red)

            col += 1
            col_correct += 1
            if col in [12, 25, 40, 55, 70, 85, 100, 115]:  # расчёт места и ряда, для удобства
                row += 1
                col_correct = 1

    def get_id(self, need_id, name, data):  # функция передачи id в класс, а также название фильма
        self.need_id = need_id
        self.name = name
        self.data = data

    def buying(self):
        self.entering_email = EmailConfirm()
        if self.price not in self.save_bilets:
            self.save_bilets.append(self.price)
        self.entering_email.working(self.save_bilets, self.name, self.data)
        self.hide()
        self.entering_email.show()


class EmailConfirm(QWidget):
    def __init__(self):
        super(EmailConfirm, self).__init__()
        self.setGeometry(400, 300, 800, 400)
        self.setWindowTitle('Подтверждение')
        self.setStyleSheet("background-color: rgb(170, 255, 255);")

        self.info_message = QLabel(self)
        self.info_message.setText('Выбрано:')
        self.info_message.move(10, 10)
        self.info_message.setFont(QFont('Arial', 18))

        self.row_col_bilets = QPlainTextEdit(self)
        self.row_col_bilets.move(10, 50)
        self.row_col_bilets.resize(780, 200)
        self.row_col_bilets.setFont(QFont('Arial', 18))
        self.row_col_bilets.setStyleSheet("""
                                    font: bold italic;
                                    color: black;
                                    background-color: rgb(170, 255, 255);
                                                        """)

        self.email_input_info = QLabel(self)
        self.email_input_info.move(10, 265)
        self.email_input_info.setFont(QFont('Arial', 13))
        self.email_input_info.setText('Адрес электронной почты')

        self.email_input = QLineEdit(self)
        self.email_input.move(290, 265)
        self.email_input.resize(445, 25)
        self.email_input.setFont(QFont('Arial', 13))

        self.send_bilets = QPushButton(self)
        self.send_bilets.setStyleSheet(settings_blue)
        self.send_bilets.setText('Приобрести')
        self.send_bilets.setFont(QFont('Arial', 13))
        self.send_bilets.move(600, 320)
        self.send_bilets.clicked.connect(self.sending_email)

        self.info_bar = QLabel(self)
        self.info_bar.move(10, 350)
        self.info_bar.setFont(QFont('Arial', 16))
        self.info_bar.resize(580, 40)

    def working(self, bilets, name, data):
        self.save_bilets = bilets  # пригодится в будущем для обновления базы данных
        self.name = name
        self.data = data
        self.input_data = ''
        a = ''
        for i in bilets:

            if isinstance(i, int):
                a = f'Итого: {i * (len(bilets) - 1)} рублей'
            else:
                self.input_data = self.input_data + f'{i[1]} ряд {i[2]} место\n'
        self.input_data += a
        self.row_col_bilets.setPlainText(self.input_data)

    def sending_email(self):
        mail = self.email_input.text()
        if mail != '':
            if self.info_bar.text() != '':
                self.info_bar.setText('')
            try:
                self.allright_send_mail(mail)
                self.update_data_base()
                self.info_bar.setText('Успешно. Подтверждение отправлено.')
                self.send_bilets.setEnabled(False)
            except Exception:
                self.info_bar.setText('Ошибка. Проверьте правильность ввода.')
        else:
            self.info_bar.setText('Ошибка. Проверьте правильность ввода.')

    def allright_send_mail(self, addr_to):
        addr_from = "cinema.projectyal.2020@gmail.com"
        password = "Parol123"

        msg = MIMEMultipart()
        msg['From'] = addr_from
        msg['To'] = addr_to
        msg['Subject'] = f'Ура! Билеты на фильм "{self.name}" забронированы'
        body = f"Всё отлично! Ваши билеты в кинотеатр успешно забронированы.\n" \
               f"{self.input_data}"
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)  # Коннектим гугол
        server.starttls()  # Начинаем шифрованный обмен по TLS
        server.login(addr_from, password)  # Получаем доступ
        server.send_message(msg)
        server.quit()

    def update_data_base(self):
        con = sqlite3.connect("cinema_films.db")
        cur = con.cursor()

        old_n_date = '_'.join(self.name.split()) + '_' + '_'.join(self.data.split())
        old_n_date = old_n_date.replace('.', '')
        old_n_date = old_n_date.replace(':', '')

        n_date = ''

        for i in old_n_date:
            if i.isalnum() or i == '_':
                n_date += i

        for i in self.save_bilets:
            if not isinstance(i, int):
                a = f"UPDATE Hall SET '{n_date}' = 'False' WHERE id = ?"
                cur.execute(a, (i[3] + 1,))
        con.commit()


settings_blue = "background-color: rgb(0, 170, 255);\n" \
                "border-width: 2px;\n" \
                "border-radius: 10px;\n" \
                "padding: 6px;\n" \
                "\n" \
                "}\n" \
                "QPushButton:hover{    \n" \
                "border-style: outset;\n" \
                "color: white;" \
                "effect = QtWidgets.QGraphicsDropShadowEffect(QPushButton)\n" \
                "effect.setOffset(0, 0)\n" \
                "effect.setBlurRadius(20)\n" \
                "effect.setColor(QColor(57, 219, 255))\n" \
                "QPushButton.setGraphicsEffect(effect)"

settings_cr = "background-color: rgb(85, 255, 127);\n" \
              "border-width: 2px;\n" \
              "border-radius: 10px;\n" \
              "color: rgb(0, 85, 255);" \
              "border-style: inset;\n" \
              "padding: 6px;\n" \
              "\n" \
              "}\n" \
              "QPushButton:hover{    \n" \
              "border-style: outset;\n" \
              "color: rgb(255, 255, 255);" \
              "border-color: rgb(255, 255, 255);\n" \
              "effect = QtWidgets.QGraphicsDropShadowEffect(QPushButton)\n" \
              "effect.setOffset(0, 0)\n" \
              "effect.setBlurRadius(20)\n" \
              "effect.setColor(QColor(57, 219, 255))\n" \
              "QPushButton.setGraphicsEffect(effect)"

settings = "background-color: rgb(85, 255, 127);\n" \
           "border-width: 2px;\n" \
           "border-radius: 10px;\n" \
           "color: rgb(85, 255, 127);" \
           "border-style: inset;\n" \
           "padding: 6px;\n" \
           "\n" \
           "}\n" \
           "QPushButton:hover{    \n" \
           "border-style: outset;\n" \
           "color: rgb(0, 85, 255);" \
           "border-color: rgb(255, 255, 255);\n" \
           "effect = QtWidgets.QGraphicsDropShadowEffect(QPushButton)\n" \
           "effect.setOffset(0, 0)\n" \
           "effect.setBlurRadius(20)\n" \
           "effect.setColor(QColor(57, 219, 255))\n" \
           "QPushButton.setGraphicsEffect(effect)"

settings_pressed = "background-color: rgb(255, 170, 0);\n" \
                   "border-width: 2px;\n" \
                   "border-radius: 10px;\n" \
                   "color: white;" \
                   "border-style: outset;\n" \
                   "padding: 6px;\n"

settings_red = "background-color: red;\n" \
               "border-width: 2px;\n" \
               "border-radius: 10px;\n" \
               "color: red;" \
               "border-style: inset;\n" \
               "padding: 6px;\n" \
               "\n" \
               "}\n" \
               "QPushButton:hover{    \n" \
               "border-style: outset;\n" \
               "color: white;" \
               "border-color: red;\n" \
               "effect = QtWidgets.QGraphicsDropShadowEffect(QPushButton)\n" \
               "effect.setOffset(0, 0)\n" \
               "effect.setBlurRadius(20)\n" \
               "effect.setColor(QColor(57, 219, 255))\n" \
               "QPushButton.setGraphicsEffect(effect)"

if __name__ == '__main__':
    app = QApplication(sys.argv)
    auth = FirstWindow()
    auth.show()
    sys.exit(app.exec())
