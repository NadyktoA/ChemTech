# avg = average
# bpt = boiling point temperature
# char = character
# cnt = count
# comp = component
# cond = condition
# idx = index
# P = pressure
# props = properties
# res = result
# T = temperature
# val = value


import traceback

from PyQt5.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem, QStatusBar, QTabWidget,
                             QAbstractItemView, QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt
import numpy as np

from stream_calculation_functions import (calculate_total_frac, calculate_unknown_frac,
                                          calc_bpt, calc_liquid_viscosity,
                                          calc_liquid_h_cap, calc_liquid_therm_cond,
                                          calc_IG_mol_vol, calc_SRK_mol_vol,
                                          calc_density, calc_IG_gas_h_cap,
                                          calc_gas_viscosity, calc_gas_therm_cond,
                                          calc_gas_enthalpy, calc_liquid_enthalpy)


def reformat_val_into_num(val):
    val = str(val.text())
    if val not in ["Vapour", "Liquid", "Vapour-Liquid"]:
        res = val.replace(",", ".")
        res = "".join([char for char in res if (char == ".") or (char.isnumeric()) or (char == "-")])
    else:
        res = val
    return res


class StreamProperties(QWidget):
    def __init__(self, name, conds_names, stream):
        super().__init__()
        self.name = name
        self.conds_names = conds_names
        self.stream = stream

        self.T_is_defined = False
        self.P_is_defined = False
        self.flowrate_is_defined = False
        self.composition_is_defined = False
        self.is_ok = False
        self.calculated = False

        self.init_ui()

    def init_ui(self):
        self.resize(800, 520)
        self.setWindowTitle(f"Stream Properties of {self.name}")
        self.setFixedSize(800, 520)

        self.create_statusbar()
        self.create_tab_comps()
        self.create_tab_props()
        self.create_tab_conds()
        # creating tabs must be initialized after creating the objects
        self.create_tabs()

    def create_statusbar(self):
        self.statusbar = QStatusBar(self)
        self.statusbar.setGeometry(0, 500, 800, 20)

        self.statusbar.showMessage("Composition Unknown")
        self.statusbar.setStyleSheet("QStatusBar{background:rgb(255,0,0);color:black;font-weight:bold;}")

    def create_tab_comps(self):
        self.tab_comps = QWidget(self)

        self.create_comps_table()
        self.load_data_comps_table()

    def create_comps_table(self):
        self.comps_table = QTableWidget(self.tab_comps)
        self.comps_table.setGeometry(0, 0, 800, 475)

        headers = ["Substance Class", "ID", "Name", "Chemical Formula", "Molar Weight [g / mol]",
                   "Normal Boiling Point [C]", "Ideal Liquid Density [kg / m3]", "Critical Temperature [C]",
                   "Critical Pressure [kPa]", "Critical Volume [m3 / kgmole]", "Acentricity"]
        self.comps_table.setRowCount(len(headers))
        self.comps_table.setColumnCount(0)
        self.comps_table.setVerticalHeaderLabels(headers)
        self.comps_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.comps_table.resizeColumnsToContents()
        self.comps_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def load_data_comps_table(self):
        comps_cnt = len(self.stream.comps)

        for comp_idx in range(1, comps_cnt + 1):
            cols_cnt = self.comps_table.columnCount() + 1
            self.comps_table.setColumnCount(cols_cnt)

            # we show classification, base and critical properties of component in components table,
            # so we need to pass values from stream to table
            comp_props = self.stream.comps[f"component {comp_idx}"]
            comp_classification = list(comp_props.general_info.classification.output_props().values())
            comp_base_props = list(comp_props.general_info.base_props.output_props().values())
            comp_critical_props = list(comp_props.general_info.critical_props.output_props().values())
            props = comp_classification + comp_base_props + comp_critical_props

            col_for_add = cols_cnt - 1  # index column begin from 0
            row_idx = 0
            for prop in props:
                item = QTableWidgetItem(str(prop))
                item.setTextAlignment(Qt.AlignCenter)
                self.comps_table.setItem(row_idx, col_for_add, item)
                row_idx += 1

        self.comps_table.resizeColumnsToContents()

    def create_tab_conds(self):
        self.tab_conds = QWidget(self)

        self.create_conds_table()
        self.create_composition_table()

        self.determine_missing_for_calc()

    def create_conds_table(self):
        self.conds_table = QTableWidget(self.tab_conds)
        self.conds_table.setGeometry(0, 0, 400, 415)

        self.conds_table.setRowCount(len(self.conds_names))
        self.conds_table.setColumnCount(1)

        self.conds_table.setVerticalHeaderLabels(self.conds_names)
        self.conds_table.setHorizontalHeaderLabels(["Value"])
        self.conds_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for cond_idx in range(len(self.conds_names)):
            cond_name = self.conds_names[cond_idx]
            cond_val = self.stream.conds[self.conds_names[cond_idx]]
            if cond_val != "empty":
                match cond_name:
                    case "Temperature [C]":
                        self.T_is_defined = True
                    case "Pressure [Pa]":
                        self.P_is_defined = True
                    case "Mass Flow [kg/sec]":
                        self.flowrate_is_defined = True
            item = QTableWidgetItem(self.stream.conds[self.conds_names[cond_idx]])
            item.setTextAlignment(Qt.AlignCenter)
            self.conds_table.setItem(cond_idx, 0, item)

        self.determine_missing_for_calc()

        self.conds_table.itemChanged.connect(self.change_conds)

    def change_conds(self, item):
        # method itemChanged has information about changed item and can give it to function

        # each command, that calls item methods, calls itemChanged again, which can cause recursion, so we used block mode
        self.conds_table.blockSignals(True)

        item_row, item_col = item.row(), item.column()

        val = reformat_val_into_num(item)
        table_val = QTableWidgetItem(val)
        table_val.setTextAlignment(Qt.AlignCenter)
        self.conds_table.setItem(item_row, item_col, table_val)

        cond_name = self.conds_table.verticalHeaderItem(self.conds_table.currentRow())
        self.stream.conds[cond_name.text()] = val
        match cond_name.text():
            case "Temperature [C]":
                self.T_is_defined = True
            case "Pressure [Pa]":
                self.P_is_defined = True
            case "Mass Flow [kg/sec]":
                self.flowrate_is_defined = True
        self.determine_missing_for_calc()

        self.conds_table.blockSignals(False)

    def create_composition_table(self):
        self.composition_table = QTableWidget(self.tab_conds)
        self.composition_table.setGeometry(400, 0, 400, 415)

        self.composition_table.setColumnCount(3)
        rows_cnt = len(self.stream.comps) + 1  # the rows count is greater by 1 than the
        # actual number of components, because the last row for the sum
        self.composition_table.setRowCount(rows_cnt)

        self.composition_table.setHorizontalHeaderLabels(["Component", "Molar Fraction", "Mass Fraction"])
        self.composition_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        mass_frac_val, mol_frac_val = "empty", "empty"
        for idx in range(1, rows_cnt):
            comp_num = f"component {idx}"
            mass_frac_val = str(self.stream.fracs[comp_num]["Mass Fraction"])
            mass_frac = QTableWidgetItem(str(mass_frac_val))
            mass_frac.setTextAlignment(Qt.AlignCenter)
            mol_frac_val = str(self.stream.fracs[comp_num]["Molar Fraction"])
            mol_frac = QTableWidgetItem(str(mol_frac_val))
            mol_frac.setTextAlignment(Qt.AlignCenter)
            comp_name = QTableWidgetItem(self.stream.comps[comp_num].general_info.classification.name)
            row_for_add = idx - 1
            self.composition_table.setItem(row_for_add, 0, comp_name)
            self.composition_table.setItem(row_for_add, 1, mol_frac)
            self.composition_table.setItem(row_for_add, 2, mass_frac)

        if mol_frac_val != "empty":
            self.calc_fracs(1)
            self.determine_missing_for_calc()
        elif mass_frac_val != "empty":
            self.calc_fracs(2)
            self.determine_missing_for_calc()

        self.composition_table.setItem(rows_cnt - 1, 0, QTableWidgetItem("Total"))

        self.composition_table.itemChanged.connect(self.change_composition)

    def change_composition(self, item):
        # method itemChanged has information about changed item and can give it to function

        # each command, that calls item methods, calls itemChanged again, which can cause recursion, so we used block mode
        self.composition_table.blockSignals(True)

        self.composition_is_defined = False

        item_row, item_col = item.row(), item.column()

        known_comp_frac_idx = item_col  # known_comp_frac_idx: 1 - molar fraction, 2 - mass fraction (cf. composition table)

        val = reformat_val_into_num(item)
        self.save_new_frac_and_lose_old(known_comp_frac_idx, val)

        table_val = QTableWidgetItem(val)
        table_val.setTextAlignment(Qt.AlignCenter)
        self.composition_table.setItem(item_row, item_col, table_val)
        # if the composition was known, but we changed it, we need to recalculate the stream molar mass
        empty = QTableWidgetItem(str("empty"))
        empty.setTextAlignment(Qt.AlignCenter)
        self.props_table.setItem(0, 1, empty)  # (remove the old stream molar mass to start with)

        self.calc_fracs(known_comp_frac_idx)

        self.composition_table.blockSignals(False)

    def save_new_frac_and_lose_old(self, known_comp_frac_idx, val):

        unknown_comp_frac_idx = None
        comp_idx = self.composition_table.currentRow() + 1
        match known_comp_frac_idx:
            case 1:
                # saving changed information
                self.stream.fracs[f"component {comp_idx}"]["Molar Fraction"] = val
                unknown_comp_frac_idx = 2
            case 2:
                # saving changed information
                self.stream.fracs[f"component {comp_idx}"]["Mass Fraction"] = val
                unknown_comp_frac_idx = 1

        # losing the old fractions
        if self.composition_is_defined is False:
            for comp in range(self.composition_table.rowCount() - 1):
                # if we changed the fractions, we save him, and we lost the old fractions
                empty = QTableWidgetItem(str("empty"))
                empty.setTextAlignment(Qt.AlignCenter)
                self.composition_table.setItem(comp, unknown_comp_frac_idx, empty)
                if unknown_comp_frac_idx == 1:
                    self.stream.fracs[f"component {comp + 1}"]["Molar Fraction"] = "empty"
                else:
                    self.stream.fracs[f"component {comp + 1}"]["Mass Fraction"] = "empty"

    def calc_fracs(self, known_comp_frac_idx):
        self.composition_is_defined = calculate_total_frac(self.composition_is_defined, self.composition_table,
                                                           self.stream, self.props_table)
        if self.composition_is_defined is True:
            calculate_unknown_frac(known_comp_frac_idx, self.composition_table, self.stream)
            # plus calculates total fraction of unknown (at the start of function) component
            self.composition_is_defined = calculate_total_frac(self.composition_is_defined, self.composition_table,
                                                               self.stream, self.props_table)
        self.determine_missing_for_calc()

    def create_tab_props(self):
        self.tab_props = QWidget(self)

        self.create_props_table()
        # self.create_btn_calculate()

    def create_props_table(self):
        self.props_table = QTableWidget(self.tab_props)
        self.props_table.setGeometry(0, 0, 800, 415)

        self.props_table_vertical_headers_labels = self.stream.props_names
        stream_properties_count = len(self.props_table_vertical_headers_labels)

        self.props_table.setRowCount(stream_properties_count)
        self.props_table.setColumnCount(2)
        self.props_table.setHorizontalHeaderLabels(["Property", "Value"])
        for prop_name_idx in range(stream_properties_count):
            prop_name = QTableWidgetItem(self.props_table_vertical_headers_labels[prop_name_idx])
            self.props_table.setItem(prop_name_idx, 0, prop_name)

        for row_index in range(stream_properties_count):
            item = QTableWidgetItem("empty")
            item.setTextAlignment(Qt.AlignCenter)
            self.props_table.setItem(row_index, 1, item)

        self.props_table.resizeColumnsToContents()
        self.props_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def determine_missing_for_calc(self):
        conds_are_defined = [self.composition_is_defined, self.T_is_defined, self.P_is_defined, self.flowrate_is_defined]
        match conds_are_defined:
            case [True, True, True, True]:
                self.is_ok = True
                self.statusbar.showMessage("OK")
                self.statusbar.setStyleSheet("QStatusBar{background:rgb(0,255,0);color:black;font-weight:bold;}")

                self.define_phase(self.stream.comps, self.stream.conds, self.stream.fracs,
                                  float(self.stream.conds["Pressure [Pa]"]) / 133.33,
                                  float(self.stream.conds["Temperature [C]"]))
            case [True, False, False, False] | [True, False, True, False] | [True, False, True, True] | [True, False, False, True]:
                self.is_ok = False
                self.statusbar.showMessage("Temperature Unknown")
                self.statusbar.setStyleSheet("QStatusBar{background:rgb(255,0,0);color:black;font-weight:bold;}")
            case [True, True, False, False] | [True, True, False, True]:
                self.is_ok = False
                self.statusbar.showMessage("Pressure Unknown")
                self.statusbar.setStyleSheet("QStatusBar{background:rgb(255,0,0);color:black;font-weight:bold;}")
            case [True, True, True, False]:
                self.is_ok = False
                self.statusbar.showMessage("Mass Flow Unknown")
                self.statusbar.setStyleSheet("QStatusBar{background:rgb(255,0,0);color:black;font-weight:bold;}")

                self.define_phase(self.stream.comps, self.stream.conds, self.stream.fracs,
                                  float(self.stream.conds["Pressure [Pa]"]) / 133.33,
                                  float(self.stream.conds["Temperature [C]"]))
            case _:
                self.is_ok = False
                self.statusbar.showMessage("Composition Unknown")
                self.statusbar.setStyleSheet("QStatusBar{background:rgb(255,0,0);color:black;font-weight:bold;}")

        if self.is_ok:
            self.calc_stream_props(self.stream.conds, self.stream.comps, self.stream.fracs)
        else:
            for row_idx in range(self.props_table.rowCount()):
                prop_val = QTableWidgetItem("empty")
                prop_val.setTextAlignment(Qt.AlignCenter)
                self.props_table.setItem(row_idx, 1, prop_val)

            self.props_table.resizeColumnsToContents()

    def calc_stream_props(self, conds, comps, fracs):
        t_and_p_props, comps_props = self.get_data_for_calc(conds, comps, fracs)
        T_Celsius, T_Kelvin, P, P_mmhg, P_c, T_c, T_c_Kelvin = t_and_p_props
        w, mol_fracs, mass_fracs, mol_wts, phase, normal_bpt, H_f = comps_props

        # self.stream.props["IG Molar Volume [m3/mol]"] = calc_IG_mol_vol(P, T_Kelvin)
        mol_vol, a, b = calc_SRK_mol_vol(P, T_Kelvin, P_c, T_c_Kelvin, mol_fracs, w, phase)

        self.stream.props["SRK Molar Volume [m3/mol]"] = mol_vol
        stream_mol_wt = self.stream.props["Stream Molar Weight [g/mol]"]
        self.stream.props["Density [kg/m3]"] = calc_density(stream_mol_wt, mol_vol)
        if conds["Phase"] == "Vapour":
            mass_enthalpy = calc_gas_enthalpy(T_Kelvin, comps, H_f, mol_fracs, stream_mol_wt)
            self.stream.props["Mass Enthalpy [kJ/kg]"] = mass_enthalpy
            total_h_cap, h_caps = calc_IG_gas_h_cap(comps, mol_fracs, T_Kelvin)
            self.stream.props["Heat Capacity [J/mol-K]"] = total_h_cap
            total_viscosity, viscosities = calc_gas_viscosity(T_Kelvin, stream_mol_wt, mol_fracs, mol_wts)
            self.stream.props["Viscosity [Pa*s]"] = total_viscosity
            self.stream.props["Thermal Conductivity [W/m-K]"] = calc_gas_therm_cond(h_caps, viscosities, mol_fracs, mol_wts)
        elif conds["Phase"] == "Liquid":
            mass_enthalpy = calc_liquid_enthalpy(T_Kelvin, comps, H_f, mol_fracs, T_c_Kelvin, self.bpt, mol_wts, stream_mol_wt, w)
            self.stream.props["Mass Enthalpy [kJ/kg]"] = mass_enthalpy
            h_cap = calc_liquid_h_cap(T_Kelvin, T_c, w, mol_fracs, comps)
            self.stream.props["Heat Capacity [J/mol-K]"] = h_cap
            therm_cond = calc_liquid_therm_cond(mol_wts, T_Kelvin, self.bpt, T_c, mass_fracs)
            self.stream.props["Thermal Conductivity [W/m-K]"] = therm_cond
            viscosity = calc_liquid_viscosity(comps, mass_fracs, T_Kelvin)
            self.stream.props["Viscosity [Pa*s]"] = viscosity

        for row_idx in range(self.props_table.rowCount()):
            prop_name = self.props_table.item(row_idx, 0).text()
            prop_val = QTableWidgetItem(str(self.stream.props[prop_name]))
            prop_val.setTextAlignment(Qt.AlignCenter)
            self.props_table.setItem(row_idx, 1, prop_val)

        self.props_table.resizeColumnsToContents()

    def define_phase(self, comps, conds, fracs, p, t):
        self.bpt = calc_bpt(comps, p)
        mol_fracs = np.array([float(fracs[f"component {i + 1}"]["Molar Fraction"]) for i in range(len(fracs))])

        self.avg_bpt = sum(self.bpt * mol_fracs)
        print(f"[bpt] {self.bpt}")
        # print(f"[avg bpt] {self.avg_bpt}")

        self.conds_table.blockSignals(True)

        if t > max(self.bpt):
            # print("Vapour")

            conds["Phase"] = "Vapour"

            phase = QTableWidgetItem("Vapour")
            phase.setTextAlignment(Qt.AlignCenter)
            self.conds_table.setItem(3, 0, phase)
        elif t < min(self.bpt):
            # print("liquid")

            conds["Phase"] = "Liquid"

            phase = QTableWidgetItem("Liquid")
            phase.setTextAlignment(Qt.AlignCenter)
            self.conds_table.setItem(3, 0, phase)
        else:
            self.T_is_defined = False
            self.P_is_defined = False
            self.determine_missing_for_calc()

            # print("vapour-liquid")

            conds["Phase"] = "Vapour-Liquid"

            phase = QTableWidgetItem("Vapour-Liquid")
            phase.setTextAlignment(Qt.AlignCenter)
            self.conds_table.setItem(3, 0, phase)

            message_empty_curr_stream_table = QMessageBox(self)
            message_empty_curr_stream_table.setWindowTitle("Error")
            message_empty_curr_stream_table.setText('The program is not yet designed to calculate "gas-liquid" mixtures.' + "\n" +
                                                    'Please change the conditions')
            message_empty_curr_stream_table.show()

        self.conds_table.blockSignals(False)

    def get_data_for_calc(self, conds, comps, fracs):
        T_Celsius = float(conds["Temperature [C]"])
        T_Kelvin = T_Celsius + 273.15
        P = float(conds["Pressure [Pa]"])
        P_mmhg = P / 133.33
        # multiplied by 1000, because the pressure is in kPa, and in the equation the pressure is in Pa
        P_c = np.array([(float(comps[f"component {i + 1}"].general_info.critical_props.critical_P * 1000)) for i in range(len(comps))])
        T_c = np.array([(float(comps[f"component {i + 1}"].general_info.critical_props.critical_T)) for i in range(len(comps))])
        T_c_Kelvin = T_c + 273.15
        w = np.array([float(comps[f"component {i + 1}"].general_info.critical_props.acentricity) for i in range(len(comps))])
        mol_fracs = np.array([float(fracs[f"component {i + 1}"]["Molar Fraction"]) for i in range(len(fracs))])
        mass_fracs = np.array([float(fracs[f"component {i + 1}"]["Mass Fraction"]) for i in range(len(fracs))])
        mol_wts = np.array([(float(comps[f"component {i + 1}"].general_info.base_props.mol_wt)) for i in range(len(comps))])
        phase = conds["Phase"]
        normal_bpt = np.array([float(comps[f"component {i + 1}"].general_info.base_props.normal_bpt) for i in range(len(comps))])
        H_f = np.array([float(comps[f"component {i + 1}"].enthalpy.heat_of_formation.heat_of_formation_value[0]) for i in range(len(comps))])

        return [T_Celsius, T_Kelvin, P, P_mmhg, P_c, T_c, T_c_Kelvin], [w, mol_fracs, mass_fracs, mol_wts, phase, normal_bpt, H_f]

    def create_tabs(self):
        self.tabs = QTabWidget(self)
        self.tabs.setGeometry(0, 0, 800, 500)

        self.tabs.addTab(self.tab_comps, "Components")
        self.tabs.addTab(self.tab_conds, "Conditions")
        self.tabs.addTab(self.tab_props, "Properties")
