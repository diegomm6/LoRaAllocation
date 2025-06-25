from src.base import *
import gurobipy as gp
from gurobipy import GRB
from src.mac.Scheduler import Scheduler

# optimization model class for 1 channel
class Opt1DModel(Scheduler):

    def __init__(self, numDevices, slottime, timeslots, numLRchannels, availableSF_data) -> None:
        no_lrfhss_availableSF_data = availableSF_data[:,:,:-2] # remove lrfhss
        super().__init__(numDevices, slottime, timeslots, numLRchannels, no_lrfhss_availableSF_data)


    def update_delta(self, scheduledEDs):

        for m in range(self.M - self.bestSF):
            for n in scheduledEDs:
                for p in range(self.W):
                    i = n + m*self.N
                    self.delta[i][p] = 0


    # solve the 1D model iteratively for as many channels are available
    def get_schedule(self):

        original_delta = self.delta.copy()

        schedules = []
        current_schedules = self.solve1Dmodel()
        for (i,p,q), _ in current_schedules.items():
            n = i % self.N
            m = i // self.N + self.bestSF
            schedules.append((n,m,p,q))

        q=1
        while q < self.LRchannels:
            
            current_scheduledEDs = [i % self.N  for (i,_,_), _ in current_schedules.items()]
            self.update_delta(current_scheduledEDs)

            new_schedules = self.solve1Dmodel()
            for (i,p,_), _ in new_schedules.items():
                n = i % self.N
                m = i // self.N + self.bestSF
                schedules.append((n,m,p,q))

            current_schedules = new_schedules
            q+=1

        self.delta = original_delta
        return schedules


    def solve1Dmodel(self):

        # no console log Gurobi environment
        env = gp.Env(empty=True)
        env.setParam("OutputFlag", 0)
        env.start()

        # Create a new model
        model = gp.Model("bin_packing", env=env)

        # Create variables
        I = range(self.N * (self.M - self.bestSF))
        P = range(self.W)
        N = range(self.N)
        M = range(self.M - self.bestSF)
        x = model.addVars(I, P, vtype=GRB.BINARY, name="x")


        # Set objective
        model.setObjective(
            gp.quicksum(x[i,p] for i in I for p in P),
            GRB.MAXIMIZE
        )

        # Add constraints
        # Constraint (i): Each item can be placed at most once
        for i in I:
            model.addConstr(
                gp.quicksum(x[i, p] for p in P) <= 1
            )

        # Constraint (ii): Each ED can transmit only once
        for n in N:
            model.addConstr(
                gp.quicksum(x[n + self.N*m, p] for p in P for m in M) <= 1
            )

        # Constraint (iii): At most M items can cover any point p
        for p in P:
            model.addConstr(
                gp.quicksum(x[i,a] for i,a,b in self.xi_p_q[p][0]) <= self.M
            )

        # Constraint (iv): At most one SF m at any point p
        for p in P:
            for m in M:
                model.addConstr(
                    gp.quicksum(x[i,a] for i,a,b in self.xi_p_q_m[p][0][m]) <= 1
                )

        # Constraint (vi): Items can only be placed at feasible positions
        for i in I:
            for p in P:
                model.addConstr(x[i,p] <= self.delta[i,p])

        # Optimize model
        model.optimize()

        # Get solution
        if model.status == GRB.OPTIMAL:
            solution = {(i,p,0): x[i,p].X for i in I for p in P if x[i,p].X > 0}
            objective_value = model.objVal
            return solution
