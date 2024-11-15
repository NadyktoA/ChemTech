# app = application
# btn = button
# cnt = count
# cond/conds = conditions
# curr = current
# info = information
# init = initialization
# lang = language
# ui = user interface
import os
import sys
import traceback
from functools import partial

from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QLabel, QMenuBar, QMenu, QAction, QGridLayout,
                             QPushButton, QMessageBox, QListWidget, QListWidgetItem, QGroupBox,
                             QVBoxLayout, QInputDialog, QSizePolicy, QToolTip)
from PyQt5.QtCore import Qt, QEvent, QCoreApplication, QRect, QMetaObject, QTranslator
from PyQt5.QtGui import QFont, QMouseEvent, QCursor, QIcon
from openpyxl import load_workbook

from components_library_window import ComponentsLibrary
from stream_properties_window import StreamProperties
from apparatuses_palette_window import ApparatusesPalette

translate_dir = "./translations"


class Worksheet(QMainWindow):
    def __init__(self, app):
        super().__init__()

        self.streams = {}
        self.windows = {}

        self.file_is_created = False
        self.app = app

        self.ui = WorksheetUI()
        self.ui.setup_ui(self)
        self.set_lang()

    def set_lang(self):
        self.curr_lang = "English"
        self.translators = []  # the installed dictionaries will be stored here
        self.lang_changed(self.curr_lang)

    def lang_changed(self, lang):
        """install dictionaries in the app"""

        def set_translators():
            for i in self.translators:
                self.app.installTranslator(i)

        def del_translators():
            for i in self.translators:
                self.app.removeTranslator(i)

        if lang == "English":
            self.ui.action_english.setChecked(True)
            self.ui.action_russian.setChecked(False)
            self.curr_lang = "English"
        else:
            self.ui.action_russian.setChecked(True)
            self.ui.action_english.setChecked(False)
            self.curr_lang = "Russian"

        del_translators()  # remove current dictionaries from the app
        self.translators.clear()  # clear the dictionary list

        # get a list of files containing dictionaries
        file_list: list[str] = [os.path.join(translate_dir, lang, i) for i in os.listdir(os.path.join(translate_dir, lang))]

        for i in file_list:  # add dictionaries to the list and upload them to the application
            self.translators.append(QTranslator())
            self.translators[-1].load(i)

        set_translators()
        self.ui.retranslate_ui(self, self.file_is_created)
        self.translate_stream_info(self.file_is_created, lang)

    def translate_stream_info(self, flag, lang):
        if flag:
            library_path = None

            if lang == "English":
                # когда классов будет много. попросим выбрать нужный класс (локализацию узнаем по программе и допишем в название библиотеки через str)
                # standard_folder = "D:/Other prjects on Py/ChemTech/libs"
                # self.library_path = QFileDialog.getOpenFileName(self, "Open Library File", standard_folder)[0]

                library_path = "./libs/Hydrocarbons_C1-C10_en.xlsx"  # пока класс один делаем так
            elif lang == "Russian":
                # standard_folder = "D:/Other prjects on Py/ChemTech/libs"
                # self.library_path = QFileDialog.getOpenFileName(self, "Open Library File", standard_folder)[0]

                library_path = "./libs/Hydrocarbons_C1-C10_ru.xlsx"

            workbook = load_workbook(library_path)  # загрузили библиотеку с нужной локализацией
            sheet_vals = list(workbook["General Information"].values)

            for stream_key in list(self.streams.keys()):
                stream = self.streams[stream_key]
                for comp_key in list(stream.comps.keys()):
                    comp_id = stream.comps[comp_key].general_info.classification.id  # номер компонента,чей перевод нам нужен (класс в-ва известен)
                    string_number = int(comp_id) + 1  # первые две строчки названия свойств (не нужны) (нумерация с нуля)

                    props = sheet_vals[string_number][0:4]  # перевод только в classification, остальные данные - числа
                    stream.comps[comp_key].general_info.classification.get_props("General Information", "Classification", props)  # вставка новых св-в

                    if stream_key in self.streams.keys():
                        self.windows[stream_key].ui.retranslate_ui(self.windows[stream_key])
                        self.windows[stream_key].load_data_to_comps_table()
                        self.windows[stream_key].load_data_to_composition_table()
                        self.windows[stream_key].load_data_to_conds_table()

    def create_new_file(self):
        if self.file_is_created:
            self.message_issue_recreate_new_file = QMessageBox(self)
            self.message_issue_recreate_new_file.setWindowTitle(self.ui.translate("Worksheet Window", "Error"))
            self.message_issue_recreate_new_file.setText(
                self.ui.translate("Worksheet Window", "The ability to recreate a new file has not yet been added"))
            self.message_issue_recreate_new_file.show()
        else:
            self.ui.start_label.deleteLater()  # delete a object

            self.init_worksheet_ui()

            self.file_is_created = True
            self.ui.retranslate_ui(self, self.file_is_created)

    def init_worksheet_ui(self):
        self.ui.create_workspace(self)
        self.ui.create_workspace_layout()

    def open_components_library(self):
        streams_cnt = self.ui.streams_list.count()
        if self.curr_lang == "English":
            stream_name = f"Stream {str(streams_cnt + 1)}"
        else:
            stream_name = f"Поток {str(streams_cnt + 1)}"

        self.components_library = ComponentsLibrary(stream_name, self)
        self.components_library.show()

    def open_apparatuses_palette(self):
        self.apparatuses_window = ApparatusesPalette(self)
        self.apparatuses_window.show()

    def open_apparatus_window(self, item):
        apparatus_name = item.text()
        self.windows[apparatus_name].update_combobox()
        self.windows[apparatus_name].show()

    def rename_item(self, list_widget):
        # Получаем текущий выбранный элемент
        curr_item = list_widget.currentItem()
        old_name = curr_item.text()
        if curr_item:
            # Запрашиваем новое имя через диалог
            new_name, ok = QInputDialog.getText(self, self.ui.translate("Worksheet Window", "Rename"),
                                                self.ui.translate("Worksheet Window", "Enter a new name:"), text=curr_item.text())
            # в Python все пустые коллекции (пустые списки, кортежи, множества, словари), числа ноль (0, 0.0) и None считаются ложными значениями.
            if ok and new_name and (new_name != old_name):
                # Меняем имя элемента
                curr_item.setText(new_name)

                self.windows[new_name] = self.windows[old_name]
                del self.windows[old_name]
                print(self.windows)

                if list_widget == self.ui.streams_list:
                    self.streams[new_name] = self.streams[old_name]
                    del self.streams[old_name]
                    self.windows[new_name].name = new_name  # change attribute "name" in stream_properties_window

    def delete_item(self, list_widget):
        # Удаляем текущий выбранный элемент
        curr_item = list_widget.currentItem()
        if curr_item:
            row = list_widget.row(curr_item)
            name = list_widget.takeItem(row).text()

            if list_widget == self.ui.streams_list:
                del self.streams[name]
                del self.windows[name]
            elif list_widget == self.ui.apparatuses_list:
                del self.windows[name]


