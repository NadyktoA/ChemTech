import traceback

from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtWidgets import (QMainWindow, QLineEdit, QComboBox, QListWidgetItem,
                             QWidget, QGridLayout, QLabel,
                             QSizePolicy, )
from PyQt5.QtGui import QPixmap, QIcon

from stream import Stream
from stream_properties_window import StreamProperties


class Heater(QMainWindow):
    def __init__(self, worksheet, name, apparatus_type):
        super().__init__()

        self.worksheet = worksheet
        self.windows = self.worksheet.windows
        self.streams = self.worksheet.streams
        self.streams_list = self.worksheet.ui.streams_list

        self.ui = HeaterUI()
        self.ui.setup_ui(self, name, apparatus_type)

    def calc_heater(self):
        if self.ui.inlet_stream_name_combobox.currentText() != '':
            self.inlet_stream = self.streams[self.ui.inlet_stream_name_combobox.currentText()]
            if isinstance(self.sender(), QLineEdit):
                if self.sender().text() == self.ui.dH.text():
                    self.ui.output_T.clear()
                else:
                    self.ui.dH.clear()
            if self.ui.output_T.text() != "":
                self.calc_dH()
            elif self.ui.dH.text() != "":
                self.calc_T()

    def calc_dH(self):
        output_T = float(self.ui.output_T.text())
        self.create_outlet_streams(output_T)
        self.windows[self.outlet_stream_name] = StreamProperties(self.outlet_stream_name,
                                                                 self.worksheet)

        input_H = self.inlet_stream.props["Mass Enthalpy [kJ/kg]"]
        output_H = self.outlet_stream.props["Mass Enthalpy [kJ/kg]"]
        dH = -1 * (input_H - output_H)  # enthalpy is a negative value, as in Hysys
        self.ui.dH.setText(f"{dH:.7f}")

    def calc_T(self):
        input_H = float(self.inlet_stream.props["Mass Enthalpy [kJ/kg]"])
        output_H = input_H + float(self.ui.dH.text())

        input_T = float(self.inlet_stream.conds["Temperature [C]"])
        if output_H > input_H:
            print("more")
            t_guess = 2000
        else:
            t_guess = input_T
            input_T = -273  # it can't be any lower
        T_calc = ((float(input_T) + float(t_guess)) / 2)
        self.create_outlet_streams(T_calc)
        outlet_stream_window = StreamProperties(self.outlet_stream_name,
                                                self.worksheet)
        H_calc = self.outlet_stream.props["Mass Enthalpy [kJ/kg]"]

        counter, accuracy = 0, 0.001
        while abs(output_H - float(H_calc)) > accuracy:
            counter += 1
            del self.streams[self.outlet_stream_name]  #
            self.streams_list.takeItem(self.streams_list.count() - 1)
            if float(H_calc) > output_H:
                t_guess = T_calc
            else:
                input_T = T_calc
            T_calc = ((float(input_T) + float(t_guess)) / 2)
            self.create_outlet_streams(T_calc)
            outlet_stream_window = StreamProperties(self.outlet_stream_name,
                                                    self.worksheet)
            H_calc = self.outlet_stream.props["Mass Enthalpy [kJ/kg]"]

        self.windows[self.outlet_stream_name] = outlet_stream_window
        self.ui.output_T.setText(f'{(self.outlet_stream.conds["Temperature [C]"]):.7f}')

    def create_outlet_streams(self, t):
        self.outlet_stream_name = f"Stream {len(self.streams) + 1}"
        conds_names = list(self.inlet_stream.conds.keys())
        stream_comps = self.inlet_stream.comps

        self.outlet_stream = Stream(self.outlet_stream_name, conds_names, stream_comps)
        self.outlet_stream.conds["Temperature [C]"] = t
        self.outlet_stream.conds["Pressure [Pa]"] = self.inlet_stream.conds["Pressure [Pa]"]
        self.outlet_stream.conds["Mass Flow [kg/sec]"] = self.inlet_stream.conds["Mass Flow [kg/sec]"]
        self.outlet_stream.fracs = self.inlet_stream.fracs

        self.streams[self.outlet_stream_name] = self.outlet_stream
        self.streams_list.addItem(QListWidgetItem(self.outlet_stream_name))
        self.ui.outlet_stream_name_combo.addItem(self.outlet_stream_name)
        self.ui.outlet_stream_name_combo.setCurrentIndex(self.ui.outlet_stream_name_combo.findText(self.outlet_stream_name))
        self.ui.outlet_stream_name_combo.setEnabled(False)

    def update_combobox(self):
        for stream_name in self.streams.keys():
            if self.ui.inlet_stream_name_combobox.findText(stream_name) == -1:  # if stream not in list, then add it
                self.ui.inlet_stream_name_combobox.addItem(stream_name)


