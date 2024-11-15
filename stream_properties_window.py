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
from functools import partial

from PyQt5.QtWidgets import (QMainWindow, QWidget, QTableWidget, QTableWidgetItem, QStatusBar, QTabWidget,
                             QAbstractItemView, QHeaderView, QMessageBox, QHBoxLayout, QSizePolicy, QVBoxLayout)
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QFont, QIcon
import numpy as np

from stream_calculation_functions import (calculate_total_frac, calculate_unknown_frac,
                                          calc_bpt, calc_liquid_viscosity,
                                          calc_liquid_h_cap, calc_liquid_therm_cond,
                                          calc_IG_mol_vol, calc_SRK_mol_vol,
                                          calc_density, calc_IG_gas_h_cap,
                                          calc_gas_viscosity, calc_gas_therm_cond,
                                          calc_gas_enthalpy, calc_liquid_enthalpy,
                                          calc_vapour_frac, calc_stream_mol_wt,
                                          calc_unknown_mass_frac, calc_total_frac_for_col,
                                          calc_stream_mol_wt_on_fracs)

conds_names = ["Temperature [C]",
               "Pressure [Pa]",
               "Mass Flow [kg/sec]"]


def reformat_val_into_num(val):
    val = str(val.text())
    if val not in ["Vapour", "Liquid", "Vapour-Liquid"]:
        res = val.replace(",", ".")
        res = "".join([char for char in res if (char == ".") or (char.isnumeric()) or (char == "-")])
    else:
        res = val
    return res


