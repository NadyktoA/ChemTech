# btn = button
# cnt = count
# cond/conds = conditions
# info = information
# init = initialization
# ui = user interface


import traceback

from PyQt5.QtWidgets import (QWidget, QLabel, QMenuBar, QMenu, QAction, QGridLayout,
                             QPushButton, QMessageBox, QListWidget, QListWidgetItem, QGroupBox,
                             QVBoxLayout, QInputDialog)
from PyQt5.QtCore import Qt, QEvent

from components_library_window import ComponentsLibrary
from stream_properties_window import StreamProperties
from apparatuses_window import ApparatusesWindow
from STHE_calculation import Heat_exchanger
from Heat_exchanger_GUI import Heat_exchanger_menu
from separator_menu import SeparatorMenu
from tank_menu import TankMenu
from heater_menu import HeaterMenu


class WorkSheet(QWidget):
    def __init__(self):
        super().__init__()

        self.file_is_created = False

        self.create_start_menu()

    def create_start_menu(self):
        self.setWindowTitle("Work Sheet")
        self.resize(1050, 700)
        self.setMinimumSize(1050, 700)

        self.create_start_label()
        self.create_menubar()

    def create_start_label(self):
        self.start_label = QLabel(self)
        self.start_label.setText('Welcome, Dear User!' + "\n" +
                                 'Press "Ctrl + Q" to create a new file' + "\n" +
                                 'Press "Ctrl + O" to open a file')
        self.start_label.setAlignment(Qt.AlignCenter)

        self.layout = QGridLayout(self)
        self.layout.addWidget(self.start_label)
        self.setLayout(self.layout)

    def create_menubar(self):
        self.menubar = QMenuBar(self)
        self.menubar.setGeometry(0, 0, 1050, 25)

        self.file_menu = QMenu(self.menubar)
        self.file_menu.setTitle("File")
        self.menubar.addMenu(self.file_menu)

        self.settings = QMenu(self.menubar)
        self.settings.setTitle("Settings")
        self.menubar.addMenu(self.settings)

        self.layout_settings = QMenu("Layout", self.menubar)
        self.russian_layout = QAction("Русский", self)
        self.layout_settings.addAction(self.russian_layout)
        self.english_layout = QAction("English", self)
        self.layout_settings.addAction(self.english_layout)
        self.settings.addMenu(self.layout_settings)

        self.open_file = QAction('Open', self)
        self.open_file.setShortcut('Ctrl+O')

        self.create_file = QAction('Create', self)
        self.create_file.setShortcut('Ctrl+Q')
        self.create_file.triggered.connect(self.create_new_file)

        self.file_menu.addAction(self.create_file)
        self.file_menu.addAction(self.open_file)

    def create_new_file(self):
        if not self.file_is_created:
            self.start_label.deleteLater()  # delete a object

            self.init_info_arrays()
            self.init_ui()
        else:
            message_issue_recreate_new_file = QMessageBox(self)
            message_issue_recreate_new_file.setWindowTitle("Error")
            message_issue_recreate_new_file.setText("The ability to recreate a new file has not yet been added")
            message_issue_recreate_new_file.show()

        self.file_is_created = True

    def init_info_arrays(self):
        self.streams = {}
        self.windows = {}
        self.apparatuses = {}

        # characteristics names will be used further
        self.conds_names = ["Temperature [C]", "Pressure [Pa]", "Mass Flow [kg/sec]", "Phase"]

    def init_ui(self):
        self.create_workspace()
        try:
            self.create_labels()
            self.create_btns_add()
            self.create_streams_list()
            self.create_apparatuses_list()

            self.create_work_sheet_layout()
        except:
            traceback.print_exc()

    def create_workspace(self):
        self.white_widget = QWidget(self)
        self.white_widget.setStyleSheet("background-color: rgb(255, 255, 255)")

        self.workspace = QGroupBox(self)
        self.workspace.setStyleSheet("QGroupBox{border: 3px solid black;}")

    def create_labels(self):
        self.label_streams = QLabel(self)
        self.label_streams.setText("Streams")
        self.label_streams.setFixedSize(200, 20)
        self.label_streams.setStyleSheet("background-color: rgb(186, 174, 255);")
        self.label_streams.setAlignment(Qt.AlignCenter)

        self.label_apparatuses = QLabel(self)
        self.label_apparatuses.setText("Apparatuses")
        self.label_apparatuses.setFixedSize(200, 20)
        self.label_apparatuses.setStyleSheet("background-color: rgb(186, 174, 255);")
        self.label_apparatuses.setAlignment(Qt.AlignCenter)

    def create_btns_add(self):
        self.create_btn_add_stream()
        self.create_btn_add_apparatus()

    def create_btn_add_stream(self):
        self.btn_add_stream = QPushButton(self)
        self.btn_add_stream.setText("Add...")
        self.btn_add_stream.setFixedSize(200, 30)

        self.btn_add_stream.clicked.connect(self.open_components_library)

    def open_components_library(self):
        streams_cnt = self.streams_list.count()
        stream_name = f"Stream {str(streams_cnt + 1)}"

        self.components_library = ComponentsLibrary(stream_name, self.streams_list,
                                                    self.streams, self.conds_names)
        self.components_library.show()

    def create_btn_add_apparatus(self):
        self.btn_add_apparatus = QPushButton(self)
        self.btn_add_apparatus.setText("Add...")
        self.btn_add_apparatus.setFixedSize(200, 30)

        self.btn_add_apparatus.clicked.connect(self.open_apparatuses_window)

    def open_apparatuses_window(self):
        self.apparatuses_window = ApparatusesWindow(self.apparatuses, self.apparatuses_list)
        self.apparatuses_window.show()

    def create_streams_list(self):
        self.streams_list = QListWidget(self)
        self.streams_list.setFixedWidth(200)
        self.streams_list.installEventFilter(self)
        try:
            self.streams_list.itemDoubleClicked.connect(self.open_stream_properties)
        except:
            traceback.print_exc()

    def eventFilter(self, source, event):
        try:
            if (event.type() == QEvent.ContextMenu and
                    source is self.streams_list):
                menu = QMenu()
                Delete = menu.addAction('Delete')
                Rename = menu.addAction('Rename')
                action = menu.exec_(event.globalPos())
                # action = menu.exec_(self.mapToGlobal(event.pos()))  # when inside self
                if action == Delete:
                    print(source.model().rowCount())
                    if source.model().rowCount() != 0:
                        print(f"[self.streams] {self.streams}")
                        print(f"[self.windows] {self.windows}")
                        print(self.streams_list.item(source.currentRow()).text())
                        del self.streams[self.streams_list.item(source.currentRow()).text()]
                        del self.windows[self.streams_list.item(source.currentRow()).text()]
                        print(f"[self.streams] {self.streams}")
                        print(f"[self.windows] {self.windows}")
                        source.model().removeRow(source.currentRow())

                elif action == Rename:
                    if source.model().rowCount() != 0:
                        print(self.streams_list.item(source.currentRow()).text())
                        previous_text = self.streams_list.item(source.currentRow()).text()
                        item = source.itemAt(event.pos())

                        text, okPressed = QInputDialog.getText(self, "New name", "New name:", text=item.text())

                        if okPressed and text != '':
                            print(self.streams)
                            self.streams[text] = self.streams.pop(previous_text)
                            print(self.streams)
                            item.setText(text)

                return True
            return super().eventFilter(source, event)
        except:
            traceback.print_exc()

    def open_stream_properties(self, item):  # method itemDoubleClicked has information about clicked item and can pass it to function
        try:
            stream_name = str(item.text())
            if stream_name not in self.windows.keys():  # checks if a StreamProperties Window has been created for this stream
                self.windows[stream_name] = StreamProperties(stream_name,
                                                             self.conds_names,
                                                             self.streams[stream_name])
            self.windows[stream_name].show()
        except:
            traceback.print_exc()

    def create_apparatuses_list(self):
        self.apparatuses_list = QListWidget(self)
        self.apparatuses_list.setFixedWidth(200)

        self.apparatuses_list.itemDoubleClicked.connect(self.open_apparatus_window)

    def open_apparatus_window(self, item):
        apparatus_name = item.text()
        apparatus_id = (apparatus_name.split(" "))[0]
        print(f'[apparatus_id] {apparatus_id}')
        if apparatus_name not in self.windows.keys():
            if apparatus_id == "Heat":
                self.windows[apparatus_name] = Heat_exchanger_menu(self.streams, self.streams_list)
            elif apparatus_id == "Heater":
                self.windows[apparatus_name] = HeaterMenu(self.streams, self.streams_list, self.windows)
            elif apparatus_id == "Separator":
                self.windows[apparatus_name] = SeparatorMenu(self.streams, self.streams_list)
            elif apparatus_id == "Tank":
                self.windows[apparatus_name] = TankMenu(self.streams, self.streams_list)
        self.windows[apparatus_name].update_combobox()
        self.windows[apparatus_name].show()

    def create_work_sheet_layout(self):
        self.layout.addWidget(self.workspace, 0, 0, 3, 1)
        self.layout.addWidget(self.label_streams, 0, 1)
        self.layout.addWidget(self.label_apparatuses, 0, 2)
        self.layout.addWidget(self.streams_list, 1, 1)
        self.layout.addWidget(self.apparatuses_list, 1, 2)
        self.layout.addWidget(self.btn_add_stream, 2, 1)
        self.layout.addWidget(self.btn_add_apparatus, 2, 2)

        self.layout.setMenuBar(self.menubar)
