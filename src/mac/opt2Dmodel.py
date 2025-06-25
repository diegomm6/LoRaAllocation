from src.base import *
import gurobipy as gp
from gurobipy import GRB
from src.mac.Scheduler import Scheduler

# optimization model class for multiple channels
class Opt2DModel(Scheduler):

    def __init__(self, numDevices, slottime, timeslots, numLRchannels, availableSF_data) -> None:
        no_lrfhss_availableSF_data = availableSF_data[:,:,:-2] # remove lrfhss
        super().__init__(numDevices, slottime, timeslots, numLRchannels, no_lrfhss_availableSF_data)


    # solve the 2D model for all channels simultaneously
    def get_schedule(self):

        solution = self.solve2Dmodel()
        schedules = []
        for (i,p,q), _ in solution.items():
            n = i % self.N
            m = i // self.N + self.bestSF
            schedules.append((n,m,p,q))
            
        return schedules


    def solve2Dmodel(self):

        # no console log Gurobi environment
        env = gp.Env(empty=True)
        env.setParam("OutputFlag", 0)
        env.start()

        # Create a new model
        model = gp.Model("bin_packing_2d", env=env)

        # Create variables
        I = range(self.N * (self.M - self.bestSF))
        P = range(self.W)
        Q = range(self.LRchannels)
        N = range(self.N)
        M = range(self.M - self.bestSF)
        x = model.addVars(I, P, Q, vtype=GRB.BINARY, name="x")


        # Set objective
        model.setObjective(
            gp.quicksum(x[i,p,q] for i in I for p in P for q in Q),
            GRB.MAXIMIZE
        )

        # Add constraints
        # Constraint (i): Each item can be placed at most once
        for i in I:
            model.addConstr(
                gp.quicksum(x[i,p,q] for p in P for q in Q) <= 1
            )

        # Constraint (ii): Each ED can transmit only once
        for n in N:
            model.addConstr(
                gp.quicksum(x[n + self.N*m, p,q] for p in P for q in Q for m in M) <= 1
            )

        # Constraint (iii): At most M items can cover any point p
        for p in P:
            for q in Q:
                model.addConstr(
                    gp.quicksum(x[i,a,b] for i,a,b in self.xi_p_q[p][q]) <= self.M
                )

        # Constraint (iv): At most one SF m at any point p
        for p in P:
            for q in Q:
                for m in M:
                    model.addConstr(
                        gp.quicksum(x[i,a,b] for i,a,b in self.xi_p_q_m[p][q][m]) <= 1
                    )

        # Constraint (iv): At most one SF m at any point p


        # Constraint (vi): Items can only be placed at feasible positions
        for i in I:
            for p in P:
                for q in Q:
                    model.addConstr(x[i,p,q] <= self.delta[i,p])

        # Optimize model
        model.optimize()

        # Get solution
        if model.status == GRB.OPTIMAL:
            solution = {(i,p,q): x[i,p,q].X for i in I for p in P for q in Q if x[i,p,q].X > 0}
            objective_value = model.objVal

            return solution