class StreamProperties(QMainWindow):
    def __init__(self, name, worksheet):
        super().__init__()

        self.worksheet = worksheet
        self.stream = self.worksheet.streams[name]
        self.name = name

        self.T_is_defined = False
        self.P_is_defined = False
        self.flowrate_is_defined = False
        self.composition_is_defined = False
        self.is_ok = False

        self.ui = StreamPropertiesUI()
        self.ui.setup_ui(self, self.worksheet)

    def load_data_to_comps_table(self):
        self.ui.comps_table.setRowCount(0)
        comps_cnt = len(self.stream.comps)

        for comp_idx in range(1, comps_cnt + 1):
            rows_cnt = self.ui.comps_table.rowCount() + 1
            self.ui.comps_table.setRowCount(rows_cnt)

            # we show classification, base and critical properties of component in components table,
            # so we need to pass values from stream to table
            comp_props = self.stream.comps[f"component {comp_idx}"]
            comp_classification = [list(comp_props.general_info.classification.output_props().values())[2]]
            comp_base_props = list(comp_props.general_info.base_props.output_props().values())[0:2]
            comp_critical_props = list(comp_props.general_info.critical_props.output_props().values())
            props = comp_classification + comp_base_props + comp_critical_props

            row_for_add = rows_cnt - 1  # index column begin from 0
            col_idx = 0
            for prop in props:
                if type(prop) is float:
                    prop = str(round(prop, 5))
                item = QTableWidgetItem(prop)
                item.setTextAlignment(Qt.AlignCenter)
                self.ui.comps_table.setItem(row_for_add, col_idx, item)
                col_idx += 1

        header = self.ui.comps_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

    def load_data_to_conds_table(self):
        phase = QTableWidgetItem(self.stream.conds["Phase"])
        phase.setTextAlignment(Qt.AlignCenter)

        self.ui.conds_table.blockSignals(True)
        self.determine_missing_for_calc()
        self.ui.conds_table.setItem(3, 0, phase)
        self.ui.conds_table.blockSignals(False)

    def load_data_to_composition_table(self):
        try:
            stream = self.worksheet.streams[self.name]

            frac_types = ["Molar Fraction", "Mass Fraction"]
            tables = [self.ui.molar_composition_table, self.ui.mass_composition_table]

            for i in range(2):
                table = tables[i]
                frac_type = frac_types[i]
                table.blockSignals(True)

                table.clearContents()

                for idx in range(1, table.rowCount()):
                    comp_num = f"component {idx}"
                    frac = stream.fracs[comp_num][frac_type]
                    if frac != "empty":
                        frac = round(float(frac), 4)
                    frac = QTableWidgetItem(str(frac))
                    frac.setTextAlignment(Qt.AlignCenter)
                    comp_name = QTableWidgetItem(stream.comps[comp_num].general_info.classification.name)
                    row_for_add = idx - 1

                    table.setItem(row_for_add, 0, comp_name)
                    table.setItem(row_for_add, 1, frac)

                table.setItem(table.rowCount() - 1, 0,
                                                  QTableWidgetItem(self.ui.translate("StreamProperties Window", "Total")))
                self.determine_missing_for_calc()

                for i in range(2, 4):
                    for j in range(table.rowCount() - 1):
                        item = QTableWidgetItem("empty")
                        item.setTextAlignment(Qt.AlignCenter)
                        # execute the line below to every item you need locked
                        item.setFlags(Qt.ItemIsEnabled)

                        table.setItem(j, i, item)

                table.blockSignals(False)

            if stream.fracs[f"component {self.ui.molar_composition_table.rowCount() - 1}"]["Molar Fraction"] != "empty":
                self.calc_fracs(self.ui.molar_composition_table, "Molar Fraction")
            elif stream.fracs[f"component {self.ui.mass_composition_table.rowCount() - 1}"]["Mass Fraction"] != "empty":
                self.calc_fracs(self.ui.mass_composition_table, "Mass Fraction")

        except: traceback.print_exc()

    def define_conds_flags(self, conds_table):
        for cond_idx in range(len(conds_names)):
            cond_name = conds_names[cond_idx]
            cond_val = self.stream.conds[conds_names[cond_idx]]
            if cond_val != "empty":
                if cond_name in ["Temperature [C]", "Температура [С]"]:
                    self.T_is_defined = True
                elif cond_name in ["Pressure [Pa]", "Давление [Па]"]:
                    self.P_is_defined = True
                elif cond_name in ["Mass Flow [kg/sec]", "Массовый расход [кг/с]"]:
                    self.flowrate_is_defined = True
            item = QTableWidgetItem(str(cond_val))
            item.setTextAlignment(Qt.AlignCenter)
            conds_table.setItem(cond_idx, 0, item)

    def change_conds(self, item):
        # method itemChanged has information about changed item and can give it to function
        # each command, that calls item methods, calls itemChanged again, which can cause recursion, so we used block mode
        self.ui.conds_table.blockSignals(True)

        item_row, item_col = item.row(), item.column()

        val = reformat_val_into_num(item)
        table_val = QTableWidgetItem(val)
        table_val.setTextAlignment(Qt.AlignCenter)
        self.ui.conds_table.setItem(item_row, item_col, table_val)

        cond_name = self.ui.conds_table.verticalHeaderItem(self.ui.conds_table.currentRow())

        if cond_name.text() in ["Temperature [C]", "Температура [С]"]:
            self.T_is_defined = True
            self.stream.conds["Temperature [C]"] = val
        elif cond_name.text() in ["Pressure [Pa]", "Давление [Па]"]:
            self.P_is_defined = True
            self.stream.conds["Pressure [Pa]"] = val
        elif cond_name.text() in ["Mass Flow [kg/sec]", "Массовый расход [кг/с]"]:
            self.flowrate_is_defined = True
            self.stream.conds["Mass Flow [kg/sec]"] = val
        self.determine_missing_for_calc()

        self.ui.conds_table.blockSignals(False)

    def change_composition(self, table, item):
        try:
            if item.text() != "empty":
                # method itemChanged has information about changed item and can give it to function
                # each command, that calls item methods, calls itemChanged again, which can cause recursion, so we used block mode
                table.blockSignals(True)

                self.composition_is_defined = False

                item_row, item_col = item.row(), item.column()

                known_comp_frac = table.horizontalHeaderItem(1).text()

                val = reformat_val_into_num(item)
                comp_idx = table.currentRow() + 1

                self.save_new_frac_and_lose_old(comp_idx, known_comp_frac, val)

                table_val = QTableWidgetItem(val)
                table_val.setTextAlignment(Qt.AlignCenter)
                table.setItem(item_row, item_col, table_val)
                # if the composition was known, but we changed it, we need to recalculate the stream molar mass
                empty = QTableWidgetItem(str("empty"))
                empty.setTextAlignment(Qt.AlignCenter)
                self.ui.props_table.setItem(0, 1, empty)  # (remove the old stream molar mass to start with)

                self.calc_fracs(table, known_comp_frac)

                table.blockSignals(False)
        except: traceback.print_exc()

    def save_new_frac_and_lose_old(self, comp_idx, known_comp_frac, val):
        unknown_comp_frac, table = None, None
        match known_comp_frac:
            case "Molar Fraction" | "Мольная доля":
                # saving changed information
                self.stream.fracs[f"component {comp_idx}"]["Molar Fraction"] = val
                unknown_comp_frac = "Mass Fraction"
                table = self.ui.mass_composition_table
            case "Mass Fraction" | "Массовая доля":
                # saving changed information
                self.stream.fracs[f"component {comp_idx}"]["Mass Fraction"] = val
                unknown_comp_frac = "Molar Fraction"
                table = self.ui.molar_composition_table
        table.blockSignals(True)
        # losing the old fractions
        if self.composition_is_defined is False:
            for comp in range(table.rowCount() - 1):
                # if we changed the fractions, we save him, and we lost the old fractions
                empty = QTableWidgetItem(str("empty"))
                empty.setTextAlignment(Qt.AlignCenter)
                table.setItem(comp, 1, empty)
                if unknown_comp_frac == "Molar Fraction":
                    self.stream.fracs[f"component {comp + 1}"]["Molar Fraction"] = "empty"
                else:
                    self.stream.fracs[f"component {comp + 1}"]["Mass Fraction"] = "empty"
        table.blockSignals(False)

    def calc_fracs(self, table, known_comp_frac):
        self.composition_is_defined = calculate_total_frac(self.composition_is_defined, known_comp_frac, table,
                                                           self.stream)

        if self.composition_is_defined is True:
            known_comp_frac, table = calculate_unknown_frac(known_comp_frac, self)
            # plus calculates total fraction of unknown (at the start of function) component
            self.composition_is_defined = calculate_total_frac(self.composition_is_defined, known_comp_frac, table,
                                                               self.stream)
        self.determine_missing_for_calc()

    def determine_missing_for_calc(self):
        conds_are_defined = [self.composition_is_defined, self.T_is_defined, self.P_is_defined, self.flowrate_is_defined]
        # print(conds_are_defined)
        match conds_are_defined:
            case [True, True, True, True]:
                self.is_ok = True
                self.ui.statusbar.showMessage(self.ui.translate("StreamProperties Window", "OK"))
                self.ui.statusbar.setStyleSheet("QStatusBar{background:rgb(0,255,0);color:black;font-weight:bold;}")
            case [True, False, False, False] | [True, False, True, False] | [True, False, True, True] | [True, False, False, True]:
                self.is_ok = False
                self.ui.statusbar.showMessage(self.ui.translate("StreamProperties Window", "Temperature Unknown"))
                self.ui.statusbar.setStyleSheet("QStatusBar{background:rgb(255,0,0);color:black;font-weight:bold;}")
            case [True, True, False, False] | [True, True, False, True]:
                self.is_ok = False
                self.ui.statusbar.showMessage(self.ui.translate("StreamProperties Window", "Pressure Unknown"))
                self.ui.statusbar.setStyleSheet("QStatusBar{background:rgb(255,0,0);color:black;font-weight:bold;}")
            case [True, True, True, False]:
                self.is_ok = False
                self.ui.statusbar.showMessage(self.ui.translate("StreamProperties Window", "Mass Flow Unknown"))
                self.ui.statusbar.setStyleSheet("QStatusBar{background:rgb(255,0,0);color:black;font-weight:bold;}")
            case _:
                self.is_ok = False
                self.ui.statusbar.showMessage(self.ui.translate("StreamProperties Window", "Composition Unknown"))
                self.ui.statusbar.setStyleSheet("QStatusBar{background:rgb(255,0,0);color:black;font-weight:bold;}")

        if self.is_ok:
            self.calc_stream_props(self.stream.conds, self.stream.comps, self.stream.fracs)
        else:
            for row_idx in range(self.ui.props_table.rowCount()):
                prop_val = QTableWidgetItem("empty")
                prop_val.setTextAlignment(Qt.AlignCenter)
                self.ui.props_table.setItem(row_idx, 1, prop_val)

            self.ui.props_table.resizeColumnsToContents()

    def calc_stream_props(self, conds, comps, fracs):
        try:
            t_and_p_props, comps_props = self.get_data_for_calc(conds, comps, fracs)
            T_Celsius, T_Kelvin, P, P_mmhg, P_c, T_c, T_c_Kelvin, mass_flow = t_and_p_props
            w, mol_fracs, mass_fracs, mol_wts, normal_bpt, bpt, H_f, antoine_coeffs = comps_props
            stream_mol_wt = self.stream.props["Stream Molar Weight [g/mol]"]

            t, p, props = [T_Kelvin, T_Celsius], [P_mmhg, P], [mol_fracs, antoine_coeffs, mol_wts]
            phase, phase_props = self.define_phase(conds, t, p, props, mass_flow, stream_mol_wt)
            if phase in ["Vapour-Liquid", "Газ-Жидкость"]:
                self.calc_vap_liq_stream(comps, t_and_p_props, comps_props, stream_mol_wt, phase, phase_props)
            else:
                self.stream.props["IG Molar Volume [m3/mol]"] = calc_IG_mol_vol(P, T_Kelvin)
                mol_vol, a, b = calc_SRK_mol_vol(P, T_Kelvin, P_c, T_c_Kelvin, mol_fracs, w, phase)

                self.stream.props["SRK Molar Volume [m3/mol]"] = mol_vol
                density = calc_density(stream_mol_wt, mol_vol)
                self.stream.props["Density [kg/m3]"] = density
                if phase in ["Vapour", "Газ"]:
                    # stream
                    mass_enthalpy = calc_gas_enthalpy(T_Kelvin, comps, H_f, mol_fracs, stream_mol_wt)
                    self.stream.props["Mass Enthalpy [kJ/kg]"] = mass_enthalpy
                    total_h_cap, h_caps = calc_IG_gas_h_cap(comps, mol_fracs, T_Kelvin)
                    self.stream.props["Heat Capacity [J/mol-K]"] = total_h_cap
                    total_viscosity, viscosities = calc_gas_viscosity(T_Kelvin, stream_mol_wt, mol_fracs, mol_wts)
                    self.stream.props["Viscosity [Pa*s]"] = total_viscosity
                    therm_cond = calc_gas_therm_cond(h_caps, viscosities, mol_fracs, mol_wts)
                    self.stream.props["Thermal Conductivity [W/m-K]"] = therm_cond
                    # vapour phase
                    self.stream.vap_phase_props["Stream Molar Weight [g/mol]"] = stream_mol_wt
                    self.stream.vap_phase_props["SRK Molar Volume [m3/mol]"] = mol_vol
                    self.stream.vap_phase_props["Density [kg/m3]"] = density
                    self.stream.vap_phase_props["Mass Enthalpy [kJ/kg]"] = mass_enthalpy
                    self.stream.vap_phase_props["Heat Capacity [J/mol-K]"] = total_h_cap
                    self.stream.vap_phase_props["Viscosity [Pa*s]"] = total_viscosity
                    self.stream.vap_phase_props["Thermal Conductivity [W/m-K]"] = therm_cond
                    # liquid phase
                    for prop_name in self.stream.liq_phase_props.keys():
                        self.stream.liq_phase_props[prop_name] = 0
                elif phase in ["Liquid", "Жидкость"]:
                    # stream
                    mass_enthalpy = calc_liquid_enthalpy(T_Kelvin, comps, H_f, mol_fracs, T_c_Kelvin, bpt, mass_fracs, mol_wts, stream_mol_wt, w)
                    self.stream.props["Mass Enthalpy [kJ/kg]"] = mass_enthalpy
                    h_cap = calc_liquid_h_cap(T_Kelvin, T_c, w, mol_fracs, comps)
                    self.stream.props["Heat Capacity [J/mol-K]"] = h_cap
                    therm_cond = calc_liquid_therm_cond(mol_wts, T_Kelvin, bpt, T_c, mass_fracs)
                    self.stream.props["Thermal Conductivity [W/m-K]"] = therm_cond
                    viscosity = calc_liquid_viscosity(comps, mass_fracs, T_Kelvin)
                    self.stream.props["Viscosity [Pa*s]"] = viscosity
                    # liquid phase
                    self.stream.liq_phase_props["Stream Molar Weight [g/mol]"] = stream_mol_wt
                    self.stream.liq_phase_props["SRK Molar Volume [m3/mol]"] = mol_vol
                    self.stream.liq_phase_props["Density [kg/m3]"] = density
                    self.stream.liq_phase_props["Mass Enthalpy [kJ/kg]"] = mass_enthalpy
                    self.stream.liq_phase_props["Heat Capacity [J/mol-K]"] = h_cap
                    self.stream.liq_phase_props["Viscosity [Pa*s]"] = viscosity
                    self.stream.liq_phase_props["Thermal Conductivity [W/m-K]"] = therm_cond
                    # vapour phase
                    for prop_name in self.stream.vap_phase_props.keys():
                        self.stream.vap_phase_props[prop_name] = 0

            for row_idx in range(self.ui.props_table.rowCount()):
                prop_name = self.stream.props_names[row_idx]
                prop_val = '{0:.7f}'.format(round(float(self.stream.props[prop_name]), 7))
                prop_val = QTableWidgetItem(prop_val)
                prop_val.setTextAlignment(Qt.AlignCenter)
                self.ui.props_table.setItem(row_idx, 0, prop_val)
            # self.ui.props_table.resizeColumnsToContents()

            props_dict = [self.stream.vap_phase_props, self.stream.liq_phase_props]
            for i in range(2):
                for row_idx in range(self.ui.props_table.rowCount()):
                    prop_name = self.stream.props_names[row_idx]
                    prop_val = '{0:.7f}'.format(round(float(props_dict[i][prop_name]), 7))
                    prop_val = QTableWidgetItem(prop_val)
                    prop_val.setTextAlignment(Qt.AlignCenter)
                    self.ui.props_table.setItem(row_idx, i + 1, prop_val)

            self.ui.props_table.resizeColumnsToContents()
        except: traceback.print_exc()

    def calc_vap_liq_stream(self, comps, t_and_p_props, comps_props, stream_mol_wt, phase, phase_props):
        print("vap-liq")
        T_Celsius, T_Kelvin, P, P_mmhg, P_c, T_c, T_c_Kelvin, mass_flow = t_and_p_props
        w, mol_fracs, mass_fracs, mol_wts, normal_bpt, bpt, H_f, antoine_coeffs = comps_props
        vapour_frac, liq_mol_fracs, vap_mol_fracs, liq_mass_fracs, vap_mass_fracs, vap_stream_mol_wt, liq_stream_mol_wt = phase_props

        vap_mol_vol, liq_mol_vol = calc_SRK_mol_vol(P, T_Kelvin, P_c, T_c_Kelvin, mol_fracs, w, phase)
        # vapour phase
        self.stream.vap_phase_props["Stream Molar Weight [g/mol]"] = vap_stream_mol_wt
        self.stream.vap_phase_props["SRK Molar Volume [m3/mol]"] = vap_mol_vol
        self.stream.vap_phase_props["Density [kg/m3]"] = calc_density(vap_stream_mol_wt, vap_mol_vol)
        vap_mass_enthalpy = calc_gas_enthalpy(T_Kelvin, comps, H_f, vap_mol_fracs, vap_stream_mol_wt)
        self.stream.vap_phase_props["Mass Enthalpy [kJ/kg]"] = vap_mass_enthalpy
        vap_total_h_cap, vap_h_caps = calc_IG_gas_h_cap(comps, vap_mol_fracs, T_Kelvin)
        self.stream.vap_phase_props["Heat Capacity [J/mol-K]"] = vap_total_h_cap
        vap_total_viscosity, vap_viscosities = calc_gas_viscosity(T_Kelvin, vap_stream_mol_wt, vap_mol_fracs, mol_wts)
        self.stream.vap_phase_props["Viscosity [Pa*s]"] = vap_total_viscosity
        vap_therm_cond = calc_gas_therm_cond(vap_h_caps, vap_viscosities, vap_mol_fracs, mol_wts)
        self.stream.vap_phase_props["Thermal Conductivity [W/m-K]"] = vap_therm_cond
        # liquid phase
        self.stream.liq_phase_props["Stream Molar Weight [g/mol]"] = liq_stream_mol_wt
        self.stream.liq_phase_props["SRK Molar Volume [m3/mol]"] = liq_mol_vol
        self.stream.liq_phase_props["Density [kg/m3]"] = calc_density(liq_stream_mol_wt, liq_mol_vol)
        liq_mass_enthalpy = calc_liquid_enthalpy(T_Kelvin, comps, H_f, liq_mol_fracs, T_c_Kelvin, bpt, liq_mass_fracs, mol_wts, liq_stream_mol_wt, w)
        self.stream.liq_phase_props["Mass Enthalpy [kJ/kg]"] = liq_mass_enthalpy
        liq_h_cap = calc_liquid_h_cap(T_Kelvin, T_c, w, liq_mol_fracs, comps)
        self.stream.liq_phase_props["Heat Capacity [J/mol-K]"] = liq_h_cap
        liq_therm_cond = calc_liquid_therm_cond(mol_wts, T_Kelvin, bpt, T_c, liq_mass_fracs)
        self.stream.liq_phase_props["Thermal Conductivity [W/m-K]"] = liq_therm_cond
        liq_viscosity = calc_liquid_viscosity(comps, liq_mass_fracs, T_Kelvin)
        self.stream.liq_phase_props["Viscosity [Pa*s]"] = liq_viscosity
        # stream
        stream_mol_vol = vapour_frac * vap_mol_vol + (1 - vapour_frac) * liq_mol_vol

        # self.stream.props["Stream Molar Weight [g/mol]"] = vapour_frac * vap_stream_mol_wt + (1 - vapour_frac) * liq_stream_mol_wt
        self.stream.props["SRK Molar Volume [m3/mol]"] = stream_mol_vol
        self.stream.props["Density [kg/m3]"] = calc_density(stream_mol_wt, stream_mol_vol)
        self.stream.props["Mass Enthalpy [kJ/kg]"] = vapour_frac * vap_stream_mol_wt / stream_mol_wt * vap_mass_enthalpy + (1 - vapour_frac) * liq_stream_mol_wt / stream_mol_wt * liq_mass_enthalpy
        self.stream.props["Heat Capacity [J/mol-K]"] = vapour_frac * vap_total_h_cap + (1 - vapour_frac) * liq_h_cap
        self.stream.props["Thermal Conductivity [W/m-K]"] = vapour_frac * vap_therm_cond + (1 - vapour_frac) * liq_therm_cond
        self.stream.props["Viscosity [Pa*s]"] = (vap_total_viscosity * liq_viscosity) / (vapour_frac * liq_viscosity + (1 - vapour_frac) * vap_total_viscosity)


    def define_phase(self, conds, t, p, props, mass_flow, stream_mol_wt):
        try:
            T_Kelvin, T_Celsius = t
            P_mmHg, P_Pa = p
            mol_fracs, coeffs, mol_wts = props
            print("define phase")

            vapour_frac, liq_total_frac, vap_total_frac, liq_mol_fracs, vap_mol_fracs = calc_vapour_frac(T_Kelvin, P_mmHg, mol_fracs, coeffs)
            vap_stream_mol_wt = calc_stream_mol_wt_on_fracs(mol_wts, vap_mol_fracs)
            liq_stream_mol_wt = calc_stream_mol_wt_on_fracs(mol_wts, liq_mol_fracs)

            self.ui.conds_table.blockSignals(True)

            mass_flows = [mass_flow * vapour_frac * vap_stream_mol_wt / stream_mol_wt,  mass_flow * (1 - vapour_frac) * liq_stream_mol_wt / stream_mol_wt]
            for i in range(2):
                T = QTableWidgetItem(str(T_Celsius))
                T.setTextAlignment(Qt.AlignCenter)
                T.setFlags(Qt.ItemIsEnabled)
                self.ui.conds_table.setItem(0, i + 1, T)

                P = QTableWidgetItem(str(P_Pa))
                P.setTextAlignment(Qt.AlignCenter)
                P.setFlags(Qt.ItemIsEnabled)
                self.ui.conds_table.setItem(1, i + 1, P)

                flow = QTableWidgetItem(str(round(mass_flows[i], 3)))
                flow.setTextAlignment(Qt.AlignCenter)
                flow.setFlags(Qt.ItemIsEnabled)
                self.ui.conds_table.setItem(2, i + 1, flow)

            composition_tables = [self.ui.molar_composition_table, self.ui.mass_composition_table]

            self.ui.molar_composition_table.blockSignals(True)
            self.ui.mass_composition_table.blockSignals(True)

            vap_mass_fracs, liq_mass_fracs = [], []
            for i in range(len(mol_fracs)):  # i == comp number
                vap_mol_frac = vap_mol_fracs[i]
                self.stream.vap_phase_fracs[f"component {i + 1}"]["Molar Fraction"] = vap_mol_frac
                vap_mass_frac = calc_unknown_mass_frac(vap_mol_frac, mol_wts[i], vap_stream_mol_wt)
                self.stream.vap_phase_fracs[f"component {i + 1}"]["Mass Fraction"] = vap_mass_frac
                vap_mass_fracs.append(vap_mass_frac)

                vap_mol_frac = QTableWidgetItem('{0:.4f}'.format(round(vap_mol_frac, 4)))
                vap_mol_frac.setTextAlignment(Qt.AlignCenter)
                vap_mol_frac.setFlags(Qt.ItemIsEnabled)
                self.ui.molar_composition_table.setItem(i, 2, vap_mol_frac)

                vap_mass_frac = QTableWidgetItem('{0:.4f}'.format(round(vap_mass_frac, 4)))
                vap_mass_frac.setTextAlignment(Qt.AlignCenter)
                vap_mass_frac.setFlags(Qt.ItemIsEnabled)
                self.ui.mass_composition_table.setItem(i, 2, vap_mass_frac)

                liq_mol_frac = liq_mol_fracs[i]
                self.stream.liq_phase_fracs[f"component {i + 1}"]["Molar Fraction"] = liq_mol_frac
                liq_mass_frac = calc_unknown_mass_frac(liq_mol_frac, mol_wts[i], liq_stream_mol_wt)
                self.stream.liq_phase_fracs[f"component {i + 1}"]["Mass Fraction"] = liq_mass_frac
                liq_mass_fracs.append(liq_mass_frac)

                liq_mol_frac = QTableWidgetItem('{0:.4f}'.format(round(liq_mol_frac, 4)))
                liq_mol_frac.setTextAlignment(Qt.AlignCenter)
                liq_mol_frac.setFlags(Qt.ItemIsEnabled)
                self.ui.molar_composition_table.setItem(i, 3, liq_mol_frac)

                liq_mass_frac = QTableWidgetItem('{0:.4f}'.format(round(liq_mass_frac, 4)))
                liq_mass_frac.setTextAlignment(Qt.AlignCenter)
                liq_mass_frac.setFlags(Qt.ItemIsEnabled)
                self.ui.mass_composition_table.setItem(i, 3, liq_mass_frac)

            phase_fracs = [[vap_mol_fracs, liq_mol_fracs], [vap_mass_fracs, liq_mass_fracs]]
            for idx in range(len(composition_tables)):
                for col in range(2, 4):
                    table = composition_tables[idx]
                    fracs = phase_fracs[idx][col - 2]
                    col_total_frac = calc_total_frac_for_col(fracs)
                    col_total_frac = QTableWidgetItem(str(round(col_total_frac, 3)))
                    col_total_frac.setTextAlignment(Qt.AlignCenter)
                    col_total_frac.setFlags(Qt.ItemIsEnabled)
                    table.setItem(table.rowCount() - 1, col, col_total_frac)

            self.ui.molar_composition_table.blockSignals(False)
            self.ui.mass_composition_table.blockSignals(False)

            if liq_total_frac == 0:
                conds["Phase"] = "Vapour"
                # if self.worksheet.curr_lang == "English":
                #     conds["Phase"] = "Vapour"
                # elif self.worksheet.curr_lang == "Russian":
                #     conds["Phase"] = "Газ"
            elif vap_total_frac == 0:
                conds["Phase"] = "Liquid"
                if self.worksheet.curr_lang == "English":
                    conds["Phase"] = "Liquid"
                #     phase = QTableWidgetItem("Liquid")
                # elif self.worksheet.curr_lang == "Russian":
                #     conds["Phase"] = "Жидкость"
                #     phase = QTableWidgetItem("Жидкость")
            else:
                conds["Phase"] = "Vapour-Liquid"
                # if self.worksheet.curr_lang == "English":
                #     conds["Phase"] = "Vapour-Liquid"
                # elif self.worksheet.curr_lang == "Russian":
                #     conds["Phase"] = "Газ-Жидкость"

            self.ui.conds_table.blockSignals(False)
            return conds["Phase"], [vapour_frac, liq_mol_fracs, vap_mol_fracs, liq_mass_fracs, vap_mass_fracs, vap_stream_mol_wt, liq_stream_mol_wt]
        except: traceback.print_exc()

    @staticmethod
    def get_data_for_calc(conds, comps, fracs):
        try:
            T_Celsius = float(conds["Temperature [C]"])
            T_Kelvin = T_Celsius + 273.15
            P = float(conds["Pressure [Pa]"])
            P_mmhg = P / 133.33
            # multiplied by 1000, because the pressure is in kPa, and in the equation the pressure is in Pa
            P_c = np.array([(float(comps[f"component {i + 1}"].general_info.critical_props.critical_P * 1000)) for i in range(len(comps))])
            T_c = np.array([(float(comps[f"component {i + 1}"].general_info.critical_props.critical_T)) for i in range(len(comps))])
            T_c_Kelvin = T_c + 273.15
            mass_flow = float(conds["Mass Flow [kg/sec]"])

            w = np.array([float(comps[f"component {i + 1}"].general_info.critical_props.acentricity) for i in range(len(comps))])
            mol_fracs = np.array([float(fracs[f"component {i + 1}"]["Molar Fraction"]) for i in range(len(fracs))])
            mass_fracs = np.array([float(fracs[f"component {i + 1}"]["Mass Fraction"]) for i in range(len(fracs))])
            mol_wts = np.array([(float(comps[f"component {i + 1}"].general_info.base_props.mol_wt)) for i in range(len(comps))])
            normal_bpt = np.array([float(comps[f"component {i + 1}"].general_info.base_props.normal_bpt) for i in range(len(comps))])
            bpt = calc_bpt(comps, P_mmhg)
            H_f = np.array([float(comps[f"component {i + 1}"].enthalpy.heat_of_formation.heat_of_formation_value[0]) for i in range(len(comps))])
            antoine_coeffs = [0 for _ in range(len(mol_fracs))]
            for idx, comp_name in enumerate(list(comps.keys())):
                comp = comps[comp_name]
                a = comp.antoine_eq.antoine_eq_coeffs.a
                b = comp.antoine_eq.antoine_eq_coeffs.b
                c = comp.antoine_eq.antoine_eq_coeffs.c
                antoine_coeffs[idx] = [a, b, c]

            return [T_Celsius, T_Kelvin, P, P_mmhg, P_c, T_c, T_c_Kelvin, mass_flow], [w, mol_fracs, mass_fracs, mol_wts, normal_bpt, bpt, H_f, antoine_coeffs]
        except: traceback.print_exc()

