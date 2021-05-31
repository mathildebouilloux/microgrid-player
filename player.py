#FRANCHINO Thibault
#21-05-30
#methode d'optimisation lineaire
#avec contrainte de journee
#sans amende si chargement <= 25% au départ (chargement > 25% imposé)
#avec dechargement de 10% du aux 30km parcourus la journee % autonomie de 300km 
#avec v2g

#CORRECTIONS
#DATE DEPART CHARGE > 25% AU DEPART
#if (t == 2*self.depart[l]): devient if (t == 2*self.depart[l] - 1):
#PERIODE JOURNEE
#if (2*self.depart[l] < t and t <= 2*self.arr[l]): devient if (2*self.depart[l] <= t and t <= 2*self.arr[l] - 1):

import pulp
import pandas as pd
import numpy as np


class Player:
    
    def __init__(self):
        self.rho_c = 0.95 #coefficient de chargement
        self.nb_slow = 2 #nombre d'EV a chargement lent
        self.nb_fast = 2 #nombre d'EV a chargement rapide
        self.pslow = 3 #kW
        self.pfast = 22 #kW
        self.horizon = 48 #nombre de pas de temps de 30 min dans 24h
        self.aggregate_charging_power = 40 #kW
        self.battery_capacity = 40 #kWh #energie maximale dans la batterie
        self.fine = 5 #euros #montant de l'amende pour etre a moins de 25% au depart
        self.rho_d = 0.95 #coefficient de reinjection
        
        
        
    def set_scenario(self, scenario_data):
        d = "01/01/2014"
        self.depart = list(scenario_data[(scenario_data["day"] == d)]["time_slot_dep"][:self.nb_slow + self.nb_fast])
        self.arr = list(scenario_data[(scenario_data["day"] == d)]["time_slot_arr"][:self.nb_slow + self.nb_fast])
    
    def set_prices(self, prices):
        self.prices = prices
    
    def optimisation(self):
        modele = pulp.LpProblem("EV_opti", pulp.LpMinimize)
        
        load_v2g_plus = {} #partie positive
        load_v2g_minus = {} #partie negative
        capacity_v2g = {} #capacité de la batterie
        load = {} #chargement total
        to_charge = {} #distinction : doit-on charger ou reinjecter sur le reseau?
        
        for t in range(self.horizon):
            load_v2g_plus[t] = {}
            load_v2g_minus[t] = {}
            capacity_v2g[t] = {}
            to_charge[t] = {}
            load[t] = pulp.LpVariable("l_" + str(t), 0.0, self.aggregate_charging_power )
            
            for l in range(self.nb_slow + self.nb_fast) :
                #creation des variables
                ###########################################################
                var_name = "load_"+str(t)+"_EV_"+str(l+1)
                var_name_2 = "capacity_"+str(t)+"_EV_"+str(l+1)
                
                to_charge[t][l] = pulp.LpVariable("to_charge_" + str(l), cat="Binary") #variable binaire : charger ou reinjecter?
                capacity_v2g[t][l] = pulp.LpVariable(var_name_2, 0.0, self.battery_capacity ) #capacite de la batterie
                
                if (l < 2):
                    #EV lents indices de 0 a self.nb_slow -1
                    load_v2g_plus[t][l] = pulp.LpVariable("plus" + var_name,0.0, self.pslow )
                    load_v2g_minus[t][l] = pulp.LpVariable("minus" + var_name,0.0, self.pslow )
                else:
                    #EV rapides indices self.nb_slow a self.nb_fast -1
                    load_v2g_plus[t][l] = pulp.LpVariable("plus" + var_name, 0.0, self.pfast )
                    load_v2g_minus[t][l] = pulp.LpVariable("minus" + var_name, 0.0, self.pfast )
                
                if (t == 0):
                    #batterie dechargee a minuit
                    constraint_name = "charging_zero_"+ str(t) + "_" + str(l)
                    modele += capacity_v2g[0][l] == 0.0 , constraint_name
                
                if (t == 2*self.depart[l] - 1):
                    #depart
                    constraint_name = "charging_up_to_25_"+ str(t) + "_" + str(l)
                    modele += 0.2500001 * self.battery_capacity <= capacity_v2g[t][l] , constraint_name
                    
                if (2*self.depart[l] <= t and t <= 2*self.arr[l] - 1):
                    #en pleine journee, on roule donc on ne charge/reinjecte pas
                    constraint_name = "no_charging_"+ str(t) + "_" + str(l)
                    modele += load_v2g_plus[t][l] == 0.0 and load_v2g_minus[t][l] == 0.0 , constraint_name
                
                if (t == 2*self.arr[l]):
                    #arrivee
                    
                    #EV charge > 10% => a la fin de la journee, charge de 10% consommee
                    constraint_name = "discharged_after_trip_EV_"+ str(t) + "_" + str(l)
                    modele += capacity_v2g[t][l] == capacity_v2g[self.depart[l]][l] - 0.10 * self.battery_capacity , constraint_name
                
                if (t > 0 and t != 2*self.arr[l]):
                    #temps sauf minuit et arrivee 
                    #(journee n'influe pas non plus car les load_v2g[t][l] correspondant valent 0)
                    
                    #chargement ou reinjection
                    constraint_name = "load_demand_"+ str(t) + "_" + str(l)
                    modele += capacity_v2g[t][l] - capacity_v2g[t-1][l] == 0.5 * (self.rho_c * load_v2g_plus[t][l] - (1.0/self.rho_d) * load_v2g_minus[t][l])  , constraint_name
                    
                    #on ne charge pas en meme temps que l'on reinjecte 
                    constraint_name = "_charging_discharging_non_simultaneous_" + str(t) + "_" + str(l)
                    modele += ( (load_v2g_plus[t][l] == 0 and load_v2g_minus[t][l] != 0) or (load_v2g_plus[t][l] != 0 and load_v2g_minus[t][l] == 0) ), constraint_name
            
            #"definition" de load par une contrainte
            constraint_name = "l_aggregate_"+ str(t)
            modele += pulp.lpSum([ load_v2g_plus[t][l] - load_v2g_minus[t][l] for l in range(self.nb_slow + self.nb_fast) ]) == load[t]
            
            #chargement total limite en valeur absolue
            constraint_name = "aggregate_charging_power_"+ str(t)
            modele += load[t] <= self.aggregate_charging_power and load[t] >= - self.aggregate_charging_power, constraint_name
            
        #fonction objectif
        #modele += pulp.lpSum([self.prices[t] * (load_v2g_plus[t][l] - load_v2g_minus[t][l])  for l in range(self.nb_slow + self.nb_fast) for t in range(self.horizon)])
        modele += pulp.lpSum([self.prices[t] * load[t] for t in range(self.horizon)])
        
        #resolution
        modele.solve()
        
        #resultats
        res, res2, res3, res5 = [], [], [], []
        for k in range(self.nb_slow + self.nb_fast):
            l, l2, c =[], [], []
            for t in range(self.horizon):
                l.append(load_v2g_plus[t][k].value())
                l2.append(load_v2g_minus[t][k].value())
                c.append(capacity_v2g[t][k].value())                
            res.append(l)
            res5.append(l2)
            res2.append(c)
        
        for t in range(self.horizon):
            res3.append(load[t].value())
        
        return (res, res2, res3, modele.objective.value(),res5)

