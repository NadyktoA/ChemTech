# fracs = fractions
# idx = index
# cnt = count
# comps = components
# cond/conds = condition/conditions
# curr = current
# props = properties
# res = result


class Stream:
    def __init__(self, name, conds_names, chosen_comps):
        super().__init__()
        self.name = name
        self.conds_names = conds_names
        self.chosen_comps = chosen_comps

        self.comps = {}

        self.conds = {}

        self.fracs = {}
        self.vap_phase_fracs = {}
        self.liq_phase_fracs = {}

        self.props = {}
        self.vap_phase_props = {}
        self.liq_phase_props = {}

        self.fill_in_stream_props()

    def fill_in_stream_props(self):
        self.fill_in_conds()
        self.fill_in_comps_and_fracs()
        self.fill_in_props()

    def fill_in_conds(self):
        # creating keys for conditions and populate values as "empty"
        for cond in self.conds_names:
            self.conds[cond] = 'empty'

    def fill_in_comps_and_fracs(self):
        # transferring information about components
        comp_keys = sorted(list(self.chosen_comps.keys()))
        for idx in range(len(comp_keys)):
            # adding a component to components_dict under the name "component X"
            comp_num = f"component {str(idx + 1)}"
            self.comps[comp_num] = self.chosen_comps[comp_keys[idx]]

            self.fracs[comp_num] = {}
            self.fracs[comp_num]["Molar Fraction"] = "empty"
            self.fracs[comp_num]["Mass Fraction"] = "empty"

            self.vap_phase_fracs[comp_num] = {}
            self.vap_phase_fracs[comp_num]["Molar Fraction"] = "empty"
            self.vap_phase_fracs[comp_num]["Mass Fraction"] = "empty"

            self.liq_phase_fracs[comp_num] = {}
            self.liq_phase_fracs[comp_num]["Molar Fraction"] = "empty"
            self.liq_phase_fracs[comp_num]["Mass Fraction"] = "empty"

    def fill_in_props(self):
        self.props_names = ["Stream Molar Weight [g/mol]",
                            "Mass Enthalpy [kJ/kg]",
                            "SRK Molar Volume [m3/mol]",
                            "Density [kg/m3]",
                            "Heat Capacity [J/mol-K]",
                            "Viscosity [Pa*s]",
                            "Thermal Conductivity [W/m-K]"]
        for prop in self.props_names:
            self.props[prop] = "empty"
            self.vap_phase_props[prop] = "empty"
            self.liq_phase_props[prop] = "empty"
