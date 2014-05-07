# -*- coding: utf-8 -*-
from random import shuffle
from random import random
from experiment import Experiment
from math import exp
from utility import pdf
from utility import cdf
from utility import randomFromCDF
from utility import getTimeStampString

VERBOSE = False
def setVerbose(val = VERBOSE):
    global VERBOSE
    VERBOSE = val
    return val

def verbose(stuff):
    if VERBOSE:
        print(stuff)

save_history = False
history_file = None
timestamp = ""
def writeHistory(folder):
    global save_history, history_file
    save_history = True
    filename = folder + "history " + timestamp + ".csv"
    history_file = open(filename, 'w')
    history_file.write("Unhappy, Sameness, Tolerance\n")

def archive(stuff):
    if history_file:
        history_file.write(stuff)
    

Grid_Size = 100
def setGridSize(value = Grid_Size):
    global Grid_Size
    Grid_Size = value
    return value

Num_of_Races = 2
Races = [0,1]
def setNumOfRaces(value = Num_of_Races):
    global Num_of_Races, Races
    Num_of_Races = value
    Races = [i for i in range(value)]
    return value

Empty_Space = 0.2
def setEmptySpace(value = Empty_Space):
    global Empty_Space
    Empty_Space = value
    return value

# initial fraction of population with no neighborhood preference
# the remainder are Schelling_Pref Segregation type 
Schelling_Pref = 1
No_Preference = 0
Initial_Opinion_Split = 0.5
def setInitialOpinionSplit(f=Initial_Opinion_Split):
    global Initial_Opinion_Split
    Initial_Opinion_Split = f
    return f

h_over_T = 0

Social_Force = 0.0  # social force h_s in the direction of "no preference"
def setSocialForce(val=Social_Force):
    global Social_Force, h_over_T
    Social_Force = val
    h_over_T = Social_Force/Social_Temperature
    return val

Social_Temperature = 1.0
def setSocialTemperature(val=Social_Temperature):
    global Social_Temperature, h_over_T
    Social_Temperature = val
    h_over_T = Social_Force/Social_Temperature
    return val

# how often do agents decide to move on average, irrespective of neighbors
Move_Rate = 0.1
def setMoveRate(val):
    global Move_Rate
    Move_Rate = val
    return val

def location(x,y):
    return (x%Grid_Size, y%Grid_Size)

def degree(agent):
    return len(agent.friends)

class Agent(object):
    
    def __init__(self, race):
        '''
        race is a number and represents the "race" of the agent
        '''
        self.race = race
        #self.opinion = No_Preference if random()<Initial_Opinion_Split else Schelling_Pref
        self.opinion = Schelling_Pref if random()>Initial_Opinion_Split else No_Preference
        self.friends = [self] # social network
    
    def step(self):
        Move_Rate += 1
        
    def connectTo(self, other):
        self.friends.append(other)
        other.friends.append(self)
    
    def evaluateOpinionState(self):
        # statistical mechanics of opinion formation
        no_pref_friends = [friend for friend in self.friends if friend.opinion==No_Preference]
        n0 = len(no_pref_friends)
        N = len(self.friends)
        n1 = N - n0 
        z = exp(h_over_T)*(n0/N)**(1/Social_Temperature) + exp(-h_over_T)*(n1/N)**(1/Social_Temperature)
        P_no_pref = (exp(h_over_T)*(n0/N)**(1/Social_Temperature))/z
        P_schell = (exp(-h_over_T)*(n1/N)**(1/Social_Temperature))/z
        if random()<P_no_pref:
            self.opinion = No_Preference
        else:
            self.opinion = Schelling_Pref
        
    def wantsToMove(self):
        prob_no_move = exp(-Move_Rate) # Poisson process probability that k=0 move events occur in one tick 
        return random() > prob_no_move        

    def isUnhappy(self, neighbors):
        if self.opinion == Schelling_Pref:
            count = [0 for i in Races] #counts of neighbors of each race in this agent's neighborhood
            for neighbor in neighbors:
                count[neighbor.race] += 1
            local_distribution = sorted(Races, key = lambda race: count[race]) # sort ascending by race count
            local_distribution = [race for race in local_distribution if count[race]>0]  # strip out non-present races
            if local_distribution[0]==self.race and len(local_distribution)>1:  # self in smallest minority
                if count[local_distribution[1]] > count[self.race]:  # not a tie
                    return True
                else:
                    return False
            else:
                return False
        else:  # no preference, therefore happy
            return False