class HeaterUI:
    def setup_ui(self, parent, name, apparatus_type):
        parent.setWindowTitle(name)
        parent.setWindowIcon(QIcon("./pics/program_icon.png"))

        parent.setFixedSize(750, 450)

        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        parent.setSizePolicy(size_policy)

        self.central_widget = QWidget(parent)
        self.central_widget.setSizePolicy(size_policy)
        parent.setCentralWidget(self.central_widget)

        self.create_layout(parent, apparatus_type)

        self.retranslate_ui()

    def create_layout(self, parent, apparatus_type):
        layout = QGridLayout(parent)

        self.create_connections(parent, apparatus_type)

        for i in range(7):
            layout.setRowStretch(i, 1)
            if i < 5:
                layout.setColumnStretch(i, 1)

        layout.addWidget(self.pic_label, 2, 1, 3, 3)
        layout.addWidget(self.inlet_stream_label, 2, 0)
        layout.addWidget(self.outlet_stream_label, 2, 4)
        layout.addWidget(self.inlet_stream_name_combobox, 3, 0)
        layout.addWidget(self.outlet_stream_name_combo, 3, 4, )
        layout.addWidget(self.temperature_label, 5, 1)
        layout.addWidget(self.output_T, 6, 1)
        layout.addWidget(self.entalpy_label, 5, 3)
        layout.addWidget(self.dH, 6, 3)

        self.central_widget.setLayout(layout)

    def create_connections(self, parent, apparatus_type):
        self.pic_label = QLabel(parent)
        if apparatus_type == "Heater":
            pic = QPixmap('./pics/Heater.png')
        else:
            pic = QPixmap('./pics/Cooler.png')
        self.pic_label.setPixmap(pic)

        self.inlet_stream_label = QLabel(parent)
        self.inlet_stream_label.setAlignment(Qt.AlignBottom)

        self.inlet_stream_name_combobox = QComboBox()
        self.inlet_stream_name_combobox.addItem('')
        for stream_name in parent.streams.keys():
            self.inlet_stream_name_combobox.addItem(stream_name)
        self.inlet_stream_name_combobox.currentIndexChanged.connect(parent.calc_heater)

        self.outlet_stream_label = QLabel(parent)
        self.outlet_stream_label.setAlignment(Qt.AlignBottom)

        self.outlet_stream_name_combo = QComboBox()

        self.temperature_label = QLabel(parent)  # T, C
        self.temperature_label.setAlignment(Qt.AlignCenter)

        self.output_T = QLineEdit()
        self.output_T.setAlignment(Qt.AlignCenter)
        self.output_T.returnPressed.connect(parent.calc_heater)

        self.entalpy_label = QLabel(parent)  # 'dH, kJ/sec'
        self.entalpy_label.setAlignment(Qt.AlignCenter)

        self.dH = QLineEdit()
        self.dH.setAlignment(Qt.AlignCenter)
        self.dH.returnPressed.connect(parent.calc_heater)

    def retranslate_ui(self):
        translate = QCoreApplication.translate

        self.inlet_stream_label.setText(translate("Heater Window", "Inlet Stream"))
        self.outlet_stream_label.setText(translate("Heater Window", "Outlet Stream"))
        self.temperature_label.setText(translate("Heater Window", "Temperature, C"))
        self.entalpy_label.setText(translate("Heater Window", "dH, kJ/sec"))
