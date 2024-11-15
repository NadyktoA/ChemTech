import traceback

import numpy as np
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtWidgets import (QMainWindow, QLineEdit, QComboBox, QLayout,
                             QWidget, QGridLayout, QLabel, QTableWidgetItem,
                             QSizePolicy, QListWidgetItem)
from PyQt5.QtGui import QPixmap, QIcon

from stream import Stream
from stream_properties_window import StreamProperties


class Separator(QMainWindow):
    def __init__(self, worksheet, name):
        super().__init__()
        try:
            self.worksheet = worksheet
            self.streams = self.worksheet.streams
            self.streams_list = self.worksheet.ui.streams_list

            self.ui = SeparatorUI()
            self.ui.setup_ui(self, name)
        except: traceback.print_exc()

    def get_stream_props(self, streams):
        self.inlet_stream = streams[self.ui.inlet_stream_name_combobox.currentText()]
        mol_fracs = []
        for comp_name in self.inlet_stream.fracs.keys():
            comp_mol_frac = self.inlet_stream.fracs[comp_name]['Molar Fraction']
            mol_fracs.append(float(comp_mol_frac))
        mass_flow = self.inlet_stream.conds["Mass Flow [kg/sec]"]

        antoine_coeffs = [0 for _ in range(len(mol_fracs))]
        for idx, comp_name in enumerate(list(self.inlet_stream.comps.keys())):
            comp = self.inlet_stream.comps[comp_name]
            a = comp.antoine_eq.antoine_eq_coeffs.a
            b = comp.antoine_eq.antoine_eq_coeffs.b
            c = comp.antoine_eq.antoine_eq_coeffs.c
            antoine_coeffs[idx] = [a, b, c]

        t = (float(self.ui.separator_T.text()) + 273.15)  # [Celsius] -> [Kelvin]
        p = (float(self.ui.separator_P.text()) * 0.0075)  # [Pa] -> [mmHg]

        return [t, p, mol_fracs, antoine_coeffs, mass_flow]

    def calc_separator(self):
        try:
            inlet_stream_name, t, p = self.ui.inlet_stream_name_combobox.currentText(), self.ui.separator_T.text(), self.ui.separator_P.text()
            if (inlet_stream_name != "") and (t != "") and (p != ""):
                self.input_data = self.get_stream_props(self.streams)

                vapour_frac, liquid_mol_fracs, vapour_mol_fracs = self.calc_vapour_frac(*self.input_data[:-1])
                stream_mass_flow = float(self.input_data[-1])
                liquid_mass_flow = stream_mass_flow * (1 - vapour_frac)
                vapour_mass_flow = stream_mass_flow * vapour_frac

                self.ui.vapour_frac.setText(str(vapour_frac))

                outlet_streams_props = [[vapour_mol_fracs, vapour_mass_flow], [liquid_mol_fracs, liquid_mass_flow]]

                for state, stream_props in enumerate(outlet_streams_props):
                    mol_fracs, mass_flow = stream_props[0], stream_props[1]
                    if state == 0:  # vapour stream
                        combobox = self.ui.outlet_vapour_stream_name_combobox
                    else:  # liquid stream
                        combobox = self.ui.outlet_liquid_stream_name_combobox
                    self.create_outlet_stream(t, p, mol_fracs, mass_flow, combobox)
        except: traceback.print_exc()

    def create_outlet_stream(self, t, p, mol_fracs, mass_flow, combobox):
        outlet_stream_name = f"Поток {len(self.streams) + 1}"
        conds_names = list(self.inlet_stream.conds.keys())
        vapour_stream_comps = self.inlet_stream.comps

        outlet_stream = Stream(outlet_stream_name, conds_names, vapour_stream_comps)
        outlet_stream.conds["Temperature [C]"] = t
        outlet_stream.conds["Pressure [Pa]"] = p
        outlet_stream.conds["Mass Flow [kg/sec]"] = mass_flow

        for comp_num, comp_name in enumerate(list(outlet_stream.fracs.keys())):
            outlet_stream.fracs[comp_name]["Molar Fraction"] = mol_fracs[comp_num]

        self.streams[outlet_stream_name] = outlet_stream
        self.streams_list.addItem(QListWidgetItem(outlet_stream_name))
        self.worksheet.windows[outlet_stream_name] = StreamProperties(outlet_stream_name, self.worksheet)

        combobox.addItem(outlet_stream_name)
        combobox.setCurrentIndex(combobox.findText(outlet_stream_name))
        combobox.setEnabled(False)

    def calc_vapour_frac(self, t, p, mol_fracs, coeffs):
        """
        p_sat = saturated vapour pressure [mmHg]
        k_i = array of equilibrium coefficients
        x_i = array of component molar fractions of the liquid stream
        y_i = array of component molar fractions of the vapour stream
        f = vapour fraction (f = Vapour/Feed)
        """
        p_sat = []
        for comp_coeffs in coeffs:
            p_sat.append(np.exp(comp_coeffs[0] - (comp_coeffs[1] / (comp_coeffs[2] + t))))
        p_sat = np.array(p_sat)
        k_i = p_sat / p

        x, y, ln_x, ln_y, x_i, y_i = 0, 0, 1, 1, None, None
        accuracy = 0.0005
        f_start, f_end, f_guess, counter = 0, 1, 0, 0
        while not ((abs(ln_x) < accuracy) and (abs(ln_y) < accuracy)):
            f_guess = (f_start + f_end) / 2
            counter += 1
            x_i = mol_fracs / (1 + (k_i - 1) * f_guess)
            x = sum(x_i)
            ln_x = np.log(x)
            y_i = k_i * x_i
            y = sum(y_i)
            ln_y = np.log(y)
            # print(f"f = {f_guess}, x = {x}, y = {y}")
            if x < 1:
                f_start = f_guess
            else:
                f_end = f_guess
            if (f_guess > 0.9999) or (f_guess < 0.0001):
                break
        print(f"[finish] f = {f_guess}, x = {x}, y = {y}, counter = {counter}")

        if f_guess > 0.9999:
            vapour_frac = 1
        elif f_guess < 0.0001:
            vapour_frac = 0
        else:
            vapour_frac = f_guess
        return vapour_frac, x_i, y_i

    def update_combobox(self):
        for stream_name in self.streams.keys():
            if self.ui.inlet_stream_name_combobox.findText(stream_name) == -1:  # if stream not in list, then add it
                self.ui.inlet_stream_name_combobox.addItem(stream_name)


