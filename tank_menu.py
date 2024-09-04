import traceback

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QTableWidget, QTableWidgetItem, QLineEdit, QFormLayout, QHBoxLayout, QComboBox, \
    QAction, QVBoxLayout, QWidget, QGridLayout, QLabel, QTabWidget, QStatusBar, QListWidgetItem, QPushButton
from PyQt5.QtGui import QPixmap, QDoubleValidator

from stream import Stream
from separator_calculation import Separator
from tank_calculation import Tank


class TankMenu(QWidget):
    def __init__(self, streams, streams_list):
        super().__init__()

        self.streams = streams
        self.streams_list = streams_list

        self.init_UI()

    def init_UI(self):
        self.setWindowTitle('Tank')
        self.resize(800, 500)

        self.create_tabs()

    def create_tabs(self):
        try:
            self.layout = QVBoxLayout(self)
            self.tabs = QtWidgets.QTabWidget(self)
            self.create_design_tab()
            self.layout.addWidget(self.tabs)
            self.setLayout(self.layout)
        except:
            traceback.print_exc()

    def create_design_tab(self):
        try:
            self.connections = QWidget()
            self.tabs.addTab(self.connections, "Connections")
            self.connections.layout = QGridLayout(self)

            self.pic_label = QtWidgets.QLabel(self)
            pic = QPixmap(r".\tank_pic.png")
            self.pic_label.setPixmap(pic)
            self.connections.layout.addWidget(self.pic_label, 5, 1, 6, 12, Qt.AlignCenter)

            self.connections.layout.addWidget(QLabel('T, C'), 1, 1, 1, 2)
            self.tank_T = QLineEdit()
            self.connections.layout.addWidget(self.tank_T, 2, 1, 1, 2)
            self.connections.layout.addWidget(QLabel('P, Pa'), 3, 1, 1, 2)
            self.tank_P = QLineEdit()
            self.connections.layout.addWidget(self.tank_P, 4, 1, 1, 2)
            self.connections.layout.addWidget(QLabel('D, m'), 5, 1, 1, 2)
            self.tank_D = QLineEdit()
            self.connections.layout.addWidget(self.tank_D, 6, 1, 1, 2)

            self.connections.layout.addWidget(QLabel('Inlet stream'), 7, 2, 1, 1, Qt.AlignBottom)
            self.inlet_stream_name_combobox = QComboBox()
            self.inlet_stream_name_combobox.addItem('')
            for stream_name in self.streams.keys():
                self.inlet_stream_name_combobox.addItem(stream_name)
            self.inlet_stream_name_combobox.currentIndexChanged.connect(self.get_stream_property)
            self.connections.layout.addWidget(self.inlet_stream_name_combobox, 8, 2, 1, 1, Qt.AlignTop)

            # self.connections.layout.addWidget(QLabel('Outlet vapour stream'), 6, 11, 1, 1, Qt.AlignBottom)
            # self.outlet_vapour_stream_name_combo = QComboBox()
            # self.connections.layout.addWidget(self.outlet_vapour_stream_name_combo, 7, 11, 1, 1, Qt.AlignTop)

            # self.connections.layout.addWidget(QLabel('Outlet liquid stream'), 10, 11, 1, 1, Qt.AlignTop)
            # self.outlet_liquid_stream_name_combo = QComboBox()
            # self.connections.layout.addWidget(self.outlet_liquid_stream_name_combo, 10, 11, 1, 1, Qt.AlignBottom)

            # self.outlet_cold_stream_T.returnPressed.connect(self.input_connections_data_status)
            self.fi_value = QLineEdit()
            self.fi_value.setEnabled(False)
            self.connections.layout.addWidget(self.fi_value, 11, 11, 1, 2, Qt.AlignBottom)

            self.connections.layout.addWidget(QLabel('fi, %'), 11, 10, 1, 1, Qt.AlignBottom)

            self.liquid_level_value = QLineEdit()
            self.liquid_level_value.setEnabled(False)
            self.connections.layout.addWidget(self.liquid_level_value, 12, 11, 1, 4, Qt.AlignBottom)

            self.connections.layout.addWidget(QLabel('H, m'), 12, 10, 1, 3, Qt.AlignBottom)

            self.btn_calc = QPushButton("Calculate")
            self.connections.layout.addWidget(self.btn_calc, 13, 11, 1, 4, Qt.AlignBottom)
            self.btn_calc.clicked.connect(self.calc_tank)

            # extra rows
            for i in range(0, 20):
                self.connections.layout.addWidget(QLabel(''), i, 0, )

            # extra columns
            for i in range(0, 7):
                self.connections.layout.addWidget(QLabel(''), 0, i, )

            self.connections.setLayout(self.connections.layout)
        except:
            traceback.print_exc()

    def calc_tank(self):
        try:
            self.T = (float(self.tank_T.text()) + 273)
            self.P = (float(self.tank_P.text()) * 0.0075)
            self.D = float(self.tank_D.text())
            self.tank = Tank(self.T, self.P, self.mol_fracs, self.antoine_coeffs, self.flow, self.D)
            self.fi1, self.x, self.y, self.H = self.tank.calc()
            self.fi_value.setText(str(self.fi1))
            self.liquid_level_value.setText(str(self.H))

            # self.create_outlet_streams(self.x, self.y, self.V, self.L)
        except:
            traceback.print_exc()

    # def create_outlet_streams(self, x, y, v, l):
    # self.outlet_vapour_stream_name = f"Stream {len(self.streams) + 1}"
    # conds_names = list(self.inlet_stream.conds.keys())
    # vapour_stream_comps = self.inlet_stream.comps

    # self.outlet_vapour_stream = Stream(self.outlet_vapour_stream_name, conds_names, vapour_stream_comps)
    # self.outlet_vapour_stream.conds["Temperature [C]"] = str(self.T)
    # self.outlet_vapour_stream.conds["Pressure [Pa]"] = str(self.P)
    # self.outlet_vapour_stream.conds["Mass Flow [kg/sec]"] = str(v[0])

    # comp_num = 0
    # for comp_name in self.outlet_vapour_stream.fracs.keys():
    # self.outlet_vapour_stream.fracs[comp_name]["Molar Fraction"] = str(y[comp_num])
    # comp_num += 1

    # self.streams[self.outlet_vapour_stream_name] = self.outlet_vapour_stream
    # self.streams_list.addItem(QListWidgetItem(self.outlet_vapour_stream_name))
    # self.outlet_vapour_stream_name_combo.addItem(self.outlet_vapour_stream_name)
    # self.outlet_vapour_stream_name_combo.setCurrentIndex(self.outlet_vapour_stream_name_combo.findText(self.outlet_vapour_stream_name))
    # self.outlet_vapour_stream_name_combo.setEnabled(False)

    # self.outlet_liquid_stream_name = f"Stream {len(self.streams) + 1}"
    # conds_names = list(self.inlet_stream.conds.keys())
    # liquid_stream_comps = self.inlet_stream.comps

    # self.outlet_liquid_stream = Stream(self.outlet_liquid_stream_name, conds_names, liquid_stream_comps)
    # self.outlet_liquid_stream.conds["Temperature [C]"] = str(self.T)
    # self.outlet_liquid_stream.conds["Pressure [Pa]"] = str(self.P)
    # self.outlet_liquid_stream.conds["Mass Flow [kg/sec]"] = str(l[0])

    # comp_num = 0
    # for comp_name in self.outlet_liquid_stream.fracs.keys():
    # self.outlet_liquid_stream.fracs[comp_name]["Molar Fraction"] = str(x[comp_num])
    # comp_num += 1

    # self.streams[self.outlet_liquid_stream_name] = self.outlet_liquid_stream
    # self.streams_list.addItem(QListWidgetItem(self.outlet_liquid_stream_name))
    # self.outlet_liquid_stream_name_combo.addItem(self.outlet_liquid_stream_name)
    # self.outlet_liquid_stream_name_combo.setCurrentIndex(self.outlet_liquid_stream_name_combo.findText(self.outlet_liquid_stream_name))
    # self.outlet_liquid_stream_name_combo.setEnabled(False)

    def get_stream_property(self):
        try:
            if self.inlet_stream_name_combobox.currentText() != '':
                self.inlet_stream = self.streams[self.inlet_stream_name_combobox.currentText()]
                self.mol_fracs = []
                for comp_name in self.inlet_stream.fracs.keys():
                    comp_mol_frac = self.inlet_stream.fracs[comp_name]['Molar Fraction']
                    self.mol_fracs.append(float(comp_mol_frac))
                self.flow = self.inlet_stream.conds["Mass Flow [kg/sec]"]

                A, B, C = [], [], []
                for comp_name in self.inlet_stream.comps.keys():
                    comp = self.inlet_stream.comps[comp_name]
                    a = comp.antoine_eq.antoine_eq_coeffs.a
                    A.append(a)
                    b = comp.antoine_eq.antoine_eq_coeffs.b
                    B.append(b)
                    c = comp.antoine_eq.antoine_eq_coeffs.c
                    C.append(c)

                self.antoine_coeffs = [A, B, C]
        except:
            traceback.print_exc()

    def update_combobox(self):
        for stream_name in self.streams.keys():
            if self.inlet_stream_name_combobox.findText(stream_name) == -1:  # if stream not in list, then add
                self.inlet_stream_name_combobox.addItem(stream_name)