class Schelling_Sim(object):

    def __init__(self):
        self.agents = {}
        self.locations = [(x,y) for x in range(Grid_Size) for y in range(Grid_Size)]
        agents_per_race = int((Grid_Size**2)*(1-Empty_Space)/Num_of_Races)
        shuffle(self.locations)
        loc_idx = 0
        minimum_friends = 3
        agents = []
        for race in range(Num_of_Races):
            for i in range(agents_per_race):
                new_agent = Agent(race)
                potential_friends = agents.copy()
                for j in range(minimum_friends):
                    if potential_friends:
                        degrees = [degree(agent) for agent in potential_friends]
                        friend = potential_friends[randomFromCDF(cdf(degrees))]
                        new_agent.connectTo(friend)
                        potential_friends.remove(friend)
                loc = self.locations[loc_idx]
                loc_idx += 1
                self.agents[loc] = new_agent
                agents.append(new_agent)
                
        # start keeping track of empty locations for unhappy agents to move to
        self.empty_locations = []
        for i in range(loc_idx, len(self.locations)):
            self.empty_locations.append(self.locations[i])
        self.steps = 0
        self.unhappy_count = 0

    def getNeighborsOf(self, loc):
        (x0, y0) = loc
        neighbors = []
        for x in [x0-1, x0, x0+1]:
            for y in [y0-1, y0, y0+1]:
                if location(x,y) in self.agents.keys():
                    neighbors.append(self.agents[location(x,y)])
        return neighbors

    def step(self):
        self.steps += 1
        self.unhappy_count = 0
        shuffle(self.locations)
        shuffle(self.empty_locations)
        for loc in self.agents.keys():
            agent = self.agents[loc]
            agent.evaluateOpinionState()
            neighbors = self.getNeighborsOf(loc)
            if agent.isUnhappy(neighbors):
                self.unhappy_count += 1
                self.moveAgentAt(loc)
            elif agent.wantsToMove():
                self.moveAgentAt(loc)
        values = (self.getUnhappyPercentage(), self.getPercentSameness(), self.getNoPreferenceFraction())
        verbose("Unhappy: %2.2f \t Sameness: %2.2f \t Tolerance: %0.2f"%values)
        archive("%2.2f, %2.2f, %0.2f\n"%values)


    def moveAgentAt(self, loc):
        # move agent to first empty location in list
        agent = self.agents.pop(loc)  # remove it from the dictionary
        new_loc = self.empty_locations[0]
        self.agents[new_loc] = agent # insert into dictionary with new location
        del self.empty_locations[0] # location no longer empty
        self.empty_locations.append(loc) # append vacated location

    def getUnhappyPercentage(self):
        return 100*self.unhappy_count/len(self.agents.keys())

    def getPercentSameness(self):
        same = 0
        for loc in self.agents.keys():
            neighbors = self.getNeighborsOf(loc)
            race = self.agents[loc].race
            count = -1 #subtract one for the agent at the center
            for agent in neighbors:
                if agent.race==race:
                    count += 1
            same += count/(len(neighbors)-1) # don't count center agent towards average
        return 100*same/len(self.agents.keys())
    
    def getNoPreferenceFraction(self):
        return sum([1 for agent in self.agents.values() if agent.opinion==No_Preference])/len(self.agents)

class SSMExperiment(Experiment):

    def __init__(self):
        super(SSMExperiment, self).__init__()
        setGridSize(50)
        setEmptySpace(0.01)
        setMoveRate(0.1)
        self.sim = None

    def initiateSim(self):
        global timestamp
        self.datetime = getTimeStampString()
        timestamp = self.datetime
        writeHistory("../output/histories/")
        self.sim = Schelling_Sim()
        self.delta_unhappy = 100
        self.last_unhappy = 100
        self.sameness = 0
        self.turns = 0

    def stopSim(self):
        return self.delta_unhappy < 0.1 and self.turns>=50

    def stepSim(self):
        self.sim.step()
        unhappy = self.sim.getUnhappyPercentage()
        self.delta_unhappy = abs(self.last_unhappy - unhappy)
        self.last_unhappy = unhappy
        self.sameness = self.sim.getPercentSameness()
        self.turns += 1

    def getHappiness(self):
        return 100-self.last_unhappy

    def getSameness(self):
        return self.sameness

    def getSteps(self):
        return self.sim.steps
    
    def getTolerance(self):
        return self.sim.getNoPreferenceFraction()

    def setupOutputs(self):
        self.addOutput(self.getSteps, "runtime", "%2d")
        self.addOutput(self.getHappiness, "pct happy", "%3.2f")
        self.addOutput(self.getSameness, "pct same", "%3.2f")
        self.addOutput(self.getTolerance, "tolerance", "%1.2f")

    def setupParameters(self):
        self.addParameter(setNumOfRaces, [2])
        self.addParameter(setInitialOpinionSplit, [0.25, 0.5, 0.75])
        self.addParameter(setSocialForce, [-0.25, 0, 0.25])
        self.addParameter(setSocialTemperature, [0.01, 0.1, 1.0])

    def setupExperiment(self):
        self.Name = "Schelling Stat Mech Experiment"
        self.comments = "Running at end and mid points for history files"
        self.setupParameters()
        self.job_repetitions = 20

class SSMExperiment2(SSMExperiment):

    def __init__(self):
        super(SSMExperiment2, self).__init__()
        
    def setupExperiment(self):
        self.Name = "Schelling Stat Mech Experiment"
        self.comments = "Looking at preferential attachment"
        self.setupParameters()
        self.job_repetitions = 20
    
    def setupParameters(self):
        self.addParameter(setNumOfRaces, [2])
        self.addParameter(setInitialOpinionSplit, [0.5])
        self.addParameter(setSocialForce, [0])
        self.addParameter(setSocialTemperature, [1.0])
        
def singleRun():
    setGridSize(50)
    setEmptySpace(0.1)
    setInitialOpinionSplit(0.5)
    setMoveRate(0.0001)
    last_unhappy = 100
    delta_unhappy = 100
    sameness = 0
    setVerbose(True)    
    sim = Schelling_Sim()
    turns = 0
    while(delta_unhappy > 0.1 or turns < 50):
        sim.step()
        unhappy = sim.getUnhappyPercentage()
        delta_unhappy = abs(last_unhappy - unhappy)
        last_unhappy = unhappy
        turns += 1

if __name__ == "__main__" :
    #SSMExperiment2().run()
    SSMExperiment().run()
    #singleRun()