class SeparatorUI:
    def setup_ui(self, parent, name):
        parent.setWindowTitle(name)
        parent.setFixedSize(900, 600)
        parent.setWindowIcon(QIcon("./pics/program_icon.png"))

        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        parent.setSizePolicy(size_policy)

        self.central_widget = QWidget(parent)
        self.central_widget.setSizePolicy(size_policy)
        parent.setCentralWidget(self.central_widget)

        self.create_layout(parent)

        self.retranslate_ui()

    def create_layout(self, parent):
        layout = QGridLayout(parent)

        self.create_connections(parent)

        layout.addWidget(self.pic_label, 0, 1, 22, 1)
        layout.addWidget(self.separator_T_label, 0, 0, 1, 1)
        layout.addWidget(self.separator_T, 1, 0, 1, 1)
        layout.addWidget(self.separator_P_label, 2, 0, 1, 1)
        layout.addWidget(self.separator_P, 3, 0, 1, 1)
        layout.addWidget(self.inlet_stream_label, 9, 0, 1, 1)
        layout.addWidget(self.inlet_stream_name_combobox, 10, 0, 1, 1)
        layout.addWidget(self.outlet_vapour_stream_label, 0, 2, 1, 1)
        layout.addWidget(self.outlet_vapour_stream_name_combobox, 1, 2, 1, 1)
        layout.addWidget(self.vapour_frac_label, 9, 2, 1, 1)
        layout.addWidget(self.vapour_frac, 10, 2, 1, 1)
        layout.addWidget(self.outlet_liquid_stream_label, 20, 2, 1, 1)
        layout.addWidget(self.outlet_liquid_stream_name_combobox, 21, 2, 1, 1)

        for i in range(layout.rowCount()):
            layout.setRowStretch(i, 1)
        for i in range(layout.columnCount()):
            layout.setColumnStretch(i, 1)

        layout.setSizeConstraint(QLayout.SetFixedSize)

        self.central_widget.setLayout(layout)

    def create_connections(self, parent):
        self.pic_label = QLabel(parent)
        pic = QPixmap('./pics/Separator.PNG')
        self.pic_label.setPixmap(pic)

        self.separator_T_label = QLabel(parent)
        self.separator_T = QLineEdit()
        self.separator_T.returnPressed.connect(parent.calc_separator)

        self.separator_P_label = QLabel(parent)
        self.separator_P = QLineEdit()
        self.separator_P.returnPressed.connect(parent.calc_separator)

        self.inlet_stream_label = QLabel(parent)
        self.inlet_stream_name_combobox = QComboBox()
        self.inlet_stream_name_combobox.addItem('')
        for stream_name in parent.streams.keys():
            self.inlet_stream_name_combobox.addItem(stream_name)
        self.inlet_stream_name_combobox.currentIndexChanged.connect(parent.calc_separator)

        self.outlet_vapour_stream_label = QLabel(parent)
        self.outlet_vapour_stream_name_combobox = QComboBox()

        self.vapour_frac_label = QLabel(parent)
        self.vapour_frac = QLineEdit()
        self.vapour_frac.setEnabled(False)

        self.outlet_liquid_stream_label = QLabel(parent)
        self.outlet_liquid_stream_name_combobox = QComboBox()

    def retranslate_ui(self):
        translate = QCoreApplication.translate

        self.separator_T_label.setText(translate("Separator Window", "Temperature, C"))
        self.separator_P_label.setText(translate("Separator Window", "Pressure, Pa"))
        self.inlet_stream_label.setText(translate("Separator Window", "Inlet stream"))
        self.outlet_vapour_stream_label.setText(translate("Separator Window", "Outlet vapour stream"))
        self.outlet_liquid_stream_label.setText(translate("Separator Window", "Outlet liquid stream"))
        self.vapour_frac_label.setText(translate("Separator Window", "Vapour fraction, %"))
