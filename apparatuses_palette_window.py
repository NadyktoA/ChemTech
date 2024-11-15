import traceback

from PyQt5.QtWidgets import (QMainWindow, QWidget, QPushButton, QApplication, QListWidget, QListWidgetItem, QVBoxLayout,
                             QSizePolicy)
from PyQt5.QtCore import QCoreApplication

from STHE_calculation import Heat_exchanger
from Heat_exchanger_GUI import Heat_exchanger_menu
from separator_window import Separator
from heater_window import Heater


class ApparatusesPalette(QMainWindow):
    def __init__(self, worksheet):
        super().__init__()

        self.worksheet = worksheet
        self.windows = self.worksheet.windows
        self.apparatuses_list = self.worksheet.ui.apparatuses_list

        self.ui = ApparatusesPaletteUI()
        self.ui.setup_ui(self)

    def add_new_apparatus(self):
        btn_text = self.sender().text()

        counter = 1
        for idx in range(self.apparatuses_list.count()):
            item = self.apparatuses_list.item(idx).text()
            if btn_text in item:
                counter += 1

        apparatus_name = f"{btn_text} {counter}"
        self.apparatuses_list.addItem(QListWidgetItem(apparatus_name))

        if apparatus_name not in self.windows.keys():
            match btn_text:
                case "Heater" | "Нагреватель":
                    self.windows[apparatus_name] = Heater(self.worksheet, apparatus_name, "Heater")
                case "Cooler" | "Холодильник":
                    self.windows[apparatus_name] = Heater(self.worksheet, apparatus_name, "Cooler")
                case "Heat Exchanger" | "Теплообменник":
                    self.windows[apparatus_name] = Heat_exchanger_menu(self.worksheet.streams, self.worksheet.ui.streams_list)
                case "Separator" | "Сепаратор":
                    self.windows[apparatus_name] = Separator(self.worksheet, apparatus_name)

        self.close()


class ApparatusesPaletteUI:
    def setup_ui(self, parent):
        parent.resize(400, 140)

        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        parent.setSizePolicy(size_policy)

        self.central_widget = QWidget(parent)
        self.central_widget.setSizePolicy(size_policy)
        parent.setCentralWidget(self.central_widget)

        translate = QCoreApplication.translate
        self.apparatuses_names = [translate("Apparatuses Btns", "Heater"),
                                  translate("Apparatuses Btns", "Cooler"),
                                  translate("Apparatuses Btns", "Heat Exchanger"),
                                  translate("Apparatuses Btns", "Separator"),
                                  ]

        self.create_btns_layout(parent)

        self.retranslate_ui(parent)

    def create_btns_layout(self, parent):
        layout = QVBoxLayout()

        for idx, name in enumerate(self.apparatuses_names):
            btn = QPushButton(name)
            btn.clicked.connect(parent.add_new_apparatus)
            layout.addWidget(btn)

        self.central_widget.setLayout(layout)

    def retranslate_ui(self, parent):
        translate = QCoreApplication.translate

        parent.setWindowTitle(translate("Apparatuses Window", "Select an apparatus"))
