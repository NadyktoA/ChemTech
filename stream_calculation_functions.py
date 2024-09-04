# bpt = boiling point temperature
# calc = calculator
# coeffs = coefficients
# frac = fraction
# h_cap = heat capacity
# idx = index
# ig = ideal gas
# mol = molar
# therm_cond = thermal conductivity
# vol = volume
# wt = weight
import traceback

import numpy as np
from scipy.optimize import fsolve
import matplotlib.pyplot as plt
from scipy.integrate import quad

from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtCore import Qt

# constants
R = 8.31446261815324  # [J/(mol*K)]


def calculate_total_frac(composition_is_defined, composition_table, stream, props_table):
    for frac_idx in range(1, 3):  # 1 - molar fraction, 2 - mass fraction (cf. composition table)
        total_frac = 0
        for row_idx in range(0, len(stream.comps)):  # last row should not be calculated (it is "Total")
            frac = (composition_table.item(row_idx, frac_idx).text())
            if frac != "empty":
                total_frac += float(frac)
        if 0.9999 <= total_frac <= 1.0001:
            composition_is_defined = True
            calc_stream_mol_wt(frac_idx, stream, props_table)

        total_frac = str(round(total_frac, 2))
        total_frac = QTableWidgetItem(total_frac)
        total_frac.setTextAlignment(Qt.AlignCenter)
        composition_table.setItem(composition_table.rowCount() - 1, frac_idx, total_frac)
    return composition_is_defined


def calc_stream_mol_wt(known_comp_frac, stream, props_table):
    #  known_comp_frac: 1 - molar fraction, 2 - mass fraction (cf. composition table)
    fracs = []
    mol_wts = []
    comps = stream.comps
    for idx in range(0, len(comps)):
        if known_comp_frac == 1:
            comp_frac = float(stream.fracs[f"component {idx + 1}"]["Molar Fraction"])
        else:
            comp_frac = float(stream.fracs[f"component {idx + 1}"]["Mass Fraction"])
        fracs.append(comp_frac)
        comp_mol_wt = comps[f"component {idx + 1}"].general_info.base_props.mol_wt
        mol_wts.append(comp_mol_wt)

        if known_comp_frac == 1:
            stream_mol_wt = sum([(mol_wts[i] * fracs[i]) for i in range(len(mol_wts))])
        else:
            mass_total = sum(fracs)  # component mass fraction equals the mass of component (cf. calculate mass fractions)
            amount_of_substance_total = sum([fracs[i] / mol_wts[i] for i in range(len(fracs))])

            stream_mol_wt = mass_total / amount_of_substance_total

        stream.props["Stream Molar Weight [g/mol]"] = stream_mol_wt

        stream_mol_wt = round(stream_mol_wt, 5)
        stream_mol_wt = QTableWidgetItem(str(stream_mol_wt))
        stream_mol_wt.setTextAlignment(Qt.AlignCenter)
        props_table.setItem(0, 1, stream_mol_wt)
        props_table.resizeColumnsToContents()


def calculate_unknown_frac(known_comp_frac_idx, composition_table, stream):
    # known_comp_frac_idx: 1 - molar fraction, 2 - mass fraction (cf. composition table)
    if known_comp_frac_idx == 1:
        unknown_comp_frac_idx = 2
    else:
        unknown_comp_frac_idx = 1

    #  I use numeric coordinates of cell here, because there is a standard library (or table) with constant location for each property
    # (I agree, it is not universal, but for now it is (p.s. writing a list search is not the easiest way to do it))
    for idx in range(len(stream.comps)):
        comp_frac = None
        stream_mol_wt = float(stream.props["Stream Molar Weight [g/mol]"])
        comp_mol_wt = float(stream.comps[f"component {idx + 1}"].general_info.base_props.mol_wt)
        match unknown_comp_frac_idx:
            case 1:
                comp_mass_frac = float(stream.fracs[f"component {idx + 1}"]["Mass Fraction"])
                # assuming that the mass of a substance is 1 g (or kg (doesn't matter, all units will be abbreviated)),
                # the amounts of the constituents are equal to molar fractions, so the calculations become simpler
                comp_frac = (comp_mass_frac / comp_mol_wt) / (1 / stream_mol_wt)
                stream.fracs[f"component {idx + 1}"]["Molar Fraction"] = comp_frac
            case 2:
                comp_mol_frac = float(stream.fracs[f"component {idx + 1}"]["Molar Fraction"])
                # assuming that the amount of a substance is 1 mole (or kmol (doesn't matter, all units will be abbreviated)),
                # the amounts of the constituents are equal to molar fractions, so the calculations become simpler
                comp_frac = comp_mol_frac * comp_mol_wt / stream_mol_wt
                stream.fracs[f"component {idx + 1}"]["Mass Fraction"] = comp_frac

        comp_frac = round(comp_frac, 5)
        comp_frac = QTableWidgetItem(str(comp_frac))
        comp_frac.setTextAlignment(Qt.AlignCenter)
        composition_table.setItem(idx, unknown_comp_frac_idx, comp_frac)