class StreamPropertiesUI:
    def setup_ui(self, window, worksheet):
        self.stream_props_window = window
        self.stream_props_window.setWindowIcon(QIcon("./pics/program_icon.png"))

        self.worksheet = worksheet

        self.translate = QCoreApplication.translate
        self.size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.stream_props_window.resize(1600, 768)
        self.stream_props_window.setSizePolicy(self.size_policy)

        self.central_widget = QWidget(self.stream_props_window)
        self.central_widget.setSizePolicy(self.size_policy)
        self.stream_props_window.setCentralWidget(self.central_widget)

        self.create_statusbar(self.stream_props_window)
        self.create_tab_comps(self.stream_props_window)
        self.create_tab_props(self.stream_props_window)
        self.create_tab_conds(self.stream_props_window)
        # creating tabs must be initialized after creating the objects
        self.create_tabs(self.stream_props_window)

        layout = QHBoxLayout()
        layout.addWidget(self.tabs)

        self.central_widget.setLayout(layout)

        self.retranslate_ui(self.stream_props_window)

    def create_statusbar(self, parent):
        self.statusbar = QStatusBar(parent)
        self.statusbar.setStyleSheet("QStatusBar{background:rgb(255,0,0);color:black;font-weight:bold;}")
        parent.setStatusBar(self.statusbar)

    def create_tab_comps(self, parent):
        self.tab_comps = QWidget(parent)
        self.tab_comps.setSizePolicy(self.size_policy)

        self.create_comps_table(self.tab_comps)
        parent.load_data_to_comps_table()

        layout = QHBoxLayout()
        layout.addWidget(self.comps_table)
        self.tab_comps.setLayout(layout)

    def create_comps_table(self, tab):
        self.comps_table = QTableWidget(tab)
        self.comps_table.setFont(QFont("Segoe UI", 10))

        self.comps_table.setColumnCount(7)  # 7 свойств я хочу выводить в эту таблицу
        self.comps_table.setRowCount(0)

        self.comps_table.resizeColumnsToContents()
        self.comps_table.horizontalHeader().setStretchLastSection(True)
        self.comps_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def create_tab_conds(self, parent):
        self.tab_conds = QWidget(parent)
        self.tab_conds.setSizePolicy(self.size_policy)

        self.create_conds_table(self.tab_conds, parent)
        self.create_composition_table(self.tab_conds, parent)

        layout = QHBoxLayout()
        layout.addWidget(self.conds_table)
        layout.addWidget(self.composition_widget)
        self.tab_conds.setLayout(layout)

        parent.determine_missing_for_calc()

    def create_conds_table(self, tab, parent):
        self.conds_table = QTableWidget(tab)
        self.conds_table.setFont(QFont("Segoe UI", 10))

        self.conds_table.setRowCount(len(conds_names))
        self.conds_table.setColumnCount(3)

        for i in range(len(conds_names)):
            for j in range(1, 3):
                item = QTableWidgetItem("empty")
                item.setTextAlignment(Qt.AlignCenter)
        #         # execute the line below to every item you need locked
                item.setFlags(Qt.ItemIsEnabled)
                self.conds_table.setItem(i, j, item)

        self.conds_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        parent.define_conds_flags(self.conds_table)

        parent.determine_missing_for_calc()

        self.conds_table.itemChanged.connect(parent.change_conds)

    def create_composition_table(self, tab, parent):
        try:
            stream = self.worksheet.streams[parent.name]

            self.composition_widget = QWidget(tab)
            layout = QVBoxLayout()

            self.molar_composition_table, self.mass_composition_table = QTableWidget(self.composition_widget), QTableWidget(self.composition_widget)
            rows_cnt = len(stream.comps) + 1  # the rows count is greater by 1 than the
            # actual number of components, because the last row for the sum
            frac_type = ["Mass Fraction", "Molar Fraction"]

            for idx, table in enumerate([self.molar_composition_table, self.mass_composition_table]):
                table.setFont(QFont("Segoe UI", 10))
                table.setRowCount(rows_cnt)
                table.setColumnCount(4)
                table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

                table.itemChanged.connect(partial(parent.change_composition, table))

            parent.load_data_to_composition_table()

            layout.addWidget(self.molar_composition_table)
            layout.addWidget(self.mass_composition_table)
            layout.setContentsMargins(0, 0, 0, 0)

            self.composition_widget.setLayout(layout)
        except: traceback.print_exc()

    def create_tab_props(self, parent):
        self.tab_props = QWidget(parent)
        self.tab_props.setSizePolicy(self.size_policy)

        self.create_props_table(self.tab_props, parent)

        layout = QHBoxLayout()
        layout.addWidget(self.props_table)
        self.tab_props.setLayout(layout)

    def create_props_table(self, tab, parent):
        self.props_table = QTableWidget(tab)
        self.props_table.setFont(QFont("Segoe UI", 10))

        stream_props_cnt = len(parent.stream.props_names)
        self.props_table.setRowCount(stream_props_cnt)
        self.props_table.setColumnCount(3)

        for row_idx in range(stream_props_cnt):
            item = QTableWidgetItem("empty")
            item.setTextAlignment(Qt.AlignCenter)
            self.props_table.setItem(row_idx, 0, item)

        self.props_table.resizeColumnsToContents()
        self.props_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def create_tabs(self, parent):
        self.tabs = QTabWidget(parent)
        self.tabs.setSizePolicy(self.size_policy)
        self.tabs.setFont(QFont("Segoe UI", 10))

        self.tabs.addTab(self.tab_comps, self.translate("StreamProperties Window", "Components"))
        self.tabs.addTab(self.tab_conds, self.translate("StreamProperties Window", "Conditions"))
        self.tabs.addTab(self.tab_props, self.translate("StreamProperties Window", "Properties"))

    def retranslate_ui(self, parent):
        parent.setWindowTitle(self.translate("StreamProperties Window", "Stream Properties of") + f" {parent.name}")
        self.statusbar.showMessage(self.translate("StreamProperties Window", "Composition Unknown"))

        self.props_table.setHorizontalHeaderLabels([self.translate("StreamProperties Window", "Value")])
        self.props_table.setVerticalHeaderLabels([self.translate("StreamProperties Window", "Stream Molar Weight [g/mol]"),
                                                  self.translate("StreamProperties Window", "Mass Enthalpy [kJ/kg]"),
                                                  self.translate("StreamProperties Window", "SRK Molar Volume [m3/mol]"),
                                                  self.translate("StreamProperties Window", "Density [kg/m3]"),
                                                  self.translate("StreamProperties Window", "Heat Capacity [J/mol-K]"),
                                                  self.translate("StreamProperties Window", "Viscosity [Pa*s]"),
                                                  self.translate("StreamProperties Window", "Thermal Conductivity [W/m-K]")])
        self.molar_composition_table.setHorizontalHeaderLabels([self.translate("StreamProperties Window", "Component"),
                                                                self.translate("StreamProperties Window", "Molar Fraction"),
                                                                self.translate("StreamProperties Window", "Vapour Molar Fraction"),
                                                                self.translate("StreamProperties Window", "Liquid Molar Fraction")])
        self.mass_composition_table.setHorizontalHeaderLabels([self.translate("StreamProperties Window", "Component"),
                                                               self.translate("StreamProperties Window", "Mass Fraction"),
                                                               self.translate("StreamProperties Window", "Vapour Mass Fraction"),
                                                               self.translate("StreamProperties Window", "Liquid Mass Fraction")])
        self.conds_table.setHorizontalHeaderLabels([self.translate("StreamProperties Window", parent.name),
                                                    self.translate("StreamProperties Window", "Vapour Phase"),
                                                    self.translate("StreamProperties Window", "Liquid Phase")])
        self.conds_table.setVerticalHeaderLabels([self.translate("StreamProperties Window", "Temperature [C]"),
                                                  self.translate("StreamProperties Window", "Pressure [Pa]"),
                                                  self.translate("StreamProperties Window", "Mass Flow [kg/sec]"),
                                                  self.translate("StreamProperties Window", "Phase")])
        self.comps_table.setHorizontalHeaderLabels([self.translate("StreamProperties Window", "Name"),
                                                    self.translate("StreamProperties Window", "Molar Weight [g / mol]"),
                                                    self.translate("StreamProperties Window", "Normal Boiling Point [C]"),
                                                    self.translate("StreamProperties Window", "Critical Temperature [C]"),
                                                    self.translate("StreamProperties Window", "Critical Pressure [kPa]"),
                                                    self.translate("StreamProperties Window", "Critical Volume [m3 / kgmole]"),
                                                    self.translate("StreamProperties Window", "Acentricity")])
        self.props_table.setHorizontalHeaderLabels([self.translate("StreamProperties Window", parent.name),
                                                    self.translate("StreamProperties Window", "Vapour Phase"),
                                                    self.translate("StreamProperties Window", "Liquid Phase")])

        self.tabs.setTabText(0, self.translate("StreamProperties Window", "Components"))
        self.tabs.setTabText(1, self.translate("StreamProperties Window", "Conditions"))
        self.tabs.setTabText(2, self.translate("StreamProperties Window", "Properties"))
