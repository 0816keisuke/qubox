import numpy as np
from qubox.base import Base

class TSP(Base):
    def __init__(self,
                distance_matrix,
                ALPHA=1
                ):
        # Check tye type of Arguments
        if isinstance(distance_matrix, list):
            distance_matrix = np.array(distance_matrix)
        elif isinstance(distance_matrix, np.ndarray):
            pass
        else:
            print("The type of the argument 'distance_matrix' is WRONG.")
            print("It shoud be list/numpy.ndarray.")
            exit()

        NUM_CITY = len(distance_matrix)
        self.distance_matrix = distance_matrix
        super().__init__(num_spin = NUM_CITY * NUM_CITY)
        self.spin_index = np.arange(NUM_CITY * NUM_CITY).reshape(NUM_CITY, NUM_CITY)
        np.set_printoptions(edgeitems=10) # Chenge the setting for printing numpy

        self.cost_term(NUM_CITY)
        self.penalty_term(NUM_CITY, ALPHA)
        self.all_term()

    def cost_term(self, NUM_CITY):
        # Quadratic term
        for t in range(NUM_CITY):
            for u in range(NUM_CITY):
                for v in range(NUM_CITY):
                    if t < NUM_CITY-1:
                        idx_i = self.spin_index[t, u]
                        idx_j = self.spin_index[t+1, v]
                    elif t == NUM_CITY-1:
                        idx_i = self.spin_index[t, u]
                        idx_j = self.spin_index[0, v]
                    coef  = self.distance_matrix[u, v]
                    if coef == 0:
                        continue
                    self.q_cost[idx_i, idx_j] += coef
        # Make QUBO upper triangular matrix
        self.q_cost = np.triu(self.q_cost + np.tril(self.q_cost, k=-1).T + np.triu(self.q_cost).T) - np.diag(self.q_cost.diagonal())

    def penalty_term(self, NUM_CITY, ALPHA):
        # Calculate constraint term1 (1-hot of horizontal line)
        # Quadratic term
        for t in range(NUM_CITY):
            for u in range(NUM_CITY-1):
                for v in range(u+1, NUM_CITY):
                    idx_i = self.spin_index[t, u]
                    idx_j = self.spin_index[t, v]
                    coef = 2
                    self.q_pen[idx_i, idx_j] += ALPHA * coef
        # Linear term
        for t in range(NUM_CITY):
            for u in range(NUM_CITY):
                idx = self.spin_index[t, u]
                coef = -1
                self.q_pen[idx, idx] += ALPHA * coef
        # Constant term
        self.const_pen[0] += ALPHA * NUM_CITY

        # Calculate constraint term2 (1-hot of vertical line)
        # Quadratic term
        for u in range(NUM_CITY):
            for t in range(NUM_CITY-1):
                for tt in range(t+1, NUM_CITY):
                    idx_i = self.spin_index[t, u]
                    idx_j = self.spin_index[tt, u]
                    coef = 2
                    self.q_pen[idx_i, idx_j] += ALPHA * coef
        # Linear term
        for u in range(NUM_CITY):
            for t in range(NUM_CITY):
                idx = self.spin_index[t, u]
                coef = -1
                self.q_pen[idx, idx] += ALPHA * coef
        # Constant term
        self.const_pen[0] += ALPHA * NUM_CITY
