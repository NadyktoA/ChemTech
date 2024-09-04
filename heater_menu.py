import traceback

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QTableWidget, QTableWidgetItem, QLineEdit, QFormLayout, QHBoxLayout, QComboBox, \
    QAction, QVBoxLayout, QWidget, QGridLayout, QLabel, QTabWidget, QStatusBar, QListWidgetItem, QPushButton
from PyQt5.QtGui import QPixmap, QDoubleValidator

from stream import Stream
from separator_calculation import Separator
from stream_properties_window import StreamProperties



class HeaterMenu(QWidget):
    def __init__(self, streams, streams_list, windows):
        super().__init__()

        self.streams = streams
        self.streams_list = streams_list
        self.windows = windows

        self.init_UI()

    def init_UI(self):
        self.setWindowTitle('Heater')
        self.resize(800, 500)

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
            pic = QPixmap(r'.\sep_pic.png')
            self.pic_label.setPixmap(pic)
            self.connections.layout.addWidget(self.pic_label, 5, 1, 6, 12, Qt.AlignCenter)

            # self.connections.layout.addWidget(QLabel('T, C'), 1, 1, 1, 2)
            # self.separator_T = QLineEdit()
            # self.connections.layout.addWidget(self.separator_T, 2, 1, 1, 2)
            # self.connections.layout.addWidget(QLabel('P, Pa'), 3, 1, 1, 2)
            # self.separator_P = QLineEdit()
            # self.connections.layout.addWidget(self.separator_P, 4, 1, 1, 2)



            self.connections.layout.addWidget(QLabel('Inlet stream'), 7, 2, 1, 1, Qt.AlignBottom)
            self.inlet_stream_name_combobox = QComboBox()
            self.inlet_stream_name_combobox.addItem('')
            for stream_name in self.streams.keys():
                self.inlet_stream_name_combobox.addItem(stream_name)
            self.inlet_stream_name_combobox.currentIndexChanged.connect(self.get_stream_property)
            self.connections.layout.addWidget(self.inlet_stream_name_combobox, 8, 2, 1, 1, Qt.AlignTop)



            self.connections.layout.addWidget(QLabel('Outlet stream'), 7, 11, 1, 1, Qt.AlignBottom)
            self.outlet_stream_name_combo = QComboBox()
            self.connections.layout.addWidget(self.outlet_stream_name_combo, 8, 11, 1, 1, Qt.AlignTop)

            # self.connections.layout.addWidget(QLabel('Outlet liquid stream'), 10, 11, 1, 1, Qt.AlignTop)
            # self.outlet_liquid_stream_name_combo = QComboBox()
            # self.connections.layout.addWidget(self.outlet_liquid_stream_name_combo, 10, 11, 1, 1, Qt.AlignBottom)

            self.output_T = QLineEdit()
            # self.output_T.setEnabled(False)
            self.connections.layout.addWidget(self.output_T, 9, 11, 1, 2, Qt.AlignBottom)

            self.connections.layout.addWidget(QLabel('T, C'), 9, 10, 1, 1, Qt.AlignBottom)

            self.dep_H = QLineEdit()
            # self.dep_H.setEnabled(False)
            self.connections.layout.addWidget(self.dep_H, 10, 11, 1, 2, Qt.AlignBottom)

            self.connections.layout.addWidget(QLabel('dH, kJ/sec'), 10, 10, 1, 1, Qt.AlignBottom)

            self.btn_calc = QPushButton("Calculate")
            self.connections.layout.addWidget(self.btn_calc, 11, 11, 1, 2, Qt.AlignBottom)
            self.btn_calc.clicked.connect(self.calc_heater)

            # extra rows
            for i in range(0, 20):
                self.connections.layout.addWidget(QLabel(''), i, 0, )

            # extra columns
            for i in range(0, 7):
                self.connections.layout.addWidget(QLabel(''), 0, i, )

            self.connections.setLayout(self.connections.layout)
        except:
            traceback.print_exc()

    def calc_heater(self):
        try:
            if self.output_T.text() != "":
                output_T_value = float(self.output_T.text())
                self.create_outlet_streams(output_T_value, 0, 0)
                self.windows[self.outlet_stream_name] = StreamProperties(self.outlet_stream_name,
                                                                         list(self.inlet_stream.conds.keys()),
                                                                         self.streams[self.outlet_stream_name])

                in_H = self.inlet_stream.props["Mass Enthalpy [kJ/kg]"]
                out_H = self.outlet_stream.props["Mass Enthalpy [kJ/kg]"]
                dep_H = in_H - out_H
                self.dep_H.setText(str(dep_H))
            elif self.dep_H.text() != "":
                in_H = float(self.inlet_stream.props["Mass Enthalpy [kJ/kg]"])
                print(f"[in_H] {in_H}")
                out_H = in_H + float(self.dep_H.text())
                print(f"[out_H] {out_H}")
                counter = 1

                self.in_T = str(self.inlet_stream.conds["Temperature [C]"])
                if out_H > in_H:
                    print("more")
                    self.t_2 = str(500)
                else:
                    self.t_2 = self.in_T
                    self.in_T = str(-273)
                self.create_outlet_streams(self.in_T, out_H, self.t_2)
                self.windows[self.outlet_stream_name] = StreamProperties(self.outlet_stream_name,
                                                                         list(self.inlet_stream.conds.keys()),
                                                                         self.streams[self.outlet_stream_name])
                H_calc = self.outlet_stream.props["Mass Enthalpy [kJ/kg]"]
                print(f'[H_calc] {H_calc}')
                while not (out_H - 0.001 < float(H_calc) < out_H + 0.001):
                    counter += 1
                    del self.windows[self.outlet_stream_name]
                    del self.streams[self.outlet_stream_name]
                    self.streams_list.takeItem(self.streams_list.count() - 1)
                    if float(H_calc) > out_H:
                        self.t_2 = self.T_calc
                        print(f"[self.t_2] {self.t_2}")
                        self.create_outlet_streams(self.in_T, out_H, self.t_2)
                    else:
                        self.in_T = self.T_calc
                        print(f"[self.in_T] {self.in_T}")

                        self.create_outlet_streams(self.in_T, out_H, self.t_2)
                    self.windows[self.outlet_stream_name] = StreamProperties(self.outlet_stream_name,
                                                                             list(self.inlet_stream.conds.keys()),
                                                                             self.streams[self.outlet_stream_name])
                    H_calc = self.outlet_stream.props["Mass Enthalpy [kJ/kg]"]
                    print(f'[H_calc] {H_calc}')
                self.output_T.setText(self.outlet_stream.conds["Temperature [C]"])
                print(f"[counter] {counter}")

        except:
            traceback.print_exc()

    def create_outlet_streams(self, t, out_H, t_2):
        self.outlet_stream_name = f"Stream {len(self.streams) + 1}"
        conds_names = list(self.inlet_stream.conds.keys())
        stream_comps = self.inlet_stream.comps
        if out_H != 0:
            self.outlet_stream = Stream(self.outlet_stream_name, conds_names, stream_comps)
            self.T_calc = str(((float(t) + float(t_2)) / 2))
            self.outlet_stream.conds["Temperature [C]"] = str(((float(t) + float(t_2)) / 2))
            self.outlet_stream.conds["Pressure [Pa]"] = self.inlet_stream.conds["Pressure [Pa]"]
            self.outlet_stream.conds["Mass Flow [kg/sec]"] = self.inlet_stream.conds["Mass Flow [kg/sec]"]
            self.outlet_stream.fracs = self.inlet_stream.fracs
        elif t != 0:
            self.outlet_stream = Stream(self.outlet_stream_name, conds_names, stream_comps)
            self.outlet_stream.conds["Temperature [C]"] = str(t)
            self.outlet_stream.conds["Pressure [Pa]"] = self.inlet_stream.conds["Pressure [Pa]"]
            self.outlet_stream.conds["Mass Flow [kg/sec]"] = self.inlet_stream.conds["Mass Flow [kg/sec]"]
            self.outlet_stream.fracs = self.inlet_stream.fracs

        self.streams[self.outlet_stream_name] = self.outlet_stream
        self.streams_list.addItem(QListWidgetItem(self.outlet_stream_name))
        self.outlet_stream_name_combo.addItem(self.outlet_stream_name)
        self.outlet_stream_name_combo.setCurrentIndex(self.outlet_stream_name_combo.findText(self.outlet_stream_name))
        self.outlet_stream_name_combo.setEnabled(False)



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
            if self.inlet_stream_name_combobox.findText(stream_name) == -1:  # if stream not in list, then add it
                self.inlet_stream_name_combobox.addItem(stream_name)
