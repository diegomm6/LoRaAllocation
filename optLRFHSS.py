from base import *
import gurobipy as gp
from gurobipy import GRB
from Scheduler import Scheduler

# optimization model class for 1 channel
class OptLRFHSS(Scheduler):

    def __init__(self, numDevices, slottime, timeslots, numFHSSchannles, availableSF_data) -> None:

        self.N = numDevices                 # number of EDs
        self.M = 6                          # number of LoRa SFs
        self.C = 2                          # number of LR-FHSS CRs
        self.W = timeslots                  # number of time slots
        self.slottime = slottime            # seconds per time slot 
        self.numOBW = 280                   # number of LR-FHSS OBW channels
        self.FHSSchannels = numFHSSchannles # number of LR-FHSS OCW channels

        self.T_c = get_timeslots_perCR(slottime)
        self.availableSF_per_node = availableSF_data

        self.delta = self.get_delta()
        self.xi_p_q = np.zeros((self.W, self.FHSSchannels), dtype=object)

        for p in range(self.W):
            for q in range(self.FHSSchannels):
                self.xi_p_q[p][q] = self.get_xi(p,q)


    # delta = 1 if CR c is available for ED n at time t
    # The packet is available if CR c is supported 
    # for all t' in [t, t+w(m)] and if t+w(m) < t_end
    def get_delta_perED(self, n, c, t):

        can_finish = t + self.T_c[c] <= self.W
        if not can_finish: return False
        
        packet_slots = self.availableSF_per_node[n, t : t + self.T_c[c], c + 6]

        return np.all(packet_slots == 1) 


    def get_delta(self):

        delta = np.zeros((self.C * self.N, self.W))

        for c in range(self.C):
            for n in range(self.N):
                for p in range(self.W):

                    i = n + c*self.N
                    delta[i][p] = self.get_delta_perED(n, c, p)

        return delta
    
    # return a list of tuples (i,a,b) where i is an item and (a,b)
    # is a position, such that if i is placed in (a,b) it covers
    # the point (p,q) while finishing before the frame ends
    def get_combinations_at_timeslost(self, a, p, q):

        perslot_combinations = []
        for c in range(self.C):

            if (a + self.T_c[c] <= self.W) and (p < a + self.T_c[c]):
                perslot_combinations += [(n + c*self.N, a, q) for n in range(self.N)]
        
        return perslot_combinations


    # set of all possible (i,a,b) such that 
    # if i is placed in (a,b) it covers point (p,q)
    def get_xi(self, p, q):

        total_combinations = []
        t_prime = p
        while t_prime >= 0 and t_prime >  (p - self.T_c[-1]):

            total_combinations += self.get_combinations_at_timeslost(t_prime, p, q)
            t_prime -= 1

        return total_combinations
    

    def update_delta(self, scheduledEDs):

        for c in range(self.C):
            for n in scheduledEDs:
                for p in range(self.W):
                    i = n + c*self.N
                    self.delta[i][p] = 0


    # solve the 1D model iteratively for as many channels are available
    def get_schedule(self):

        original_delta = self.delta.copy()

        schedules = []
        current_schedules = self.solve1Dmodel()
        for (i,p,q), _ in current_schedules.items():
            schedules.append((i,p,q))

        q=1
        while q < self.FHSSchannels:
            
            current_scheduledEDs = [i % self.N  for (i,_,_), _ in current_schedules.items()]
            self.update_delta(current_scheduledEDs)

            new_schedules = self.solve1Dmodel()
            for (i,p,_), _ in new_schedules.items():
                schedules.append((i,p,q))

            current_schedules = new_schedules
            q+=1

        self.delta = original_delta
        return schedules
    
    
    def write_schedule(self, schedules, filename='lrfhss_schedule.txt'):

        with open(filename, 'w') as f:
            for i,p,q in schedules:
                f.write(f"{i},{p},{q}\n")


    def solve1Dmodel(self):

        # no console log Gurobi environment
        env = gp.Env(empty=True)
        env.setParam("OutputFlag", 0)
        env.start()

        # Create a new model
        model = gp.Model("lrfhss_packing", env=env)

        # Create variables
        I = range(self.N * self.C)
        P = range(self.W)
        N = range(self.N)
        C = range(self.C)
        x = model.addVars(I, P, vtype=GRB.BINARY, name="x")


        # Set objective
        model.setObjective(
            gp.quicksum(x[i,p] for i in I for p in P),
            GRB.MAXIMIZE
        )

        # Add constraints
        # Constraint (1): Each ED can transmit only once
        for n in N:
            model.addConstr(
                gp.quicksum(x[n + self.N*c, p] for p in P for c in C) <= 1
            )

        # Constraint (2): At most 280 items can cover any point p
        for p in P:
            model.addConstr(
                gp.quicksum(x[i,a] for i,a,b in self.xi_p_q[p][0]) <= self.numOBW
            )

        # Constraint (3): Items can only be placed at feasible positions
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