if __name__ == "__main__":
    
    #lecture des donnees
    scenario_data = pd.read_csv("ev_scenarios.csv", sep=";", decimal=".")
    
    #initialisation du joueur
    p = Player()
    p.set_scenario(scenario_data)
    
    #choix des prix
    #random_lambda = 5.0 * np.random.rand(p.horizon)
    #p.set_prices(random_lambda)
    
    prices_test = [1,2,3,4,5,6,7,8,9,1,2,3,4,5,6,7,8,9,1,2,3,4,5,6,7,8,9,1,2,3,4,5,6,7,8,9,1,2,3,4,5,6,7,8,9,1,2,3]
    prices_test = [0.5 * prices_test[i] for i in range(len(prices_test))]
    p.set_prices(prices_test)
    
    #lancement de l'optimisation et recuperation des resultats
    resultat = p.optimisation()
    l,c,l_aggregate, cout_total, l2 = resultat
    
    #affichage des resultats
    for k in range(p.nb_slow + p.nb_fast):
        print("\n" + "------------------" + "EV_" + str(k+1) + "------------------" + "\n")
        print("date_depart_EV_" + str(k+1) + "\n", p.depart[k] * 2,"\n" )
        print("date_arrivee_EV_" + str(k+1) + "\n", p.depart[k] * 2,"\n" )
        print("load_+_EV_" + str(k+1) + "\n",np.array(l[k]),"\n")
        print("load_-_EV_" + str(k+1) + "\n",np.array(l2[k]),"\n")
        print("capacity_EV_" + str(k+1) + "\n",np.array(c[k]),"\n")
    print("\n" + "------------------" + "resultats" + "------------------" + "\n")
    print("load_aggregate" + "\n",np.array(l_aggregate),"\n")
    print("prices" + "\n", p.prices, "\n")
    print("total_cost" + "\n",cout_total,"\n")
    
    