def calc_bpt(comps, p):
    bpt = []
    for comp_key in comps.keys():
        a = comps[comp_key].antoine_eq.antoine_eq_coeffs.a
        b = comps[comp_key].antoine_eq.antoine_eq_coeffs.b
        c = comps[comp_key].antoine_eq.antoine_eq_coeffs.c

        comp_bpt = ((a * c - b - np.log(p) * c) / (np.log(p) - a)) - 273.15
        bpt.append(comp_bpt)
    return bpt


def calc_IG_mol_vol(p, t):
    v = R * t / p
    return v


def calc_SRK_m_i(w):
    return 0.480 + 1.574 * w - 0.176 * (w ** 2)


def calc_SRK_alpha_i(t, t_c, m):
    return (1 + m * (1 - np.sqrt(t / t_c))) ** 2


def calc_SRK_a_i(t_c, p_c, a):
    return 0.42748 * (((R ** 2) * (t_c ** 2)) / p_c) * a


def calc_SRK_b_i(t_c, p_c):
    return 0.08664 * ((R * t_c) / p_c)


def calc_SRK_a_mix(mol_fracs, a_i):
    a_mix = 0
    for idx in range(len(a_i)):
        a_mix += mol_fracs[idx] * np.sqrt(a_i[idx])
    a_mix = a_mix ** 2
    return a_mix


def calc_SRK_b_mix(mol_fracs, b_i):
    b_mix = 0
    for idx in range(len(b_i)):
        b_mix += mol_fracs[idx] * b_i[idx]
    return b_mix


def calc_Zra_i(w):
    return 0.29056 - 0.08775 * w


def calc_c_i(p_c, t_c, z_ra):
    return -0.40768 * R * t_c * (0.29441 - z_ra) / p_c


def calc_SRK_mol_vol(p, t, p_c, t_c, mol_fracs, w, phase):
    m = np.array(calc_SRK_m_i(w))
    alpha = np.array(calc_SRK_alpha_i(t, t_c, m))
    a_i = np.array(calc_SRK_a_i(t_c, p_c, alpha))
    b_i = np.array(calc_SRK_b_i(t_c, p_c))

    a_mix = calc_SRK_a_mix(mol_fracs, a_i)
    b_mix = calc_SRK_b_mix(mol_fracs, b_i)

    z_ra_i = calc_Zra_i(w)
    c_i = calc_c_i(p_c, t_c, z_ra_i)
    c = sum(c_i * mol_fracs)
    # print(f"[c] {c}")

    coeffs = [p, -R * t, (a_mix - p * (b_mix ** 2) - R * t * b_mix), -a_mix * b_mix]
    roots = np.roots(coeffs)
    # print(f"[roots] {roots}")
    real_roots = [i.real for i in roots if abs(i.imag) < (10 ** (-10))]
    # print(f"[real roots] {real_roots}")

    match len(real_roots):
        case 1:
            if phase == "Vapour":
                SRK_mol_vol = max(real_roots)
                # print(f"[SRK v] {SRK_mol_vol}")
                return [SRK_mol_vol, a_mix, b_mix]
            elif phase == "Liquid":
                SRK_mol_vol = max(real_roots)
                SRK_mol_vol = SRK_mol_vol + c
                # print(f"[SRK v] {SRK_mol_vol}")
                return [SRK_mol_vol, a_mix, b_mix]
        case 2:
            if phase == "Vapour":
                SRK_mol_vol = max(real_roots)
                # print(f"[SRK v] {SRK_mol_vol}")
                return [SRK_mol_vol, a_mix, b_mix]
            elif phase == "Liquid":
                print("TWO ROOTS! mol_vol is max of two")
                SRK_mol_vol = min(real_roots)
                SRK_mol_vol = SRK_mol_vol + c
                # print(f"[SRK v] {SRK_mol_vol}")
                return [SRK_mol_vol, a_mix, b_mix]
        case 3:
            if phase == "Vapour":
                SRK_mol_vol = max(real_roots)
                # print(f"[SRK v] {SRK_mol_vol}")
                return [SRK_mol_vol, a_mix, b_mix]
            elif phase == "Liquid":
                # real_roots.pop(real_roots.index(max(real_roots)))
                # real_roots.pop(real_roots.index(min(real_roots)))
                # print(f"[real roots without max and min] {real_roots}")
                SRK_mol_vol = min(real_roots)
                SRK_mol_vol = SRK_mol_vol + c
                # print(f"[SRK v] {SRK_mol_vol}")
                return [SRK_mol_vol, a_mix, b_mix]


