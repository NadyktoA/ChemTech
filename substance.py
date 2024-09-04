# bpt = boiling point temperature
# coeff = coefficient
# eq = equation
# h_cap = heat capacity
# info = information
# ig = ideal gas
# mol = molar
# P = pressure
# props = properties
# T = temperature
# vol = volume
# wt = weight


class Substance:
    def __init__(self):
        self.general_info = PropsClass()
        self.enthalpy = PropsClass()
        self.h_cap = PropsClass()
        self.antoine_eq = PropsClass()
        self.viscosity = PropsClass()

    def get_props(self, props_class, props_group, props):
        match props_class:
            case "General Information":
                self.general_info.get_props(props_class, props_group, props)
            case "Enthalpy":
                self.enthalpy.get_props(props_class, props_group, props)
            case "Heat Capacity":
                self.h_cap.get_props(props_class, props_group, props)
            case "Antoine Equation":
                self.antoine_eq.get_props(props_class, props_group, props)
            case "Viscosity":
                self.viscosity.get_props(props_class, props_group, props)


class PropsClass:
    def get_props(self, props_class, props_group, props):
        match props_class:
            case "General Information":
                match props_group:
                    case "Classification":
                        self.classification = PropsGroup()
                        self.classification.get_props(props_class, props_group, props)
                    case "Base Properties":
                        self.base_props = PropsGroup()
                        self.base_props.get_props(props_class, props_group, props)
                    case "Critical Properties":
                        self.critical_props = PropsGroup()
                        self.critical_props.get_props(props_class, props_group, props)
            case "Enthalpy":
                match props_group:
                    case "Mass Vapour Enthalpy (Ideal Gas) [kJ/kg]":
                        self.mass_vapor_enthalpy_ig = PropsGroup()
                        self.mass_vapor_enthalpy_ig.get_props(props_class, props_group, props)
                    case "Heat of formation [J/mol]":
                        self.heat_of_formation = PropsGroup()
                        self.heat_of_formation.get_props(props_class, props_group, props)
            case "Heat Capacity":
                match props_group:
                    case "Gas Heat Capacity Empiric Coefficients (Ideal Gas) [kJ/kmole-C]":
                        self.ig_gas_h_cap_empiric_coeffs = PropsGroup()
                        self.ig_gas_h_cap_empiric_coeffs.get_props(props_class, props_group, props)
            case "Antoine Equation":
                match props_group:
                    case "Antoine Vapour Pressure Coefficients [mmHg]":
                        self.antoine_eq_coeffs = PropsGroup()
                        self.antoine_eq_coeffs.get_props(props_class, props_group, props)
            case "Viscosity":
                match props_group:
                    case "Liquid Viscosity Empiric Coefficients [cP]":
                        self.liquid_viscosity_coeffs = PropsGroup()
                        self.liquid_viscosity_coeffs.get_props(props_class, props_group, props)

    def output_props_groups(self):
        return self.__dict__


class PropsGroup:
    def get_props(self, props_class, props_group, props):
        match props_class:
            case "General Information":
                match props_group:
                    case "Classification":
                        self.substance_class, self.id, self.name, self.chemical_formula = props
                    case "Base Properties":
                        self.mol_wt, self.normal_bpt, self.ideal_liquid_density = props
                    case "Critical Properties":
                        self.critical_T, self.critical_P, self.critical_vol, self.acentricity = props
            case "Enthalpy":
                match props_group:
                    case "Mass Vapour Enthalpy (Ideal Gas) [kJ/kg]":
                        self.a, self.b, self.c, self.d, self.e, self.f = props
                    case "Heat of formation [J/mol]":
                        self.heat_of_formation_value = props
            case "Heat Capacity":
                match props_group:
                    case "Gas Heat Capacity Empiric Coefficients (Ideal Gas) [kJ/kmole-C]":
                        self.a, self.b, self.c, self.d, self.e = props
            case "Antoine Equation":
                match props_group:
                    case "Antoine Vapour Pressure Coefficients [mmHg]":
                        self.a, self.b, self.c, self.t_max, self.t_min = props
            case "Viscosity":
                match props_group:
                    case "Liquid Viscosity Empiric Coefficients [cP]":
                        self.a, self.b, self.c, self.d, self.t_min, self.t_max = props

    def output_props(self):
        return self.__dict__
