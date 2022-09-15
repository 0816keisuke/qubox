import numpy as np
from qubox.base import Base

class QAP(Base):
    def __init__(self,
                weight_mtx,
                dist_mtx,
                ALPHA=1
                ):
        # Check tye type of Arguments
        if isinstance(weight_mtx, list):
            weight_mtx = np.array(weight_mtx)
        elif isinstance(weight_mtx, np.ndarray):
            pass
        else:
            print("The type of the argument 'weight_mtx' is WRONG.")
            print("It shoud be list/numpy.ndarray.")
            exit()
        if isinstance(dist_mtx, list):
            dist_mtx = np.array(dist_mtx)
        elif isinstance(dist_mtx, np.ndarray):
            pass
        else:
            print("The type of the argument 'dist_mtx' is WRONG.")
            print("It shoud be list/numpy.ndarray.")
            exit()

        NUM_FACTORY = len(weight_mtx)
        self.weight_mtx = weight_mtx
        self.dist_mtx = dist_mtx
        super().__init__(num_spin = NUM_FACTORY * NUM_FACTORY)
        self.spin_index = np.arange(NUM_FACTORY * NUM_FACTORY).reshape(NUM_FACTORY, NUM_FACTORY)
        np.set_printoptions(edgeitems=10) # Chenge the setting for printing numpy

        self.h_cost(NUM_FACTORY)
        self.h_pen(NUM_FACTORY, ALPHA)
        self.h_all()

    def h_cost(self, NUM_FACTORY):
        # Quadratic term
        for i in range(NUM_FACTORY):
            for j in range(NUM_FACTORY):
                for k in range(NUM_FACTORY):
                    for l in range(NUM_FACTORY):
                        idx_i = self.spin_index[i, k]
                        idx_j = self.spin_index[j, l]
                        coef = self.weight_mtx[i, j] * self.dist_mtx[k, l]
                        if coef == 0:
                            continue
                        self.q_cost[idx_i, idx_j] += coef
        self.q_cost = np.triu(self.q_cost + np.tril(self.q_cost, k=-1).T + np.triu(self.q_cost).T) - np.diag(self.q_cost.diagonal())

    def h_pen(self, NUM_FACTORY, ALPHA):
        # Constraint term1 (1-hot of horizontal line)
        # Quadratic term
        for i in range(NUM_FACTORY):
            for k in range(NUM_FACTORY-1):
                for l in range(k+1, NUM_FACTORY):
                    idx_i = self.spin_index[i, k]
                    idx_j = self.spin_index[i, l]
                    coef = 2
                    self.q_pen[idx_i, idx_j] += ALPHA * coef
        # Linear term
        for i in range(NUM_FACTORY):
            for k in range(NUM_FACTORY):
                idx = self.spin_index[i, k]
                coef = -1
                self.q_pen[idx, idx] += ALPHA * coef
        # Constant term
        self.const_pen[0] += ALPHA * NUM_FACTORY

        # Constraint term2 (1-hot of vertical line)
        # Quadratic term
        for k in range(NUM_FACTORY):
            for i in range(NUM_FACTORY-1):
                for j in range(i+1, NUM_FACTORY):
                    idx_i = self.spin_index[i, k]
                    idx_j = self.spin_index[j, k]
                    coef = 2
                    self.q_pen[idx_i, idx_j] += ALPHA * coef
        # Linear term
        for k in range(NUM_FACTORY):
            for i in range(NUM_FACTORY):
                idx = self.spin_index[i, k]
                coef = -1
                self.q_pen[idx, idx] += ALPHA * coef
        # Constant term
        self.const_pen[0] += ALPHA * NUM_FACTORY
