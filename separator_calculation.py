import numpy as np
from scipy.optimize import fsolve
import matplotlib.pyplot as plt
import sympy as sp
from shapely.geometry import LineString

def func(fi):
    res = (0.0621739693001397*fi**4 - 3.55962302204912*fi**3 + 10.3019872237631*fi**2 - 10.0674331583929*fi + 3.25955690670405)/(0.0621739693001398*fi**5 - 4.28463927352945*fi**4 + 13.2520430214225*fi**3 - 13.0080545997237*fi**2 + 2.97975291946284*fi + 1.0)
    return res

def func_F(K, z):
    fi = sp.symbols("fi")
    res = 0
    for j in range(len(z)):
        res += (K[j] - 1) * z[j] / (1 + (K[j] - 1) * fi)
    res = sp.simplify(res)
    # f_ex = np.linspace(0, 1, 200)
    # f0 = f_ex * 0
    # plt.plot(f_ex, func(f_ex), 'b-')
    # plt.plot(f_ex, f0, 'k-')
    # plt.show()
    res = sp.Eq(res, 0)
    solution = sp.solveset(res, fi)
    fi = np.array([value for value in solution if 0 < value < 1])
    #print(f"[fi] {fi}")
    return fi



def func_F1(cnt, fi, A, B, C, T, P, z):
    res = 0
    for i in range(cnt):
        res += (z[i]) / (1 + (np.exp(A[i] - (B[i] / (C[i] + T))) / P - 1) * fi)
    return res


def func_P0(cnt, A, B, C, T):
    res = []
    for i in range(cnt):
        res.append(np.exp(A[i] - (B[i] / (C[i] + T))))
    return np.array(res)


def func_K(cnt, P0, P):
    res = 0
    for i in range(cnt):
        res = P0 / P
    return res


class Separator:
    def __init__(self, T, P, z, antoine_coeffs, Flow):
        self.T = T
        self.P = P
        self.z = np.array(z)
        self.A, self.B, self.C = antoine_coeffs
        self.Flow = float(Flow)

        self.substances_cnt = len(self.A)

    def calc(self):
        self.P0 = func_P0(self.substances_cnt, self.A, self.B, self.C, self.T)
        # print(self.P0)
        self.K = func_K(self.substances_cnt, self.P0, self.P)
        # print(self.K)
        self.fi1, self.V, self.L, self.x, self.y = self.calc_fi(self.K, self.z)
        self.fi1 = self.fi1[0] * 100
        return self.fi1, self.V, self.L, self.x, self.y


    def calc_fi(self, K, z):
        fi1 = func_F(K, z)
        print('Доля отгона: ', fi1 * 100, '%')
        # x = []
        # for i in range(self.substances_cnt):
        #     x.append(z[i] / (1 + (K[i] - 1) * fi1))
        x = z / (1 + (K - 1) * fi1)
        sum_x = np.sum(x)
        print(f'Доля компонента в жидкой фазе: {x}')
        print('Проверка: ', sum_x)
        # y = []
        # for i in range(self.substances_cnt):
        #     y.append(x[i] * K[i])
        y = x * K
        sum_y = np.sum(y)
        print(f'Доля компонента в паровой фазе: {y}')
        print('Проверка: ', sum_y)
        V = self.Flow * fi1
        print('Расход паровой фазы: ', V, 'кг/сек')
        L = self.Flow * (1 - fi1)
        print('Расход жидкой фазы: ', L, 'кг/сек')
        return fi1, V, L, x, y


 # [T] = K; [P] = мм.рт.ст.; [Flow] = кг/сек; [fi] = доли