def calc_density(stream_mol_wt, mol_vol):
    stream_mol_wt = stream_mol_wt / 1000  # [g/mol] --> [kg/mol]

    density = stream_mol_wt / mol_vol
    return density


def calc_IG_gas_h_cap(comps, mol_fracs, t):
    try:
        h_caps = []
        for comp_key in comps.keys():
            a = comps[comp_key].h_cap.ig_gas_h_cap_empiric_coeffs.a
            b = comps[comp_key].h_cap.ig_gas_h_cap_empiric_coeffs.b
            c = comps[comp_key].h_cap.ig_gas_h_cap_empiric_coeffs.c
            d = comps[comp_key].h_cap.ig_gas_h_cap_empiric_coeffs.d
            e = comps[comp_key].h_cap.ig_gas_h_cap_empiric_coeffs.e
            comp_coeffs = [a, b, c, d, e]

            comp_h_cap = 0
            for idx in range(len(comp_coeffs)):
                comp_h_cap += comp_coeffs[idx] * (t ** idx)
            h_caps.append(comp_h_cap)

        h_caps = np.array(h_caps)
        # vol fracs = mol fracs (ideal gas) (followed the formula, although it was possible to simply multiply by mole fractions)
        vol_fracs = mol_fracs

        total_h_cap = sum(list(np.multiply(h_caps, vol_fracs)))
        return total_h_cap, h_caps
    except:
        traceback.print_exc()


def calc_gas_viscosity(t, stream_mol_wt, mol_fracs, mol_wts):
    # vol fracs = mol fracs (ideal gas)
    vol_fracs = mol_fracs
    viscosities = []
    for mol_wt in mol_wts:
        comp_viscosity = t * (6.6 - 2.25 * np.log10(mol_wt)) * (10 ** (-8))
        viscosities.append(comp_viscosity)

    total_viscosity = stream_mol_wt / sum([((vol_fracs[i] * mol_wts[i]) / viscosities[i]) for i in range(len(mol_wts))])
    return total_viscosity, viscosities


def calc_gas_therm_cond(h_caps, viscosities, mol_fracs, mol_wts):
    comps_mol_Cv = np.array([(Cp - R) for Cp in h_caps])
    adiabatic_parameters = [(h_caps[i] / comps_mol_Cv[i]) for i in range(len(h_caps))]
    B_coeffs = np.array([((9 * adiabatic_parameters[i] - 5) / 4) for i in range(len(adiabatic_parameters))])
    viscosities = np.array(viscosities)
    # [J/kg-K] = [J/mol-K] / [g/mol] * 1000 (g --> kg)
    comps_mass_Cv = comps_mol_Cv * 1000 / mol_wts
    therm_conds = B_coeffs * comps_mass_Cv * viscosities

    total_therm_cond = sum(therm_conds * mol_fracs)
    return total_therm_cond


def calc_heat_of_vaporization(bpt):
    return (36.63 + 19.13 * np.log10(bpt)) * bpt


