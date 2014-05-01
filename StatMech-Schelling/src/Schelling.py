# -*- coding: utf-8 -*-
from random import shuffle
from random import random
from experiment import Experiment

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

# initial fraction of population with a "Schelling" attitude
# the remainder are indifferent to neighborhood racial make-up 
Schelling = 1
No_Preference = 0
Initial_Opinion_Split = 0.5
def setInitialOpinionSplit(f=Initial_Opinion_Split):
    global Initial_Opinion_Split
    Initial_Opinion_Split = f
    return f

Social_Force = 0.0
def setSocialForce(val=Social_Force):
    global Social_Force
    Social_Force = val
    return val

Social_Temperature = 1.0
def setSocialTemperature(val=Social_Temperature):
    global Social_Temperature
    Social_Temperature = val
    return val

# how often do agents decide to move on average, irrespective of neighbors
Move_Frequency = 0.1
def setMoveFrequency(val):
    global Move_Frequency
    Move_Frequency = val
    return val

Minimum_Residency = 3

def location(x,y):
    return (x%Grid_Size, y%Grid_Size)

class Agent(object):
    
    def __init__(self, race):
        '''
        race is a number and represents the "race" of the agent
        '''
        self.race = race
        self.opinion = No_Preference if random()>Initial_Opinion_Split else Schelling
        self.friends = []
        self.residency = random()/Move_Frequency
        
    def connectTo(self, other):
        self.friends.append(other)
    
    def evaluateOpinionState(self):
        no_pref_friends = [friend for friend in self.friends if friend.opinion==No_Preference]
        n0 = len(no_pref_friends)
        N = len(self.friends)
        n1 = N - n0
        z = 
        

    def isUnhappy(self, neighbors):
        if self.opinion == Schelling:
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
        else:
            return False

class SchellingSim(object):

    def __init__(self):
        self.agents = {}
        self.locations = [(x,y) for x in range(Grid_Size) for y in range(Grid_Size)]
        agents_per_race = int((Grid_Size**2)*(1-Empty_Space)/Num_of_Races)
        shuffle(self.locations)
        loc_idx = 0
        for race in range(Num_of_Races):
            for i in range(agents_per_race):
                loc = self.locations[loc_idx]
                loc_idx += 1
                self.agents[loc] = Agent(race)
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
            neighbors = self.getNeighborsOf(loc)
            if agent.isUnhappy(neighbors):
                self.unhappy_count += 1
                self.moveAgentAt(loc)

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

class SSMExperiment(Experiment):

    def __init__(self):
        super(SSMExperiment, self).__init__()
        setGridSize(50)
        setEmptySpace(0.01)
        self.sim = None

    def initiateSim(self):
        self.sim = SchellingSim()
        self.delta_unhappy = 100
        self.last_unhappy = 100
        self.sameness = 0

    def stopSim(self):
        return self.delta_unhappy < 0.1

    def stepSim(self):
        self.sim.step()
        unhappy = self.sim.getUnhappyPercentage()
        self.delta_unhappy = abs(self.last_unhappy - unhappy)
        self.last_unhappy = unhappy
        self.sameness = self.sim.getPercentSameness()

    def getHappiness(self):
        return 100-self.last_unhappy

    def getSameness(self):
        return self.sameness

    def getSteps(self):
        return self.sim.steps

    def setupOutputs(self):
        self.addOutput(self.getSteps, "runtime", "%2d")
        self.addOutput(self.getHappiness, "pct happy", "%3.2f")
        self.addOutput(self.getSameness, "pct same", "%3.2f")

    def setupParameters(self):
        self.addParameter(setAgentClass, ["ORIGINAL", "VARIANT"])
        self.addParameter(setNumOfRaces, [2, 3])#, 3, 4, 5, 6, 7, 8])

    def setupExperiment(self):
        self.Name = "Schelling Experiment"
        self.comments = "Original vs Variant"
        self.setupParameters()
        self.job_repetitions = 20

if __name__ == "__main__" :
    SSMExperiment().run()
