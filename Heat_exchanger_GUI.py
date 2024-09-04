import traceback
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QTableWidget, QTableWidgetItem, QLineEdit, QFormLayout, QHBoxLayout, QComboBox, \
    QAction, QVBoxLayout, QWidget, QGridLayout, QLabel, QTabWidget, QStatusBar, QListWidgetItem, QMessageBox, QSlider, QFrame
from PyQt5.QtGui import QPixmap, QDoubleValidator
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import sys
import scipy.integrate as spi
from scipy import sparse
from scipy.sparse.linalg import spsolve
import math

from stream import Stream
from STHE_calculation import Heat_exchanger
from stream_calculation_functions import calc_IG_gas_h_cap, calc_liquid_h_cap


class Heat_exchanger_menu(QWidget):
    def __init__(self, streams, streams_list):
        super(Heat_exchanger_menu, self).__init__()
        self.streams = streams
        self.streams_list = streams_list
        self.init_UI()


    def init_UI(self):
        self.setWindowTitle('Heat Exchanger Menu')
        self.resize(800, 500)
        self.create_tabs()
        self.create_statusbar()

    def create_tabs(self):
        self.layout = QVBoxLayout(self)
        self.tabs = QtWidgets.QTabWidget(self)
        self.connections_tab()
        self.design_tab()
        self.performance_tab()
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

    def create_statusbar(self):
        self.statusbar = QtWidgets.QStatusBar(self)
        self.statusbar.showMessage("Connect streams")
        self.statusbar.setStyleSheet("QStatusBar{background:rgb(255,0,0);color:black;font-weight:bold;}")
        self.statusbar.setGeometry(0, 540, 800, 20)

    def connections_tab(self):
        self.connections = QWidget()
        self.tabs.addTab(self.connections, "Connections")
        self.connections.layout = QGridLayout(self)

        self.pic_label = QtWidgets.QLabel(self)
        #pic = QPixmap(r"C:\Users\cudak\Desktop\test after liquid update\sthe_pic.png")  # laptop
        pic = QPixmap(r'.\sthe_pic') #PC
        self.pic_label.setPixmap(pic)
        self.connections.layout.addWidget(self.pic_label, 5, 1, 6, 12, Qt.AlignCenter)

        self.connections.layout.addWidget(QLabel('Inlet cold stream'), 4, 2, 1, 1)
        self.inlet_cold_stream_name_combobox = QComboBox()
        self.inlet_cold_stream_name_combobox.addItem('')
        for stream_name in self.streams.keys():
            self.inlet_cold_stream_name_combobox.addItem(stream_name)
        self.inlet_cold_stream_name_combobox.currentIndexChanged.connect(self.input_design_data_status)
        self.connections.layout.addWidget(self.inlet_cold_stream_name_combobox, 5, 2, 1, 1)

        self.connections.layout.addWidget(QLabel('Inlet hot stream'), 7, 2, 1, 1, Qt.AlignTop)
        self.inlet_hot_stream_name_combobox = QComboBox()
        self.inlet_hot_stream_name_combobox.addItem('')
        for stream_name in self.streams.keys():
            self.inlet_hot_stream_name_combobox.addItem(stream_name)
        self.inlet_hot_stream_name_combobox.currentIndexChanged.connect(self.input_design_data_status)
        self.connections.layout.addWidget(self.inlet_hot_stream_name_combobox, 7, 2, 1, 1, Qt.AlignBottom)

        self.connections.layout.addWidget(QLabel('Outlet hot stream'), 6, 11, 1, 1, Qt.AlignBottom)
        self.outlet_hot_stream_name_combobox = QComboBox()
        self.connections.layout.addWidget(self.outlet_hot_stream_name_combobox, 7, 11, 1, 1, Qt.AlignTop)
        self.outlet_hot_stream_T = QLineEdit()
        self.outlet_hot_stream_T.returnPressed.connect(self.input_design_data_status)
        self.connections.layout.addWidget(self.outlet_hot_stream_T, 8, 11, 1, 2)
        self.outlet_hot_stream_flow = QLineEdit()
        self.connections.layout.addWidget(QLabel('T,°C'), 8, 10, 1, 1)
        # self.connections.layout.addWidget(self.outlet_hot_stream_flow, 9, 11, 1, 2)
        # self.connections.layout.addWidget(QLabel('G, kg/s'), 9, 10, 1, 1)

        self.connections.layout.addWidget(QLabel('Outlet cold stream'), 10, 11, 1, 1, Qt.AlignTop)
        self.outlet_cold_stream_name_combobox = QComboBox()
        self.connections.layout.addWidget(self.outlet_cold_stream_name_combobox, 10, 11, 1, 1, Qt.AlignBottom)
        self.outlet_cold_stream_T = QLineEdit()
        # self.outlet_cold_stream_T.returnPressed.connect(self.input_connections_data_status)
        self.connections.layout.addWidget(self.outlet_cold_stream_T, 11, 11, 1, 2, Qt.AlignBottom)
        self.outlet_cold_stream_flow = QLineEdit()
        self.connections.layout.addWidget(QLabel('T,°C'), 11, 10, 1, 1, Qt.AlignBottom)
        # self.connections.layout.addWidget(self.outlet_cold_stream_flow, 12, 11, 1, 2,Qt.AlignBottom)
        # self.connections.layout.addWidget(QLabel('G, kg/s'), 12, 10, 1, 1,Qt.AlignBottom)
        # extra rows
        for i in range(0, 20):
            self.connections.layout.addWidget(QLabel(''), i, 0, )

        # extra columns
        for i in range(0, 7):
            self.connections.layout.addWidget(QLabel(''), 0, i, )

        self.connections.setLayout(self.connections.layout)

    def create_outlet_streams(self):
        self.outlet_hot_stream_name = f"Stream {len(self.streams) + 1}"
        conds_names = list(self.hot_stream.conds.keys())
        hot_stream_comps = self.hot_stream.comps

        self.outlet_hot_stream = Stream(self.outlet_hot_stream_name, conds_names, hot_stream_comps)
        self.outlet_hot_stream.conds["Temperature [C]"] = self.outlet_hot_stream_T.text()
        self.outlet_hot_stream.conds["Pressure [Pa]"] = str(self.hot_P_out)
        self.outlet_hot_stream.conds["Mass Flow [kg/sec]"] = str(self.hot_mass_flow_out)
        self.outlet_hot_stream.fracs = self.hot_fracs

        self.streams[self.outlet_hot_stream_name] = self.outlet_hot_stream
        self.streams_list.addItem(QListWidgetItem(self.outlet_hot_stream_name))
        self.outlet_hot_stream_name_combobox.addItem(self.outlet_hot_stream_name)
        self.outlet_hot_stream_name_combobox.setCurrentIndex(self.outlet_hot_stream_name_combobox.findText(self.outlet_hot_stream_name))  # set always the last
        self.outlet_hot_stream_name_combobox.setEnabled(False)

        self.outlet_cold_stream_name = f"Stream {len(self.streams) + 1}"
        conds_names = list(self.cold_stream.conds.keys())
        cold_stream_comps = self.cold_stream.comps

        self.outlet_cold_stream = Stream(self.outlet_cold_stream_name, conds_names, cold_stream_comps)
        self.outlet_cold_stream.conds["Temperature [C]"] = self.outlet_cold_stream_T.text()
        self.outlet_cold_stream.conds["Pressure [Pa]"] = str(self.cold_P_out)
        self.outlet_cold_stream.conds["Mass Flow [kg/sec]"] = str(self.cold_mass_flow_out)
        self.outlet_cold_stream.fracs = self.cold_fracs

        self.streams[self.outlet_cold_stream_name] = self.outlet_cold_stream
        self.streams_list.addItem(QListWidgetItem(self.outlet_cold_stream_name))
        self.outlet_cold_stream_name_combobox.addItem(self.outlet_cold_stream_name)
        self.outlet_cold_stream_name_combobox.setCurrentIndex(self.outlet_cold_stream_name_combobox.findText(self.outlet_cold_stream_name))
        self.outlet_cold_stream_name_combobox.setEnabled(False)

    def design_tab(self):
        self.design = QWidget()
        self.tabs.addTab(self.design, "Design")
        self.design.layout = QGridLayout(self)

        '''shell side'''
        self.shell_geometry_label = QLabel('Shell Geometry')
        self.shell_geometry_label.setStyleSheet("background-color: rgb(186, 174, 255);")
        self.design.layout.addWidget(self.shell_geometry_label, 0, 0, 1, 2, Qt.AlignTop)

        # shell diameter
        self.shell_diameter = QLabel('ID, mm')
        self.shell_diameter.setToolTip('Inside shell diameter')
        self.design.layout.addWidget(self.shell_diameter, 1, 0, 1, 1)
        self.ID_value = QLineEdit()
        self.ID_value.setEnabled(False)
        self.design.layout.addWidget(self.ID_value, 1, 1)

        # baffle type
        self.design.layout.addWidget(QLabel('Baffle type *'), 2, 0)
        self.baffle_type_value = QComboBox()
        self.baffle_type_value.addItem('Segmental')
        self.baffle_type_value.addItem('No baffle')
        self.design.layout.addWidget(self.baffle_type_value, 2, 1)
        self.baffle_type_value.currentIndexChanged.connect(self.input_design_data_status)

        # baffle cut
        self.baffle_cut = QLabel('Baffle cut, %')
        self.design.layout.addWidget(self.baffle_cut, 3, 0)
        self.baffle_cut_value = QComboBox()
        self.baffle_cut_value.addItem('20')
        self.baffle_cut_value.addItem('25')
        self.baffle_cut_value.addItem('30')
        self.baffle_cut_value.addItem('35')
        self.design.layout.addWidget(self.baffle_cut_value, 3, 1)
        self.baffle_cut_value.currentIndexChanged.connect(self.input_design_data_status)

        # baffle spacing
        self.baffle_spacing = QLabel('Baffle spacing, mm')
        self.baffle_spacing.setToolTip('Baffle spacing takes value from 20 to 100 % of the ID')
        self.design.layout.addWidget(self.baffle_spacing, 4, 0)
        self.baffle_spacing_value = QLineEdit()
        self.baffle_spacing_value.setValidator(QtGui.QIntValidator(0, 1000))
        self.design.layout.addWidget(self.baffle_spacing_value, 4, 1)
        self.baffle_spacing_value.setEnabled(False)

        # number of baffles
        self.baffle_number = QLabel('Number of baffles')
        self.design.layout.addWidget(self.baffle_number, 5, 0)
        self.baffle_number_value = QLineEdit()
        self.design.layout.addWidget(self.baffle_number_value, 5, 1)
        self.baffle_number_value.setEnabled(False)

        '''tube  side'''
        self.tube_geometry_label = QLabel('Tube Geometry')
        self.tube_geometry_label.setStyleSheet("background-color: rgb(186, 174, 255);")
        self.design.layout.addWidget(self.tube_geometry_label, 0, 2, 1, 2, Qt.AlignTop)

        # tube diameter
        self.d_out = QLabel('OD, mm *')
        self.d_out.setToolTip('Outside tube diameter takes value from 5 to 50 mm')
        self.design.layout.addWidget(self.d_out, 1, 2, 1, 1)
        self.d_out_value = QLineEdit()
        self.d_out_value.setValidator(QtGui.QIntValidator(5, 50))
        self.design.layout.addWidget(self.d_out_value, 1, 3)
        self.d_out_value.returnPressed.connect(self.input_design_data_status)

        # tube thickness
        self.tube_thickness = QLabel('Tube thickness, mm *')
        self.tube_thickness.setToolTip('Tube thickness takes value from 1 to 5 mm')
        self.design.layout.addWidget(self.tube_thickness, 2, 2, 1, 1)
        self.tube_thickness_value = QLineEdit()
        self.tube_thickness_value.setValidator(QtGui.QIntValidator(1, 5))
        self.design.layout.addWidget(self.tube_thickness_value, 2, 3)
        self.tube_thickness_value.returnPressed.connect(self.input_design_data_status)

        # tube pitch
        self.tube_pitch = QLabel('Tube pitch, mm *')
        self.tube_pitch.setToolTip('Tube pitch takes value from 5 to 50 mm')
        self.design.layout.addWidget(self.tube_pitch, 3, 2, 1, 1)
        self.tube_pitch_value = QLineEdit()
        self.tube_pitch_value.setValidator(QtGui.QIntValidator(5, 50))
        self.design.layout.addWidget(self.tube_pitch_value, 3, 3)
        self.tube_pitch_value.returnPressed.connect(self.input_design_data_status)

        # tube layout
        self.design.layout.addWidget(QLabel('Tube layout *'), 4, 2, 1, 1)
        self.tube_layout_value = QComboBox()
        self.tube_layout_value.addItem('Triangular 30°')
        self.tube_layout_value.addItem('Square 90°')
        self.design.layout.addWidget(self.tube_layout_value, 4, 3)
        self.tube_layout_value.currentIndexChanged.connect(self.input_design_data_status)

        # tube passes
        self.design.layout.addWidget(QLabel('Number of tube passes *'), 5, 2, 1, 1)
        self.tube_passes_value = QComboBox()
        self.tube_passes_value.addItem('1')
        self.tube_passes_value.addItem('2')
        self.tube_passes_value.addItem('3')
        self.design.layout.addWidget(self.tube_passes_value, 5, 3)
        self.tube_passes_value.currentIndexChanged.connect(self.input_design_data_status)

        # number of tubes
        self.design.layout.addWidget(QLabel('Number of tubes'), 6, 2, 1, 1)
        self.number_of_tubes_value = QLineEdit()
        self.number_of_tubes_value.setEnabled(False)
        self.design.layout.addWidget(self.number_of_tubes_value, 6, 3)

        # tube length
        self.design.layout.addWidget(QLabel('Tube length, m'), 7, 2, 1, 1)
        self.tube_length_value = QLineEdit()
        self.tube_length_value.setEnabled(False)
        self.design.layout.addWidget(self.tube_length_value, 7, 3)

        # tube-side pressure drop
        self.design.layout.addWidget(QLabel('Pressure drop, kPa'), 9, 2)
        self.tube_pressure_drop_value = QLineEdit()
        self.tube_pressure_drop_value.setEnabled(False)
        self.design.layout.addWidget(self.tube_pressure_drop_value, 9, 3)

        # tube-side pressure drop
        self.design.layout.addWidget(QLabel('Pressure drop, kPa'), 9, 0)
        self.shell_pressure_drop_value = QLineEdit()
        self.shell_pressure_drop_value.setEnabled(False)
        self.design.layout.addWidget(self.shell_pressure_drop_value, 9, 1)

        # flow direction
        self.design.layout.addWidget(QLabel('Flow direction'), 10, 0)
        self.flow_direction_value = QComboBox()
        self.flow_direction_value.addItem('Parallel')
        self.flow_direction_value.addItem('Counter')
        self.flow_direction_value.currentIndexChanged.connect(self.input_design_data_status)

        self.design.layout.addWidget(self.flow_direction_value, 10, 1)
        # extra rows
        for i in range(8, 13):
            self.design.layout.addWidget(QLabel(''), i, 0, 1, 1)

        self.design.setLayout(self.design.layout)

    def input_design_data_status(self):
        if (self.inlet_hot_stream_name_combobox.currentText() != '') and (self.inlet_cold_stream_name_combobox.currentText() != ''):
            self.statusbar.showMessage("Specify geometry parameters marked with *")
            self.statusbar.setStyleSheet("QStatusBar{background:rgb(255,0,0);color:black;font-weight:bold;}")
            if len(self.d_out_value.text()) > 0 and len(self.tube_thickness_value.text()) > 0 and len(self.tube_pitch_value.text()):
                if self.baffle_type_value.currentText() == 'Segmental':
                    self.baffle_cut.setVisible(True)
                    self.baffle_spacing.setVisible(True)
                    self.baffle_number.setVisible(True)
                    self.baffle_cut_value.setVisible(True)
                    self.baffle_spacing_value.setVisible(True)
                    self.baffle_number_value.setVisible(True)
                    self.perfomance_fill()
                    self.statusbar.showMessage("OK")
                    self.statusbar.setStyleSheet("QStatusBar{background:rgb(0,255,0);color:black;font-weight:bold;}")

                if self.baffle_type_value.currentText() == 'No baffle':
                    self.baffle_cut.setVisible(False)
                    self.baffle_spacing.setVisible(False)
                    self.baffle_number.setVisible(False)
                    self.baffle_cut_value.setVisible(False)
                    self.baffle_spacing_value.setVisible(False)
                    self.baffle_number_value.setVisible(False)
                    self.perfomance_fill()
                    self.statusbar.showMessage("OK")
                    self.statusbar.setStyleSheet("QStatusBar{background:rgb(0,255,0);color:black;font-weight:bold;}")
        else:
            self.statusbar.showMessage("Connect streams")
            self.statusbar.setStyleSheet("QStatusBar{background:rgb(255,0,0);color:black;font-weight:bold;}")

    def get_stream_property(self):
        try:
            if (self.inlet_hot_stream_name_combobox.currentText() != '') and (self.inlet_cold_stream_name_combobox.currentText() != ''):
                self.cold_stream = self.streams[self.inlet_cold_stream_name_combobox.currentText()]
                self.cold_stream_molar_wt = self.cold_stream.props["Stream Molar Weight [g/mol]"]
                self.c_temp1 = self.cold_stream.conds["Temperature [C]"]
                self.cold_P_out = self.cold_stream.conds["Pressure [Pa]"]
                self.cold_mass_flow_out = self.cold_stream.conds["Mass Flow [kg/sec]"]
                self.c_cp = self.calc_cp(self.cold_stream, float(self.c_temp1), float(self.outlet_cold_stream_T.text()))
                self.c_cp = self.c_cp / (self.cold_stream_molar_wt / 1000)
                self.c_t_cond = self.cold_stream.props["Thermal Conductivity [W/m-K]"]
                self.c_visc = self.cold_stream.props["Viscosity [Pa*s]"]
                self.c_den = self.cold_stream.props["Density [kg/m3]"]
                self.cold_fracs = self.cold_stream.fracs

                self.hot_stream = self.streams[self.inlet_hot_stream_name_combobox.currentText()]
                self.hot_stream_molar_wt = self.hot_stream.props["Stream Molar Weight [g/mol]"]
                self.h_temp1 = self.hot_stream.conds["Temperature [C]"]
                print(f"[h_temp1] {self.h_temp1}")
                self.hot_P_out = self.hot_stream.conds["Pressure [Pa]"]
                self.hot_mass_flow_out = self.hot_stream.conds["Mass Flow [kg/sec]"]
                self.h_cp = self.calc_cp(self.hot_stream, float(self.h_temp1), float(self.outlet_hot_stream_T.text()))
                self.h_cp = self.h_cp / (self.hot_stream_molar_wt / 1000)
                self.h_t_cond = self.hot_stream.props["Thermal Conductivity [W/m-K]"]
                self.h_visc = self.hot_stream.props["Viscosity [Pa*s]"]
                self.h_den = self.hot_stream.props["Density [kg/m3]"]
                self.hot_fracs = self.hot_stream.fracs

                # self.create_outlet_streams()
        except:
            traceback.print_exc()

    def calc_cp(self, stream, temp1, temp2):
        phase = stream.conds["Phase"]
        t = ((temp1 + temp2) / 2) + 273.15
        comps = stream.comps
        fracs = stream.fracs

        mol_fracs, t_c, w = [], [], []
        for comp_name in fracs.keys():
            comp_mol_frac = fracs[comp_name]['Molar Fraction']
            mol_fracs.append(float(comp_mol_frac))

        for comp_name in comps.keys():
            t_c.append(comps[comp_name].general_info.critical_props.critical_T)
            w.append(comps[comp_name].general_info.critical_props.acentricity)
        mol_fracs, t_c, w = np.array(mol_fracs), np.array(t_c), np.array(w)

        if phase == "Vapour":
            total_cp, comps_cp = calc_IG_gas_h_cap(comps, mol_fracs, t)
            print(f'[cp ({temp1}-{temp2})] {total_cp} [J/mol-K]')
            return total_cp
        elif phase == "Liquid":
            cp = calc_liquid_h_cap(t, t_c, w, mol_fracs, comps)
            print(f'[cp ({temp1}-{temp2})] {cp} [J/mol-K]')
            return cp

    def update_combobox(self):
        for stream_name in self.streams.keys():
            if self.inlet_hot_stream_name_combobox.findText(stream_name) == -1:  # if stream not in list, then add it
                self.inlet_hot_stream_name_combobox.addItem(stream_name)
            if self.inlet_cold_stream_name_combobox.findText(stream_name) == -1:  # if stream not in list, then add it
                self.inlet_cold_stream_name_combobox.addItem(stream_name)

    def performance_tab(self):
        self.performance = QWidget()
        self.tabs.addTab(self.performance, "Performance")
        self.performance.layout = QGridLayout(self)

        self.heat_load_value = QLineEdit()
        self.heat_load_value.setEnabled(False)
        self.performance.layout.addWidget(QLabel('Heat load, kW'), 0, 0, Qt.AlignCenter)
        self.performance.layout.addWidget(self.heat_load_value, 0, 1, 1, 1, Qt.AlignLeft)

        self.LMTD_value = QLineEdit()
        self.LMTD_value.setEnabled(False)
        self.performance.layout.addWidget(QLabel('LMTD, K'), 1, 0, Qt.AlignCenter)
        self.performance.layout.addWidget(self.LMTD_value, 1, 1, 1, 1, Qt.AlignLeft)

        self.overall_U_value = QLineEdit()
        self.overall_U_value.setEnabled(False)
        self.performance.layout.addWidget(QLabel("Overall U, W/(m^2 K)"), 2, 0, Qt.AlignCenter)
        self.performance.layout.addWidget(self.overall_U_value, 2, 1, 1, 1, Qt.AlignLeft)

        self.he_surface_area_value = QLineEdit()
        self.he_surface_area_value.setEnabled(False)
        self.performance.layout.addWidget(QLabel("HE surface area, m^2"), 3, 0, Qt.AlignCenter)
        self.performance.layout.addWidget(self.he_surface_area_value, 3, 1, 1, 1, Qt.AlignLeft)

        self.temperature = QtWidgets.QPushButton('Temperature profile')
        self.performance.layout.addWidget(self.temperature, 4, 0, Qt.AlignTop)
        self.temperature.clicked.connect(self.plot)

        # extra columns
        self.performance.layout.addWidget(QLabel(""), 0, 3)
        self.performance.layout.addWidget(QLabel(""), 0, 4)

        self.performance.setLayout(self.performance.layout)

    def perfomance_fill(self):
        try:
            self.get_stream_property()

            '''data collecting'''
            # geometry
            d_out = float(self.d_out_value.text()) / 1000  # m
            tube_wall_thickness = float(self.tube_thickness_value.text()) / 1000  # m
            d_in = (d_out - 2 * tube_wall_thickness)  # m
            tube_pitch = float(self.tube_pitch_value.text()) / 1000  # m
            pass_num = int(self.tube_passes_value.currentText())
            layout_type = self.tube_layout_value.currentText()
            flow_dir = self.flow_direction_value.currentText()
            # conditions
            # self.h_temp1 = float(self.h_temp1)
            # self.h_temp2 = float(self.outlet_hot_stream_T.text())  # 60
            # self.h_flow = float(self.hot_mass_flow_out)
            # self.c_temp1 = float(self.c_temp1)
            # self.c_temp2 = float(self.outlet_cold_stream_T.text())  # 55
            # self.c_flow = float(self.cold_mass_flow_out)
            # # properties
            # self.h_den = float(self.h_den)
            # self.c_den = float(self.c_den)
            # self.h_cp = float(self.h_cp)
            # self.c_cp = float(self.c_cp)
            # # h_visc = 0.00017 # some random value ONLY for test
            # # c_vics = 0.0004 # some random value ONLY for test
            # self.h_visc = float(self.h_visc)
            # self.c_vics = float(self.c_visc)
            # self.h_t_cond = float(self.h_t_cond)
            # self.c_t_cond = float(self.c_t_cond)

            d_out = float(self.d_out_value.text()) / 1000  # m
            tube_wall_thickness = float(self.tube_thickness_value.text()) / 1000  # m
            d_in = (d_out - 2 * tube_wall_thickness)  # m
            tube_pitch = float(self.tube_pitch_value.text()) / 1000  # m
            pass_num = int(self.tube_passes_value.currentText())
            layout_type = self.tube_layout_value.currentText()

            '''DATA FROM HYSYS'''
            self.h_temp1 = 80
            self.h_temp2 = 60
            self.h_flow = 7
            self.c_temp1 = 45
            self.c_temp2 = 55
            self.c_flow =  14.16
            # properties
            self.h_den = 0.5*(811+712)
            self.c_den = 0.5*(833.8+704)
            self.h_cp = 0.5*(1823+2218)
            self.c_cp = 0.5*(1731+2264)
            self.h_visc = 0.5*(0.3113+0.6562)/1000
            self.c_vics = 0.5*(0.3888+0.5842)/1000
            # h_visc = self.h_visc
            # c_vics = self.c_visc
            self.h_t_cond = 0.5*(0.1165+0.1278)
            self.c_t_cond = 0.5*(0.1218+0.1255)

            tube_t_cond = 50

            self.create_outlet_streams()

            self.heat1 = Heat_exchanger(self.h_temp1, self.h_temp2, self.h_flow, self.c_temp1, self.c_temp2, self.c_flow, self.h_cp, self.c_cp)

            '''number of tubes filling'''
            tubes_per_pass = self.heat1.n_tube(self.h_flow, d_in, self.h_visc)
            tubes_total_number = self.heat1.n_tube_total(tubes_per_pass, pass_num)
            self.number_of_tubes_value.setText(str(tubes_total_number))

            '''shell diameter filling'''
            CL = self.heat1.CL(layout_type)
            CTP = self.heat1.CTP(pass_num)
            PR = self.heat1.PR(tube_pitch, d_out)
            inside_shell_diameter = self.heat1.Ds(d_out, CL, PR, CTP, tubes_total_number)  # m
            self.ID_value.setText(str(round(inside_shell_diameter * 1000)))

            '''heat load filling'''
            heat_load = self.heat1.heat_load(self.h_temp1, self.h_temp2, self.h_flow, self.h_cp, self.c_temp1, self.c_temp2, self.c_flow, self.c_cp)
            self.heat_load_value.setText(str(round(heat_load / 1000, 3)))

            '''LMTD filling'''
            LMTD = round(self.heat1.LMTD(self.h_temp1, self.h_temp2, self.c_temp1, self.c_temp2, pass_num, flow_dir), 2)
            self.LMTD_value.setText(str(LMTD))

            '''overall U filling'''
            baffle_presence = self.baffle_type_value.currentText()
            baffle_cut = int(self.baffle_cut_value.currentText())
            As = self.heat1.As(baffle_presence, baffle_cut, inside_shell_diameter, tubes_total_number, d_out)[0]
            De = self.heat1.As(baffle_presence, baffle_cut, inside_shell_diameter, tubes_total_number, d_out)[1]
            #As = self.heat1.As_test(inside_shell_diameter,tube_pitch,d_out)

            # tube-side
            Re_tube = self.heat1.Re_tube_side(self.h_flow, tubes_per_pass, d_in, self.h_visc)
            Pr_tube = self.heat1.Pr_tube_side(self.h_cp, self.h_visc, self.h_t_cond)
            a_tube = self.heat1.alpha_t(Re_tube, Pr_tube, self.h_t_cond, d_in)
            # shell-side
            Re_shell = self.heat1.Re_shell_side(self.c_flow, De, As, self.c_vics)
            Pr_shell = self.heat1.Pr_shell_side(self.c_cp, self.c_vics, self.c_t_cond)
            a_shell = self.heat1.alpha_s(Re_shell, Pr_shell, self.c_t_cond, De)
            overall_U = self.heat1.overall_U(a_shell, a_tube, tube_wall_thickness, tube_t_cond)
            self.overall_U_value.setText(str(round(overall_U, 2)))

            '''heat exchange surface area filling'''
            F = self.heat1.he_surf(heat_load, overall_U, LMTD)
            self.he_surface_area_value.setText(str(round(F, 2)))

            '''tube length filling'''
            l = self.heat1.l_tube(F, tubes_total_number, d_out)
            self.tube_length_value.setText(str(round(l, 2)))

            '''baffle spacing filling'''
            baffle_spacing = 0.5 * inside_shell_diameter
            self.baffle_spacing_value.setText(str(round(baffle_spacing * 1000)))

            '''number of baffles filling'''
            baffle_number = round(self.heat1.baffle_number(l, baffle_spacing))
            self.baffle_number_value.setText(str(baffle_number))

            '''tube-side pressure drop'''
            w_tube = self.heat1.w_tube(d_in, self.h_flow, self.h_den, tubes_per_pass)
            tube_E = self.heat1.tube_kinetic_energy(self.h_den, w_tube)
            # dp_tube = self.heat1.tube_pressure_drop(Re_tube,l,pass_num,d_in,tube_E)
            dp_tube_test = self.heat1.tube_pressure_drop_test(Re_tube, l, pass_num, d_in, tube_E)
            self.tube_pressure_drop_value.setText(str(round(dp_tube_test / 1000, 3)))

            '''shell-side pressure drop'''
            w_shell = self.heat1.w_shell(self.c_flow, self.c_den, As)
            print(w_shell, Re_shell)
            numerator = self.heat1.pressure_drop_shell_numerator(Re_shell, inside_shell_diameter, baffle_number, self.c_den, w_shell)
            dp_shell = self.heat1.pressure_drop_shell(numerator, De)
            #self.shell_pressure_drop_value.setText(str(round(dp_shell / 1000, 3)))

            tube_row = self.heat1.tube_rows(layout_type, tubes_total_number, inside_shell_diameter, tube_pitch)
            print(f"[tube row] {tube_row}")
            dp_shell_test = self.heat1.pressure_drop_shell_test(tube_row, baffle_number, Re_shell, self.c_den, w_shell)
            self.shell_pressure_drop_value.setText(str(round(dp_shell_test / 1000, 3)))

        except:
            traceback.print_exc()

    def plot(self):
        match int(self.tube_passes_value.currentText()):
            case 1:
                self.plot_if_one()
            case 2:
                if self.flow_direction_value.currentText() == 'Parallel':
                    self.plot_if_two()
                else:
                    self.show_message_box()
            case _:
                self.show_message_box()

    def plot_if_one(self):
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.performance.layout.addWidget(self.canvas, 0, 4, 5, 2)
        self.performance.layout.addWidget(self.toolbar, 7, 4, 2, 2, Qt.AlignCenter)

        match self.flow_direction_value.currentText():
            case 'Parallel':
                def h_e(l, T):
                    dTdl = np.zeros(2)
                    n = int(self.number_of_tubes_value.text())
                    d_out = int(self.d_out_value.text()) / 1000
                    K = float(self.overall_U_value.text())

                    dTdl[0] = n * np.pi * d_out * K * (T[1] - T[0]) / self.h_cp / self.h_flow
                    dTdl[1] = n * np.pi * d_out * K * (T[0] - T[1]) / self.c_cp / self.c_flow
                    return dTdl

                L_int = float(self.tube_length_value.text())
                L = np.linspace(0, L_int, 20)
                solution = spi.solve_ivp(h_e, [0, L_int], [self.h_temp1, self.c_temp1], method='Radau', t_eval=L)
                T1 = solution.y[0]
                T2 = solution.y[1]

            case 'Counter':
                def diff_system(t_cold_end):
                    def h_e(l, T):
                        dTdl = np.zeros(2)
                        n = int(self.number_of_tubes_value.text())
                        d_out = int(self.d_out_value.text()) / 1000
                        K = float(self.overall_U_value.text())

                        dTdl[0] = n * np.pi * d_out * K * (T[1] - T[0]) / self.h_cp / self.h_flow
                        dTdl[1] = n * np.pi * d_out * K * (T[1] - T[0]) / self.c_cp / self.c_flow
                        return dTdl

                    L_int = float(self.tube_length_value.text())
                    L = np.linspace(0, L_int, 20)
                    solution = spi.solve_ivp(h_e, [0, L_int], [self.h_temp1, t_cold_end], method='Radau', t_eval=L)
                    T1 = solution.y[0]
                    T2 = solution.y[1]
                    return T2[-1]

                def half_method(a, b):
                    eps = 0.01
                    c_temp2_guess = (a + b) / 2
                    count_iter = 0
                    while abs((diff_system(c_temp2_guess) - self.c_temp1)) > eps:
                        if self.c_temp1 - diff_system(c_temp2_guess) < 0:
                            a = c_temp2_guess
                        if self.c_temp1 - diff_system(c_temp2_guess) > 0:
                            b = c_temp2_guess
                        c_temp2_guess = (a + b) / 2
                        count_iter = count_iter + 1
                    print('Number of iterations:', count_iter)
                    return c_temp2_guess

                def h_e(l, T):
                    dTdl = np.zeros(2)
                    n = int(self.number_of_tubes_value.text())
                    d_out = int(self.d_out_value.text()) / 1000
                    K = float(self.overall_U_value.text())

                    dTdl[0] = n * np.pi * d_out * K * (T[1] - T[0]) / self.h_cp / self.h_flow
                    dTdl[1] = n * np.pi * d_out * K * (T[1] - T[0]) / self.c_cp / self.c_flow
                    return dTdl

                L_int = float(self.tube_length_value.text())
                L = np.linspace(0, L_int, 20)
                solution = spi.solve_ivp(h_e, [0, L_int], [self.h_temp1, half_method(self.h_temp1, self.c_temp1)],method='Radau', t_eval=L)
                T1 = solution.y[0]
                T2 = solution.y[1]

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_title('Temperature distribution')
        ax.set_xlim(0, float(self.tube_length_value.text()))
        ax.plot(L, T1, label='Hot stream temperature -->', color='C1')
        ax.plot(L, T2, label='Cold stream temperature <--', color='C0')
        ax.legend()
        ax.set_xlabel('Length, m')
        ax.set_ylabel('Temperature, °C')
        # ax.set_xticks(fontsize=12)
        # ax.set_yticks(fontsize=12)
        ax.grid()
        self.canvas.show()

    def plot_if_two(self):
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.performance.layout.addWidget(self.canvas, 0, 4, 5, 2)
        self.performance.layout.addWidget(self.toolbar, 7, 4, 2, 2, Qt.AlignCenter)

        def diff_system_two(t_hot_end):
            def h_e(l, T):
                dTdl = np.zeros(3)
                n = int(self.number_of_tubes_value.text())
                d_out = int(self.d_out_value.text()) / 1000
                K = float(self.overall_U_value.text())

                dTdl[0] = n * np.pi * d_out * K * (T[1] - T[0]) / self.h_cp / self.h_flow
                dTdl[1] = n * np.pi * d_out * K * (T[0] - T[1]) / self.c_cp / self.c_flow + n * np.pi * d_out * K * (T[2] - T[1]) / self.c_cp / self.c_flow
                dTdl[2] = n * np.pi * d_out * K * (T[2] - T[1]) / self.h_cp / self.h_flow
                return dTdl

            L_int = float(self.tube_length_value.text())
            L = np.linspace(0, L_int, 20)
            solution = spi.solve_ivp(h_e, [0, L_int], [self.h_temp1,self.c_temp1,t_hot_end], method='Radau', t_eval=L)
            T_tube1 = solution.y[0]
            T_shell = solution.y[1]
            T_tube2 = solution.y[2]
            return [T_tube1[-1],T_tube2[-1]]

        def half_method(a, b):
            eps = 0.01
            h_temp_guess = (a + b) / 2
            count_iter = 0
            while abs((diff_system_two(h_temp_guess)[0] - diff_system_two(h_temp_guess)[1])) > eps:
                if diff_system_two(h_temp_guess)[0] - diff_system_two(h_temp_guess)[1] < 0:
                    a = h_temp_guess
                if diff_system_two(h_temp_guess)[0] - diff_system_two(h_temp_guess)[1] > 0:
                    b = h_temp_guess
                h_temp_guess = (a + b) / 2
                count_iter = count_iter + 1
            print('Number of iterations:', count_iter)
            return h_temp_guess

        def h_e(l, T):
            dTdl = np.zeros(3)
            n = int(self.number_of_tubes_value.text())
            d_out = int(self.d_out_value.text()) / 1000
            K = float(self.overall_U_value.text())

            dTdl[0] = n * np.pi * d_out * K * (T[1] - T[0]) / self.h_cp / self.h_flow
            dTdl[1] = n * np.pi * d_out * K * (T[0] - T[1]) / self.c_cp / self.c_flow + n * np.pi * d_out * K * (T[2] - T[1]) / self.c_cp / self.c_flow
            dTdl[2] = n * np.pi * d_out * K * (T[2] - T[1]) / self.h_cp / self.h_flow
            return dTdl

        L_int = float(self.tube_length_value.text())
        L = np.linspace(0, L_int, 20)
        solution = spi.solve_ivp(h_e, [0, L_int], [self.h_temp1,self.c_temp1, half_method(self.h_temp1, self.c_temp1)], method='Radau', t_eval=L)
        T_tube1 = solution.y[0]
        T_shell = solution.y[1]
        T_tube2 = solution.y[2]

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_title('Temperature distribution')
        ax.set_xlim(0, float(self.tube_length_value.text()))
        ax.plot(L, T_tube1, label='Hot stream temperature -->', color='C3')
        ax.plot(L, T_tube2, label='Hot stream temperature <--', color='C1')
        ax.plot(L, T_shell, label='Cold stream temperature -->', color='C0')
        ax.legend()
        ax.set_xlabel('Length, m')
        ax.set_ylabel('Temperature, °C')
        # ax.set_xticks(fontsize=12)
        # ax.set_yticks(fontsize=12)
        ax.grid()
        self.canvas.show()

    def show_message_box(self):
        QMessageBox.about(self, 'Sorry', 'Something went wrong!')
# app = QtWidgets.QApplication(sys.argv)
# mainWind = Heat_exchanger_menu()
# mainWind.show()
# sys.exit(app.exec_())
# print(mainWind.heat_load())