def func_gas_h_cap_for_integrate(t, coeffs):
    res = 0
    for i in range(len(coeffs)):
        res += coeffs[i] * (t ** i)
    return res


def func_liq_h_cap_for_integrate(t, t_c, w):
    t_ri = t / t_c
    res = (1.45 + 0.45 * ((1 - t_ri) ** (-1)) + 0.25 * w * (
                17.11 + 25.2 * ((1 - t_ri) ** (1 / 3)) * (t_ri ** (-1)) + 1.742 * ((1 - t_ri) ** (-1)))) * R
    return res

def calc_gas_enthalpy(t, comps, h_f, mol_fracs, stream_mol_wt):
    comps_gas_h_caps = []
    for comp_key in comps.keys():
        a = comps[comp_key].h_cap.ig_gas_h_cap_empiric_coeffs.a
        b = comps[comp_key].h_cap.ig_gas_h_cap_empiric_coeffs.b
        c = comps[comp_key].h_cap.ig_gas_h_cap_empiric_coeffs.c
        d = comps[comp_key].h_cap.ig_gas_h_cap_empiric_coeffs.d
        e = comps[comp_key].h_cap.ig_gas_h_cap_empiric_coeffs.e
        comps_coeffs = np.array([a, b, c, d, e])

        comps_gas_h_caps.append(quad(func_gas_h_cap_for_integrate, 298.15, t, args=(comps_coeffs))[0])
    comps_gas_h_caps = np.array(comps_gas_h_caps)
    H = h_f + comps_gas_h_caps
    H = sum(H * mol_fracs) / stream_mol_wt
    return H


def calc_liquid_enthalpy(t, comps, h_f, mol_fracs, t_c, bpt, mol_wts, stream_mol_wt, w):

    bpt = np.array(bpt) + 273.15

    comps_gas_h_caps = []
    comps_liq_h_caps = []
    i = 0
    for comp_key in comps.keys():
        a = comps[comp_key].h_cap.ig_gas_h_cap_empiric_coeffs.a
        b = comps[comp_key].h_cap.ig_gas_h_cap_empiric_coeffs.b
        c = comps[comp_key].h_cap.ig_gas_h_cap_empiric_coeffs.c
        d = comps[comp_key].h_cap.ig_gas_h_cap_empiric_coeffs.d
        e = comps[comp_key].h_cap.ig_gas_h_cap_empiric_coeffs.e
        comps_coeffs = np.array([a, b, c, d, e])

        comps_gas_h_caps.append(quad(func_gas_h_cap_for_integrate, 298.15, bpt[i], args=(comps_coeffs))[0])
        gas_h_caps_for_liq = quad(func_gas_h_cap_for_integrate, bpt[i], t, args=(comps_coeffs))[0]
        liq_h_caps_for_liq = quad(func_liq_h_cap_for_integrate, bpt[i], t, args=(t_c[i], w[i]))[0]
        comps_liq_h_caps.append(gas_h_caps_for_liq + liq_h_caps_for_liq)
        i += 1
    comps_gas_h_caps = np.array(comps_gas_h_caps)
    comps_liq_h_caps = np.array(comps_liq_h_caps)
    # print(f"[comps_gas_h_caps] {comps_gas_h_caps}")
    # print(f"[comps_liq_h_caps] {comps_liq_h_caps}")
    h_vap = (-1) * calc_heat_of_vaporization(bpt)  # just like Hysys is negative
    # print(f"[h_vap] {h_vap}")

    H = h_f + comps_gas_h_caps + h_vap + comps_liq_h_caps
    H = sum(H * mol_fracs) / stream_mol_wt
    return H



def calc_density20_4(stream_mol_wt, p_c, t_c, mol_fracs, w, phase):
    density_water_4 = 1000  # [kg/m3]

    mol_vol = calc_SRK_mol_vol(101325, 293.15, p_c, t_c, mol_fracs, w, phase)
    density20 = calc_density(stream_mol_wt, mol_vol)

    density20_4 = density20 / density_water_4
    return density20_4


def calc_density15_15(density20_4):
    return density20_4 + (0.0035 / density20_4)


def calc_characterizing_factor(avg_bpt, density15_15):
    return 1.216 * ((np.abs(avg_bpt) ** (1 / 3))) / density15_15  # не учитываю знак средней молярной температуры, тк уходит в отрицательные числа


