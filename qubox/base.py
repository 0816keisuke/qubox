from abc import ABCMeta, abstractmethod

import numpy as np


class Base(metaclass=ABCMeta):
    def __init__(self, modeltype, mtx="upper", num_spin=None):

        self.MODELTYPE = modeltype
        self.__check_model_name__()

        self.MTXTYPE = mtx
        self.__check_mtx_type__()

        self.num_spin = num_spin

        if self.MODELTYPE == "ISING":
            self.J = np.zeros((self.num_spin, self.num_spin))
            self.J_cost = np.zeros((self.num_spin, self.num_spin))
            self.J_pen = np.zeros((self.num_spin, self.num_spin))
            self.h = np.diag(self.J)
            self.h_cost = np.diag(self.J_cost)
            self.h_pen = np.diag(self.J_pen)

        elif self.MODELTYPE == "QUBO":
            self.Q = np.zeros((self.num_spin, self.num_spin))
            self.Q_cost = np.zeros((self.num_spin, self.num_spin))
            self.Q_pen = np.zeros((self.num_spin, self.num_spin))

        self.const = 0
        self.const_cost = 0
        self.const_pen = 0

    @abstractmethod
    def hamil_cost(self):
        pass

    @abstractmethod
    def hamil_pen(self):
        pass

    def hamil_all(self):
        if self.MODELTYPE == "ISING":
            self.J = self.J_cost + self.J_pen
        elif self.MODELTYPE == "QUBO":
            self.Q = self.Q_cost + self.Q_pen
        self.const = self.const_cost + self.const_pen

    # モデル名のチェック
    def __check_model_name__(self):
        if self.MODELTYPE not in ["ISING", "QUBO"]:
            error_msg = "Invalid model type. It should be 'ISING' or 'QUBO'."
            raise KeyError(error_msg)

    # 行列形式(上三角行列/対称行列)のチェック
    def __check_mtx_type__(self):
        if self.MTXTYPE not in ["upper", "sym"]:
            error_msg = "Invalid matrix type. It should be 'upper' or 'sym'."
            raise KeyError(error_msg)

    def __upper2sym__(self):
        if self.MODELTYPE == "ISING" and self.MTXTYPE == "sym":
            self.J_cost = (np.triu(self.J_cost) + np.triu(self.J_cost).T)/2
            self.J_pen = (np.triu(self.J_pen) + np.triu(self.J_pen).T)/2
        if self.MODELTYPE == "QUBO" and self.MTXTYPE == "sym":
            self.Q_cost = (np.triu(self.Q_cost) + np.triu(self.Q_cost).T)/2
            self.Q_pen = (np.triu(self.Q_pen) + np.triu(self.Q_pen).T)/2

    # モデルタイプ(ISING/QUBO)及びグループ(None(:=all)/cost/pen)によってどのQUBO行列を利用するかを決定
    def __select_mtx_group__(self, group=None):
        if self.MODELTYPE == "ISING":
            if group is None:
                mtx = self.J
            elif group == "cost":
                mtx = self.J_cost
            elif group == "pen":
                mtx = self.J_pen
        elif self.MODELTYPE == "QUBO":
            if group is None:
                mtx = self.Q
            elif group == "cost":
                mtx = self.Q_cost
            elif group == "pen":
                mtx = self.Q_pen
            else:
                erro_msg = "Invalid group. the group should be [None, cost, pen]."
                raise KeyError(erro_msg)
        return mtx

    # モデル(ISING/QUBO)及びグループ(None(:=all)/cost/pen)によってどの定数を利用するかを決定
    def __select_constant_group__(self, group=None):
        if self.MODELTYPE == "ISING":
            if group is None:
                const = self.const
            elif group == "cost":
                const = self.const_cost
            elif group == "pen":
                const = self.const_pen
        elif self.MODELTYPE == "QUBO":
            if group is None:
                const = self.const
            elif group == "cost":
                const = self.const_cost
            elif group == "pen":
                const = self.const_pen
            else:
                erro_msg = "Invalid group. the group should be [None, cost, pen]."
                raise KeyError(erro_msg)
        return const

    # Convert Ising/QUBO-model to list
    def to_list(self, group, union=True):
        mtx = self.__select_mtx_group__(group)

        Q = []
        for idx_i in range(self.num_spin):
            for idx_j in range(idx_i, self.num_spin):
                coef = mtx[idx_i, idx_j]
                if not coef == 0:
                    Q.append([idx_i, idx_j, coef])
        return Q

    # Convert Ising/QUBO-model to dict
    def to_dict(self, group=None, union=True):
        mtx = self.__select_mtx_group__(group)

        # Merge linear & quadratic term
        if union:
            quadratic = {}

            # Linear & quadratic term
            for idx_i in range(self.num_spin):
                for idx_j in range(idx_i, self.num_spin):
                    if group is None:
                        coef = mtx[idx_i, idx_j]
                    elif group == "cost":
                        coef = mtx[idx_i, idx_j]
                    elif group == "pen":
                        coef = mtx[idx_i, idx_j]
                    if coef != 0:
                        quadratic[idx_i, idx_j] = coef
            return quadratic

        # Separate linear & quadratic term
        if not union:
            linear = {}
            quadratic = {}

            # Linear term
            for idx_i in range(self.num_spin):
                if group is None:
                    linear[idx_i] = mtx[idx_i, idx_i]
                elif group == "cost":
                    linear[idx_i] = mtx[idx_i, idx_i]
                elif group == "pen":
                    linear[idx_i] = mtx[idx_i, idx_i]

                # Quadratic term
                for idx_j in range(idx_i + 1, self.num_spin):
                    if group is None:
                        coef = mtx[idx_i, idx_j]
                    elif group == "cost":
                        coef = mtx[idx_i, idx_j]
                    elif group == "pen":
                        coef = mtx[idx_i, idx_j]
                    if coef != 0:
                        quadratic[idx_i, idx_j] = coef
            return linear, quadratic

    # Convert Ising/QUBO-model to bqm
    def to_bqm(self, group=None):
        import dimod

        linear, quadratic = self.to_dict(group=group, union=False)
        const = self.__select_constant_group__(group)

        if self.MODELTYPE == "ISING":
            vartype = dimod.Vartype.SPIN
        if self.MODELTYPE == "QUBO":
            vartype = dimod.Vartype.BINARY

        bqm = dimod.BinaryQuadraticModel(linear, quadratic, const, vartype)

        return bqm

    # Calculate the hamiltonian's energy
    def energy(self, x, group=None):
        mtx = self.__select_mtx_group__(group)
        const = self.__select_constant_group__(group)

        if self.MODELTYPE == "ISING":
            energy = int(np.dot(np.dot(x, np.triu(mtx, k=1)), x)) + np.dot(x, np.diag(mtx) + const)
        elif self.MODELTYPE == "QUBO":
            energy = int(np.dot(np.dot(x, mtx), x) + const)

        return energy

    def show(self, group=None):
        import plotly.express as px

        mtx = self.__select_mtx_group__(group)
        fig = px.imshow(mtx)
        fig.show()

    def qubo_to_ising(self, qubo):
        size = qubo.shape[0]
        ising = np.zeros((size, size), dtype=float)

        for i in range(size):
            sum = 0.0
            for j in range(i + 1, size):
                ising[i][j] = 0.25 * qubo[i][j]
                sum += 0.25 * qubo[i][j]
            for k in range(i):
                sum += 0.25 * qubo[k][i]
            ising[i][i] = sum + 0.5 * qubo[i][i]

        return ising

    def ising_to_qubo(self, ising):
        size = ising.shape[0]
        qubo = np.zeros((size, size), dtype=int)

        for i in range(size):
            sum = 0.0
            for j in range(i + 1, size):
                qubo[i][j] = int(4 * ising[i][j])
                sum += ising[i][j]
            for k in range(i):
                sum += ising[k][i]
            qubo[i][i] = int(2 * ising[i][i] - 2 * sum)
        return qubo

    # def convert_qubo_to_ising(self):
    #     self.const_ising += 4 * self.const_qubo # Multiply by 4 to convert to integer, as appearance of fraction 1/4
    #     for i in range(self.num_spin):
    #         self.const_ising += 2 * self.bias_qubo[i]
    #         self.bias_ising[i] += 2 * self.bias_qubo[i]
    #         for j in range(i, self.num_spin):
    #             self.const_ising += self.weight_qubo[i][j]
    #             self.bias_ising[i] += self.weight_qubo[i][j]
    #             self.bias_ising[j] += self.weight_qubo[i][j]
    #             self.weight_ising[i][j] += self.weight_qubo[i][j]
    #             # 下三角を埋める
    #             self.weight_ising[j][i] = self.weight_ising[i][j]

    # def convert_ising_to_qubo(self):
    #     self.const_qubo += self.const_ising
    #     for i in range(self.num_spin):
    #         self.const_qubo += -1 * self.bias_ising[i]
    #         self.bias_qubo[i] += 2 * self.bias_ising[i]
    #         for j in range(i, self.num_spin):
    #             self.const_qubo += self.weight_ising[i][j]
    #             self.bias_qubo[i] += -2 * self.weight_ising[i][j]
    #             self.bias_qubo[j] += -2 * self.weight_ising[i][j]
    #             self.weight_qubo[i][j] += 4 * self.weight_ising[i][j]
    #             # 下三角を埋める
    #             self.weight_qubo[j][i] = self.weight_qubo[i][j]