class WorksheetUI:
    def setup_ui(self, worksheet):
        self.worksheet = worksheet
        self.worksheet.resize(1024, 768)
        self.worksheet.setWindowIcon(QIcon("./pics/program_icon.png"))

        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.worksheet.setSizePolicy(size_policy)

        self.central_widget = QWidget(self.worksheet)
        self.central_widget.setSizePolicy(size_policy)
        self.worksheet.setCentralWidget(self.central_widget)

        self.create_menubar(self.worksheet)
        self.create_layout(self.central_widget)

    def create_menubar(self, parent):
        self.menubar = QMenuBar(parent)
        self.menubar.setFont(QFont("Segoe UI", 10))
        parent.setMenuBar(self.menubar)

        self.file_menu = QMenu(self.menubar)
        self.file_menu.setFont(QFont("Segoe UI", 10))
        self.action_load = QAction(parent)
        self.action_save = QAction(parent)
        self.action_create = QAction(parent)

        self.file_menu.addAction(self.action_load)
        self.file_menu.addAction(self.action_save)
        self.file_menu.addAction(self.action_create)

        self.action_create.triggered.connect(self.worksheet.create_new_file)

        self.settings_menu = QMenu(self.menubar)
        self.settings_menu.setFont(QFont("Segoe UI", 10))
        self.lang_menu = QMenu(self.settings_menu)
        self.lang_menu.setFont(QFont("Segoe UI", 10))
        self.action_russian = QAction(parent)
        self.action_russian.setCheckable(True)
        self.action_russian.triggered.connect(partial(parent.lang_changed, "Russian"))
        self.action_english = QAction(parent)
        self.action_english.setCheckable(True)
        self.action_english.triggered.connect(partial(parent.lang_changed, "English"))

        self.settings_menu.addMenu(self.lang_menu)
        self.lang_menu.addAction(self.action_russian)
        self.lang_menu.addAction(self.action_english)

        self.menubar.addMenu(self.file_menu)
        self.menubar.addMenu(self.settings_menu)

    def create_layout(self, parent):
        self.layout = QGridLayout(parent)

        self.start_label = QLabel(parent)
        self.start_label.setFont(QFont("Segoe UI", 10))
        self.start_label.setAlignment(Qt.AlignCenter)

        self.layout.addWidget(self.start_label)

        parent.setLayout(self.layout)

    def create_workspace(self, parent):
        self.black_border = QGroupBox(parent)
        self.black_border.setStyleSheet("QGroupBox{border: 3px solid black;}")

        self.create_labels(parent)
        self.create_btns_add(parent)
        self.create_streams_list(parent)
        self.create_apparatuses_list(parent)

    def create_labels(self, parent):
        self.label_streams = QLabel(parent)
        self.label_streams.setFont(QFont("Segoe UI", 10))
        self.label_streams.setFixedSize(200, 20)
        self.label_streams.setStyleSheet("background-color: rgb(186, 174, 255);")
        self.label_streams.setAlignment(Qt.AlignCenter)

        self.label_apparatuses = QLabel(parent)
        self.label_apparatuses.setFont(QFont("Segoe UI", 10))
        self.label_apparatuses.setFixedSize(200, 20)
        self.label_apparatuses.setStyleSheet("background-color: rgb(186, 174, 255);")
        self.label_apparatuses.setAlignment(Qt.AlignCenter)

    def create_btns_add(self, parent):
        self.btn_add_stream = QPushButton(parent)
        self.btn_add_stream.setFont(QFont("Segoe UI", 10))
        self.btn_add_stream.setFixedSize(200, 30)
        self.btn_add_stream.clicked.connect(parent.open_components_library)

        self.btn_add_apparatus = QPushButton(parent)
        self.btn_add_apparatus.setFont(QFont("Segoe UI", 10))
        self.btn_add_apparatus.setFixedSize(200, 30)
        self.btn_add_apparatus.clicked.connect(parent.open_apparatuses_palette)

    def create_streams_list(self, parent):
        self.streams_list = QListWidget(parent)
        self.streams_list.setFont(QFont("Segoe UI", 10))
        self.streams_list.setFixedWidth(200)

        self.streams_list.itemDoubleClicked.connect(lambda item: parent.windows[item.text()].show())

        # Устанавливаем контекстное меню
        # (полагаю, что контекстное меню предполагает использование именно правого клика, потому как нигде больше это не прописано)
        self.streams_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.streams_list.customContextMenuRequested.connect(lambda pos, s_list=self.streams_list: self.show_context_menu(pos, s_list))

        # отслеживаем положение курсора при работе со списком
        self.streams_list.setMouseTracking(True)
        # если мышь наводится на элемент списка запускаем фукнцию создания подсказки
        self.streams_list.itemEntered.connect(self.display_tooltip)
        self.streams_list.setToolTipDuration(10000)

    def display_tooltip(self, item):
        if item:
            stream = self.worksheet.streams[item.text()]

            t = str(stream.conds["Temperature [C]"])
            p = str(stream.conds["Pressure [Pa]"])

            procent_mass, procent_mol = "", ""
            if self.worksheet.curr_lang == "English":
                t, p = t + " C", p + " Pa"
                procent_mass, procent_mol = ' % mass', ' % mol'
            elif self.worksheet.curr_lang == "Russian":
                t, p = t + " С", p + " Па"
                procent_mass, procent_mol = ' % мас.', ' % мол.'

            text = self.create_streams_tooltip_text(stream, t, p, procent_mass, procent_mol)

            item.setToolTip(text)  # к объекту, на котором находится мышь, привязываем подсказку с нужным текстом
            QToolTip.setFont(QFont("Segoe UI", 10))  # подсказка создана и привязана к объекту, а значит можно менять ее шрифт

    @staticmethod
    def create_streams_tooltip_text(stream, t, p, procent_mass, procent_mol):
        # Формирование HTML таблицы для выравненного текста подсказки
        text = '<table>'
        text += '<tr> <td style="text-align: left;">' + f'T = {t}' + '</td> </tr>'
        text += '<tr> <td style="text-align: left;">' + f'P = {p}' + '</td> </tr>'
        for idx, comp in enumerate(list(stream.comps.keys())):
            name = stream.comps[comp].general_info.classification.name
            frac, procent = 0, "error"
            if stream.fracs[comp]["Molar Fraction"] != "empty":
                frac = stream.fracs[comp]["Molar Fraction"]
                procent = procent_mol
            elif stream.fracs[comp]["Mass Fraction"] != "empty":
                frac = stream.fracs[comp]["Mass Fraction"]
                procent = procent_mass
            text += '<tr>'
            text += '<td style="text-align: left;">' + f'{name}:' + '</td>'
            text += '<td style="text-align: right;">' + f'{(float(frac) * 100):.2f}' + procent + '</td>'
            text += '</tr>'
        text += '</table>'

        return text

    def create_apparatuses_list(self, parent):
        self.apparatuses_list = QListWidget(parent)
        self.apparatuses_list.setFont(QFont("Segoe UI", 10))
        self.apparatuses_list.setFixedWidth(200)
        self.apparatuses_list.itemDoubleClicked.connect(self.worksheet.open_apparatus_window)

        self.apparatuses_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.apparatuses_list.customContextMenuRequested.connect(lambda pos, a_list=self.apparatuses_list: self.show_context_menu(pos, a_list))

    def show_context_menu(self, pos, list_widget):
        # Создаем контекстное меню
        menu = QMenu(self.central_widget)

        # Определяем действия
        action_rename_item = QAction(self.translate("Worksheet Window", "Rename"), self.central_widget)
        action_delete_item_from_list = QAction(self.translate("Worksheet Window", "Delete"), self.central_widget)

        action_rename_item.triggered.connect(partial(self.worksheet.rename_item, list_widget))
        action_delete_item_from_list.triggered.connect(partial(self.worksheet.delete_item, list_widget))

        # Добавляем действия в меню
        menu.addAction(action_rename_item)
        menu.addAction(action_delete_item_from_list)

        # Отображаем меню
        # mapToGlobal(pos):
        # преобразует локальные координаты pos элемента list_widget (позиции мыши на экране вашего виджета) в глобальные координаты экрана.
        # pos — это  координаты мыши, где должно открываться контекстное меню
        # exec_ вызывает контекстное меню (или любое другое меню), в позиции (глобальные координаты) переданной в виде аргумента
        menu.exec_(list_widget.mapToGlobal(pos))

    def create_workspace_layout(self):
        self.layout.addWidget(self.black_border, 0, 0, 3, 1)
        self.layout.addWidget(self.label_streams, 0, 1)
        self.layout.addWidget(self.label_apparatuses, 0, 2)
        self.layout.addWidget(self.streams_list, 1, 1)
        self.layout.addWidget(self.apparatuses_list, 1, 2)
        self.layout.addWidget(self.btn_add_stream, 2, 1)
        self.layout.addWidget(self.btn_add_apparatus, 2, 2)

    def retranslate_ui(self, parent, flag):
        self.translate = QCoreApplication.translate

        parent.setWindowTitle(self.translate("Worksheet Window", "Worksheet"))
        self.file_menu.setTitle(self.translate("Worksheet Window", "File"))
        self.settings_menu.setTitle(self.translate("Worksheet Window", "Settings"))
        self.lang_menu.setTitle(self.translate("Worksheet Window", "Language"))
        self.action_load.setText(self.translate("Worksheet Window", "Load"))
        self.action_save.setText(self.translate("Worksheet Window", "Save"))
        self.action_create.setText(self.translate("Worksheet Window", "Create"))
        self.action_create.setShortcut(self.translate("Worksheet Window", "Ctrl+C"))
        self.action_russian.setText(self.translate("Worksheet Window", "Russian"))
        self.action_english.setText(self.translate("Worksheet Window", "English"))

        if flag:
            self.label_streams.setText(self.translate("Worksheet Window", "Streams"))
            self.label_apparatuses.setText(self.translate("Worksheet Window", "Apparatuses"))

            self.btn_add_stream.setText(self.translate("Worksheet Window", "Add..."))
            self.btn_add_apparatus.setText(self.translate("Worksheet Window", "Add..."))
        else:
            self.start_label.setText(self.translate("Worksheet Window", 'Welcome, Dear User!' + "\n" +
                                                    'Press "Ctrl + C" to create a new file' + "\n" +
                                                    'Press "Ctrl + O" to open a file'))