def calc_liquid_h_cap(t, t_c, w, mol_fracs, comps):
    try:
        t_c = np.array(t_c) + 273.15
        t_ri = t / t_c
        comps_h_caps = (1.45 + 0.45 * ((1 - t_ri) ** (-1)) + 0.25 * w * (17.11 + 25.2 * ((1 - t_ri) ** (1 / 3)) * (t_ri ** (-1)) + 1.742 * ((1 - t_ri) ** (-1)))) * R
        ig_h_cap, ig_h_caps = calc_IG_gas_h_cap(comps, mol_fracs, t)

        comps_h_caps = comps_h_caps + ig_h_caps
        # print(f"[comp_h_caps] {comps_h_caps}")
        total_h_cap = sum(mol_fracs * comps_h_caps)
        return total_h_cap
    except:
        traceback.print_exc()


def calc_liquid_viscosity(comps, mass_fracs, t):
    try:
        comps_viscosities = []
        for comp_key in comps.keys():
            a = comps[comp_key].viscosity.liquid_viscosity_coeffs.a
            b = comps[comp_key].viscosity.liquid_viscosity_coeffs.b
            c = comps[comp_key].viscosity.liquid_viscosity_coeffs.c
            d = comps[comp_key].viscosity.liquid_viscosity_coeffs.d
            comp_coeffs = [a, b, c, d]

            comp_viscosity = 10 ** (comp_coeffs[0] + (comp_coeffs[1] / t) + comp_coeffs[2] * t + comp_coeffs[3] * (t ** 2))
            comps_viscosities.append(comp_viscosity)
        comps_viscosities = np.array(comps_viscosities)  # [cP = mPa*s]
        # print(f"[comps_viscosities] {comps_viscosities}")

        total_viscosity = ((sum(mass_fracs * (comps_viscosities ** (1 / 3)))) ** 3)/1000
        # print(f"[total_viscosity] {total_viscosity}")
        return total_viscosity
    except:
        traceback.print_exc()

def calc_liquid_therm_cond(mol_wt, t, bpt, t_c, mass_fracs):
    try:
        bpt, t_c = np.array(bpt) + 273.15, np.array(t_c) + 273.15
        t_ri = t / t_c
        t_bri = bpt / t_c
        comps_therm_conds = (1.1053152 / (mol_wt ** 0.5)) * ((3 + 20 * ((1 - t_ri) ** (2 / 3))) / (3 + 20 * ((1 - t_bri) ** (2 / 3))))
        # print(f"[comps_therm_conds] {comps_therm_conds}")
        therm_cond = sum(comps_therm_conds * mass_fracs)
        return therm_cond
    except:
        traceback.print_exc()


# def calc_liquid_viscosity20(t, p, normal_bpt, density20_4, mol_wts):
#     t20_k = (normal_bpt + 273) / 293.15
#     # for alkanes
#     f, a0, a1, a2, a3, a4 = 0.21, 1.43, -1.61, 1.55, 1, 0
#
#     viscosity20 = f * (t20_k ** (a0 + (a1 / t20_k) + (a2 * t20_k) + (a3 * density20_4) + (a4 * (density20_4 ** 2))))
#     print(viscosity20)
#
#     t20 = (t + 273) / 293.15
#     pi = p / 101325
#     # for alkanes
#     alpha0, alpha1, alpha2, alpha3, beta0, beta1 = -2.2, -0.6, 0.3, 0, -0.026, 0.0005
#
#     viscosity20_tp = viscosity20 * (t20 ** (alpha0 + (alpha1 * t20) + (alpha2 * density20_4))) * (pi ** (beta0 + (beta1 * pi)))
#     print(viscosity20_tp)
#
#     t_t = (1.02 * (10 ** (-6)) * (mol_wts ** 1.87)) + (5.48 * (10 ** (-3)))
#     t_p = (4.24 * (10 ** (-5)) * mol_wts) + (6.82 * (10 ** (-3)))
#
#     viscosity20_tp2 = viscosity20 * ((np.exp(t_p * ((p / (10 ** 6)) - 0.101))) / (np.exp(t_t * (t - 20))))
#     print(viscosity20_tp2)
#     return viscosity20_tp


