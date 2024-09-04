from PyQt5.QtWidgets import QWidget, QPushButton, QApplication, QListWidget, QListWidgetItem, QVBoxLayout


class ApparatusesWindow(QWidget):
    def __init__(self, apparatuses, apparatuses_list):
        super().__init__()

        self.apparatuses = apparatuses
        self.apparatuses_list = apparatuses_list

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Select an apparatus")
        self.resize(400, 140)

        self.create_btn_heat_exchanger()
        self.create_btn_heater()
        self.create_btn_cooler()
        self.create_btn_separator()
        self.create_btn_tank()

        layout = QVBoxLayout()
        layout.addWidget(self.btn_heat_exchanger)
        layout.addWidget(self.btn_heater)
        layout.addWidget(self.btn_cooler)
        layout.addWidget(self.btn_separator)
        layout.addWidget(self.btn_tank)


        self.setLayout(layout)

    def create_btn_heat_exchanger(self):
        self.btn_heat_exchanger = QPushButton(self)
        self.btn_heat_exchanger.setText("Heat Exchanger")
        self.btn_heat_exchanger.setFixedSize(400, 30)

        self.btn_heat_exchanger.clicked.connect(self.add_new_apparatus)

    def create_btn_heater(self):
        self.btn_heater = QPushButton(self)
        self.btn_heater.setText("Heater")
        self.btn_heater.setFixedSize(400, 30)

        self.btn_heater.clicked.connect(self.add_new_apparatus)

    def create_btn_cooler(self):
        self.btn_cooler = QPushButton(self)
        self.btn_cooler.setText("Cooler")
        self.btn_cooler.setFixedSize(400, 30)

        self.btn_cooler.clicked.connect(self.add_new_apparatus)

    def create_btn_separator(self):
        self.btn_separator = QPushButton(self)
        self.btn_separator.setText("Separator")
        self.btn_separator.setFixedSize(400, 30)

        self.btn_separator.clicked.connect(self.add_new_apparatus)

    def create_btn_tank(self):
        self.btn_tank = QPushButton(self)
        self.btn_tank.setText("Tank")
        self.btn_tank.setFixedSize(400, 30)

        self.btn_tank.clicked.connect(self.add_new_apparatus)

    def add_new_apparatus(self):
        apparatus_name = f"{QApplication.instance().sender().text()}"


        items = []
        counter = 1
        for idx in range(self.apparatuses_list.count()):
            item = self.apparatuses_list.item(idx).text()
            items.append(item)
            if apparatus_name in item:
                counter += 1
        # print(items)
        # print(counter)

        apparatus_name = f"{apparatus_name} {counter}"
        # print(apparatus_name)
        self.apparatuses_list.addItem(QListWidgetItem(apparatus_name))
        self.close()
        # self.apparatuses[apparatus_name] = EGOR's CLASS HEAT EXCHANGER


