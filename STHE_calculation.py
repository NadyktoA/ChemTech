import numpy as np
import matplotlib.pyplot as plt
import scipy.integrate as spi
import math

class Heat_exchanger():
    def __init__(self, h_temp1=None, h_temp2=None, h_flow=None, c_temp1=None, c_temp2=None, c_flow=None,h_cp=None,c_cp=None):

        '''stream parameters'''
        # self.h_temp1 = h_temp1  # FROM STREAM DATA
        # self.h_temp2 = h_temp2  # FROM STREAM DATA
        # self.c_temp1 = c_temp1  # FROM STREAM DATA
        # self.c_temp2 = c_temp2  # FROM STREAM DATA
        # self.h_flow = h_flow  # FROM STREAM DATA
        # self.c_flow = c_flow  # FROM STREAM DATA
        # self.q_loss = 0.98
        # self.c_p1 = 250  # kPa
        # self.c_p2 = 150  # kPa
        # self.d_out = 0.02  # float(input('Enter outside tube diameter (m) --> '))
        # self.d_in = 0.016  # float(input('Enter inside tube diameter (m) --> '))
        # self.Pt = 0.032  # 0.032#float(input('Enter tube pitch (m) --> '))
        # self.tlc = 'tr'  # input('Choose pitch-tube layout: square(sqr) or triangular(tr) --> ')
        # self.n_t_pass = 2  # int(input('Enter the number of tube passes: 1,2 or 3 --> '))
        #self.missing_param()

    '''heat load'''
    def heat_load(self, h_T1, h_T2, tube_side_flow,h_cp ,c_T1, c_T2,shell_side_flow, c_cp):
        prm = [h_T1, h_T2,tube_side_flow, c_T1, c_T2,shell_side_flow]
        if prm[0] and prm[1] and prm[2] is not None:
            Q = tube_side_flow * h_cp * (h_T1 - h_T2)
            return Q
        elif prm[3] and prm[4] and prm[5] is not None:
            Q = shell_side_flow * c_cp * (c_T2 - c_T1)
            return Q
        else:
            print('Add missing parameter(s)')
            return

    '''missing parameter'''
    def missing_param(self):
        prm = [self.h_temp1, self.h_temp2, self.h_flow, self.c_temp1, self.c_temp2, self.c_flow]  # убрать self!!!!
        if prm.count(None) == 0:
            return
        if prm.count(None) > 1:
            print('Add missing parameter(s)')
            return
        else:
            missing_param_index = prm.index(None)
            match prm.index(None):
                # inlet hot temp
                case 0:
                    self.h_temp1 = self.c_flow * c_cp * (self.c_temp2 - self.c_temp1) / (
                            self.h_flow * h_cp) + self.h_temp2
                # outlet hot temp
                case 1:
                    self.h_temp2 = self.h_temp1 - self.c_flow * c_cp * (self.c_temp2 - self.c_temp1) / (
                            self.h_flow * h_cp)
                # hot stream flow
                case 2:
                    self.h_flow = self.c_flow * c_cp * (self.c_temp2 - self.c_temp1) / (
                            h_cp * (self.h_temp1 - self.h_temp2))
                # inlet cold temp
                case 3:
                    self.c_temp1 = self.c_temp2 - self.h_flow * h_cp * (self.h_temp1 - self.h_temp2) / (
                            self.c_flow * c_cp)
                # outlet cold temp
                case 4:
                    self.c_temp2 = self.c_temp1 + self.h_flow * h_cp * (self.h_temp1 - self.h_temp2) / (
                            self.c_flow * c_cp)
                # cold stream flow
                case 5:
                    self.c_flow = self.h_flow * h_cp * (self.h_temp1 - self.h_temp2) / (
                            c_cp * (self.c_temp2 - self.c_temp1))

    '''log-mean temperature difference (LMTD)'''
    def LMTD(self, h_T1,h_T2,c_T1,c_T2, pass_num,flow_dir):
        match pass_num:
            case 1:
                if flow_dir == 'Parallel':
                    T_diff_b = h_T1 - c_T1
                    T_diff_s = h_T2 - c_T2
                    return (T_diff_b - T_diff_s) / (np.log(T_diff_b / T_diff_s))
                if flow_dir == 'Counter':
                    T_diff_b = h_T1 - c_T2
                    T_diff_s = h_T2 - c_T1
                    return (T_diff_b - T_diff_s) / (np.log(T_diff_b / T_diff_s))
            case 2:
                T_diff_b = h_T1 - c_T2
                T_diff_s = h_T2 - c_T1
                LMTD_counter = (T_diff_b - T_diff_s) / (np.log(T_diff_b / T_diff_s))
                R = (h_T1 - h_T2)/(c_T2 - c_T1)
                P = (c_T2 - c_T1)/(h_T1 - c_T1)
                delta = (R-1)/np.log((1-P)/(1-R*P))
                eta = np.sqrt((R**2)+1)
                corr_factor = eta/delta / np.log( (2-P*(1+R-eta))/(2-P*(1+R+eta)) )
                return LMTD_counter*corr_factor
            case 3:
                T_diff_b = h_T1 - c_T2
                T_diff_s = h_T2 - c_T1
                return (T_diff_b - T_diff_s) / (np.log(T_diff_b / T_diff_s))
        #return T_diff

    '''number of tubes per one tube pass'''
    def n_tube(self,tube_side_flow, inside_tube_diameter, h_visc):
        Re_start = 15000  # rough Re value
        n = 4 * (tube_side_flow) / (np.pi * inside_tube_diameter * Re_start * h_visc)
        return math.ceil(n)

    '''total number of tubes'''
    def n_tube_total(self,n_per_one_pass,pass_num):
        n = n_per_one_pass * pass_num
        return math.ceil(n)

        '''length of tubes'''
    def l_tube(self,F,n_tube_total,outside_tube_diameter):
        l = F / (n_tube_total * np.pi * outside_tube_diameter)
        return l

    '''tube count calculation constant'''
    def CTP(self,pass_num):
        match pass_num:
            case 1:
                return 0.93
            case 2:
                return 0.9
            case 3:
                return 0.85

    '''pitch-tube layout constant'''
    def CL(self,layout_type):
        match layout_type:
            case 'Square 90°':
                return 1
            case 'Triangular 30°':
                return 0.87

    '''tube pitch ratio'''
    def PR(self,pitch,outside_tube_diameter):
        ratio = pitch / outside_tube_diameter
        return ratio

    '''inside shell diameter'''
    def Ds(self,outside_tube_diameter,CL,PR,CTP,n_tube_total):
        D = 0.637 * np.sqrt(CL * ((PR * outside_tube_diameter) ** 2) * np.pi * n_tube_total / CTP)
        return D

    '''shell equivalent diameter'''
    # def De(self,pitch,layout_type,outside_tube_diameter):
    def De(self,inside_shell_diameter,total_tube_number, outside_tube_diameter):
        De = ((inside_shell_diameter**2) - total_tube_number*(outside_tube_diameter**2))/(inside_shell_diameter+total_tube_number*outside_tube_diameter)
        return De
        # match layout_type:
        #     case 'Square 90°':
        #         return 4 * ((pitch ** 2) - np.pi * (outside_tube_diameter ** 2) / 4) / (np.pi * outside_tube_diameter)
        #     case 'Triangular 30°':
        #         return 4 / (np.pi * outside_tube_diameter / 2) * (pitch ** 2 * (3 ** (1 / 3)) / 4 - (np.pi * outside_tube_diameter ** 2) / 8)

    '''bundle cross flow area'''
    def As(self,baffle_presence,cut, inside_shell_diameter,total_tube_number,outside_tube_diameter):
        match baffle_presence:
            case 'No baffle':
                As = np.pi / 4 * ((inside_shell_diameter ** 2) - total_tube_number * (outside_tube_diameter ** 2))
                De = ((inside_shell_diameter**2) - total_tube_number*(outside_tube_diameter**2))/(inside_shell_diameter+total_tube_number*outside_tube_diameter)
                return [As, De]
            case 'Segmental':
                r = inside_shell_diameter/2
                cut_height = cut/100*inside_shell_diameter
                h = r - cut_height
                angle = 2*np.arccos(h / r)
                window_area = np.degrees(angle) / 360 * np.pi * (r ** 2) - 0.5 * (r ** 2) * np.sin(angle)
                shell_area = np.pi * (inside_shell_diameter ** 2) / 4
                n_window_tubes = math.floor(window_area / shell_area * total_tube_number)
                As = window_area-n_window_tubes*np.pi*(outside_tube_diameter**2)/4

                chord = 2*h*np.tan(angle/2)
                arc = np.pi*r/180 * np.degrees(angle)
                wetted_perimeter = arc + chord + n_window_tubes*np.pi*outside_tube_diameter
                De = 4*As/wetted_perimeter
                return [As, De]

    def As_test(self, inside_shell_diameter, tube_pitch,outside_tube_diameter):
        clearance = tube_pitch - outside_tube_diameter
        B = inside_shell_diameter/2
        As = inside_shell_diameter*clearance*B/tube_pitch
        return As
    '''tube-side Re'''
    def Re_tube_side(self,h_flow, tubes_per_pass, inside_tube_diameter,h_visc):
        Re = 4 * h_flow / (tubes_per_pass * np.pi * inside_tube_diameter * h_visc)
        return Re

    '''tube-side Pr'''
    def Pr_tube_side(self, h_cp, h_visc, h_t_cond):
        Pr = h_cp * h_visc / h_t_cond
        return Pr

    '''tube-side heat transfer coefficient'''
    def alpha_t(self,Re, Pr, h_t_cond, inside_tube_diameter):
        if Re > 10000:
            f = (1.58 * np.log(Re) - 3.28) ** (-2)  # Petukhov-Kirillov, Kern-method
            Nu = (f / 2) * Re * Pr / (1.07 + 12.7 * np.sqrt(f / 2) * (Pr ** (2 / 3)) - 1)
        else:
            print('Required equation for laminar flow (tube-side)',Re)
        # ДОБАВИТЬ УРАВНЕНИЯ
        a = Nu * h_t_cond / inside_tube_diameter
        return a

    '''Re_shell_side'''
    def Re_shell_side(self, c_flow, De, As, c_visc):
        Re = c_flow * De / As / c_visc
        return Re

    '''shell-side Pr'''
    def Pr_shell_side(self, c_cp, c_visc, c_t_cond):
        Pr = c_cp * c_visc / c_t_cond
        return Pr

    '''shell-side heat transfer coefficient'''
    def alpha_s(self,Re, Pr, c_t_cond, De):
        # if Re > 10000:
        #     a = 0.36 * c_t_cond * (Re ** (0.55)) * (Pr ** (1 / 3)) / De  # Kern-method
        # else:
        #     print('Required equation for laminar flow (shell-side)')
        # Дытнерский
        if Re>= 1000:
            Nu = 0.24*Re**(0.6)*Pr**(0.36) # учесть Pr стенки!!!!
        else:
            Nu = 0.34*Re**(0.5)*Pr**(0.36)
        a = Nu * c_t_cond / De
        return a

    '''overall heat transfer coefficient'''
    def overall_U(self, a_s, a_t, tube_wall_thickness, tube_t_cond):
        K = 1 / (1 / a_s + 1 / a_t + tube_wall_thickness / tube_t_cond)
        return K

    '''heat exchange surface area'''
    def he_surf(self, Q, U, LMTD):
        F = Q / U / LMTD
        return F

    '''number of baffles'''
    def baffle_number(self,tube_length, baffle_spacing):
        n = tube_length / baffle_spacing - 1
        return n

    '''tube-side fluid velocity'''
    def w_tube(self, inside_tube_diameter,h_flow, h_den, tubes_per_pass):
        tube_s = (np.pi * inside_tube_diameter ** 2) / 4
        w = h_flow / (h_den * tubes_per_pass * tube_s)
        return w

    '''tube-side kinetic energy'''
    def tube_kinetic_energy(self, h_den, w):
        E = (h_den * w**2)/2
        return E

    '''tube-side pressure drop'''
    def tube_pressure_drop(self,Re,tube_length,pass_num,d_in,E):
        # Kern method
        f = (1.58*np.log(Re)-3.28)**(-2)
        dp = (4*f*tube_length*pass_num/d_in + 4*pass_num)*E
        return dp

    def tube_pressure_drop_test(self,Re,tube_length,pass_num,d_in,E):
        k = 0.2/1000 # высота выступов шероховатостей, мм
        e = k/d_in
        lambd = 0.25*(np.log10( e/3.7 + (6.81/Re)**0.9 ))**(-2)
        dp = (lambd*tube_length*pass_num/d_in + 3 + 2.5*(pass_num-1) +2) * E
        return dp

    '''shell-side fluid velocity'''
    def w_shell(self, c_flow,c_den,As):
        w = c_flow / (c_den * As)
        return w

    '''shell-side pressure drop'''
    def pressure_drop_shell_numerator(self,Re,Ds,baffle_number,den,w):
        f = np.exp(0.576 - 0.19 * np.log(Re))
        numerator = f * Ds * (baffle_number+1) * den * (w**2)/2
        return numerator

    def pressure_drop_shell(self, numerator,De):
         dp = numerator / De
         return dp

    def tube_rows(self,layout_type, total_tube_number,inside_shell_diameter, tube_pitch ):
        match layout_type:
            case 'Square 90°':
                return round(inside_shell_diameter/tube_pitch)
            case 'Triangular 30°':
                return round(np.sqrt(total_tube_number / 3))
    def pressure_drop_shell_test(self,tube_rows, baffle_number,Re_shell, den,w):
        dp = 3*tube_rows*(baffle_number+1)/(Re_shell**0.2) * den * (w**2)/2 + 1.5*baffle_number*den*(w**2)/2 + 3*baffle_number*den*(w**2)/2
        return dp



