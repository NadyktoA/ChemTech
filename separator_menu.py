import traceback

import numpy as np
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QMainWindow, QTableWidget, QTableWidgetItem, QLineEdit, QFormLayout, QHBoxLayout, QComboBox,
    QAction, QVBoxLayout, QWidget, QGridLayout, QLabel, QTabWidget, QStatusBar, QListWidgetItem, QPushButton, QLayout)
from PyQt5.QtGui import QPixmap

from stream import Stream
from separator_window import Separator



class SeparatorMenu(QWidget):
    def __init__(self, streams, streams_list):
        super().__init__()

        self.streams = streams
        self.streams_list = streams_list

        self.init_UI()

    def init_UI(self):
        self.setWindowTitle('Separator')
        # self.resize(800, 500)
        self.setFixedSize(930, 630)

        self.create_tabs()

    def create_tabs(self):
            self.layout = QVBoxLayout(self)
            self.tabs = QtWidgets.QTabWidget(self)
            self.create_design_tab()
            self.layout.addWidget(self.tabs)
            self.setLayout(self.layout)

    def create_design_tab(self):
        try:
            self.connections = QWidget()
            self.tabs.addTab(self.connections, "Connections")
            self.connections.layout = QGridLayout(self)

            self.pic_label = QtWidgets.QLabel(self)
            pic = QPixmap('./pics/Separator.PNG')
            self.pic_label.setPixmap(pic)
            # self.pic_label.setStyleSheet('border-style: solid; border-width: 1px; border-color: black;')
            self.connections.layout.addWidget(self.pic_label, 0, 1, 22, 1)

            self.connections.layout.addWidget(QLabel('T, C'), 0, 0, 1, 1, Qt.AlignBottom)
            self.separator_T = QLineEdit()
            self.connections.layout.addWidget(self.separator_T, 1, 0, 1, 1, Qt.AlignTop)
            self.connections.layout.addWidget(QLabel('P, Pa'), 2, 0, 1, 1, Qt.AlignBottom)
            self.separator_P = QLineEdit()
            self.connections.layout.addWidget(self.separator_P, 3, 0, 1, 1, Qt.AlignTop)

            inlet_stream_label = QLabel('Inlet stream')
            # inlet_stream_label.setStyleSheet('border-style: solid; border-width: 1px; border-color: black;')
            self.connections.layout.addWidget(inlet_stream_label, 9, 0, 1, 1)
            self.inlet_stream_name_combobox = QComboBox()
            self.inlet_stream_name_combobox.addItem('')
            for stream_name in self.streams.keys():
                self.inlet_stream_name_combobox.addItem(stream_name)
            self.inlet_stream_name_combobox.currentIndexChanged.connect(self.get_stream_property)
            self.connections.layout.addWidget(self.inlet_stream_name_combobox, 10, 0, 1, 1)

            outlet_vapour_stream_label = QLabel('Outlet vapour stream')
            # outlet_vapour_stream_label.setStyleSheet('border-style: solid; border-width: 1px; border-color: black;')
            self.connections.layout.addWidget(outlet_vapour_stream_label, 0, 2, 1, 1)
            self.outlet_vapour_stream_name_combo = QComboBox()
            # self.outlet_vapour_stream_name_combo.setStyleSheet('border-style: solid; border-width: 1px; border-color: black;')
            self.connections.layout.addWidget(self.outlet_vapour_stream_name_combo, 1, 2, 1, 1)

            outlet_liquid_stream_label = QLabel('Outlet liquid stream')
            # outlet_liquid_stream_label.setStyleSheet('border-style: solid; border-width: 1px; border-color: black;')
            self.connections.layout.addWidget(outlet_liquid_stream_label, 20, 2, 1, 1)
            self.outlet_liquid_stream_name_combo = QComboBox()
            # self.outlet_liquid_stream_name_combo.setStyleSheet('border-style: solid; border-width: 1px; border-color: black;')
            self.connections.layout.addWidget(self.outlet_liquid_stream_name_combo, 21, 2, 1, 1)

            # self.outlet_cold_stream_T.returnPressed.connect(self.input_connections_data_status)
            self.fi_value = QLineEdit()
            self.fi_value.setEnabled(False)
            self.connections.layout.addWidget(self.fi_value, 10, 2, 1, 1)

            self.connections.layout.addWidget(QLabel('fi, %'), 9, 2, 1, 1)

            for i in range(self.connections.layout.rowCount()):
                self.connections.layout.setRowStretch(i, 1)
            for i in range(self.connections.layout.columnCount()):
                self.connections.layout.setColumnStretch(i, 1)

            self.connections.layout.setSizeConstraint(QLayout.SetFixedSize)

            # self.btn_calc = QPushButton("Calculate")
            # self.connections.layout.addWidget(self.btn_calc, 12, 11, 1, 2, Qt.AlignBottom)
            # self.btn_calc.clicked.connect(self.calc_separator)

            # extra rows
            # for i in range(0, 20):
            #     self.connections.layout.addWidget(QLabel(''), i, 0, )
            #
            # # extra columns
            # for i in range(0, 7):
            #     self.connections.layout.addWidget(QLabel(''), 0, i, )

            self.connections.setLayout(self.connections.layout)
        except:
            traceback.print_exc()

    def calc_separator(self):
        try:
            self.T = (float(self.separator_T.text()) + 273.15)
            self.P = (float(self.separator_P.text()) * 0.0075)
            # print(self.T, self.P, self.mol_fracs, self.antoine_coeffs, self.flow)
            self.separator = Separator(self.T, self.P, self.mol_fracs, self.antoine_coeffs, self.flow)
            # self.fi1, self.V, self.L, self.x, self.y = self.separator.calc()
            # self.fi_value.setText(str(self.fi1))
            #
            # self.create_outlet_streams(self.x, self.y, self.V, self.L)
        except:
            traceback.print_exc()

    def create_outlet_streams(self, x, y, v, l):
        self.outlet_vapour_stream_name = f"Stream {len(self.streams) + 1}"
        conds_names = list(self.inlet_stream.conds.keys())
        vapour_stream_comps = self.inlet_stream.comps

        self.outlet_vapour_stream = Stream(self.outlet_vapour_stream_name, conds_names, vapour_stream_comps)
        self.outlet_vapour_stream.conds["Temperature [C]"] = str(self.T - 273.15)
        self.outlet_vapour_stream.conds["Pressure [Pa]"] = str(self.P / 0.0075)
        self.outlet_vapour_stream.conds["Mass Flow [kg/sec]"] = str(v[0])

        comp_num = 0
        for comp_name in self.outlet_vapour_stream.fracs.keys():
            self.outlet_vapour_stream.fracs[comp_name]["Molar Fraction"] = str(y[comp_num])
            comp_num += 1

        self.streams[self.outlet_vapour_stream_name] = self.outlet_vapour_stream
        self.streams_list.addItem(QListWidgetItem(self.outlet_vapour_stream_name))
        self.outlet_vapour_stream_name_combo.addItem(self.outlet_vapour_stream_name)
        self.outlet_vapour_stream_name_combo.setCurrentIndex(self.outlet_vapour_stream_name_combo.findText(self.outlet_vapour_stream_name))
        self.outlet_vapour_stream_name_combo.setEnabled(False)

        self.outlet_liquid_stream_name = f"Stream {len(self.streams) + 1}"
        conds_names = list(self.inlet_stream.conds.keys())
        liquid_stream_comps = self.inlet_stream.comps

        self.outlet_liquid_stream = Stream(self.outlet_liquid_stream_name, conds_names, liquid_stream_comps)
        self.outlet_liquid_stream.conds["Temperature [C]"] = str(self.T - 273.15)
        self.outlet_liquid_stream.conds["Pressure [Pa]"] = str(self.P / 0.0075)
        self.outlet_liquid_stream.conds["Mass Flow [kg/sec]"] = str(l[0])

        comp_num = 0
        for comp_name in self.outlet_liquid_stream.fracs.keys():
            self.outlet_liquid_stream.fracs[comp_name]["Molar Fraction"] = str(x[comp_num])
            comp_num += 1

        self.streams[self.outlet_liquid_stream_name] = self.outlet_liquid_stream
        self.streams_list.addItem(QListWidgetItem(self.outlet_liquid_stream_name))
        self.outlet_liquid_stream_name_combo.addItem(self.outlet_liquid_stream_name)
        self.outlet_liquid_stream_name_combo.setCurrentIndex(self.outlet_liquid_stream_name_combo.findText(self.outlet_liquid_stream_name))
        self.outlet_liquid_stream_name_combo.setEnabled(False)

    def get_stream_property(self):
        try:
            if self.inlet_stream_name_combobox.currentText() != '':
                self.inlet_stream = self.streams[self.inlet_stream_name_combobox.currentText()]
                self.mol_fracs = []
                for comp_name in self.inlet_stream.fracs.keys():
                    comp_mol_frac = self.inlet_stream.fracs[comp_name]['Molar Fraction']
                    self.mol_fracs.append(float(comp_mol_frac))
                self.flow = self.inlet_stream.conds["Mass Flow [kg/sec]"]

                self.antoine_coeffs = [0 for _ in range(len(self.mol_fracs))]
                for idx, comp_name in enumerate(list(self.inlet_stream.comps.keys())):
                    comp = self.inlet_stream.comps[comp_name]
                    print(idx, comp_name)
                    a = comp.antoine_eq.antoine_eq_coeffs.a
                    b = comp.antoine_eq.antoine_eq_coeffs.b
                    c = comp.antoine_eq.antoine_eq_coeffs.c
                    self.antoine_coeffs[idx] = [a, b, c]

        except:
            traceback.print_exc()

    def update_combobox(self):
        for stream_name in self.streams.keys():
            if self.inlet_stream_name_combobox.findText(stream_name) == -1:  # if stream not in list, then add it
                self.inlet_stream_name_combobox.addItem(stream_name)
