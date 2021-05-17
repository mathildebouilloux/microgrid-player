# python 3
# this class combines all basic features of a generic player
import numpy as np


class Player:

	def __init__(self):
		# some player might not have parameters
		self.parameters = 0
		self.horizon = 48

	def set_scenario(self, scenario_data):
		self.data = scenario_data
		arr_dep = list(scenario_data_values())[:self.nb_slow + self.nb_fast]
		self.depart = {"slow": [d[1] for d in arr_dep[:self.nb_slow]], "fast": [d[1] for d in arr_dep[self.nb_slow:self.nb_fast + self.nb_slow]]}
		self.arrival = {"slow": [d[0] for d in arr_dep[:self.nb_slow]], "fast": [d[0] for d in arr_dep[self.nb_slow:self.nb_fast + self.nb_slow]]}
		# depart et arr contiennent respectivement la liste des heures de départ et d'arrivée des véhicules à la date d
		d="01/01/2014"
		self.depart=list(scenario_data[(scenario_data["day"] == d)]["time_slot_dep"][:p.nb_slow + p.nb_fast])
		self.arr = list(scenario_data[(scenario_data["day"] == d)]["time_slot_arr"][:p.nb_slow + p.nb_fast])

	def set_prices(self, prices):
		self.prices = prices

	def compute_all_load(self):
		load = np.zeros(self.horizon)
		loadbis=np.zeros(self.nb_slow+self.nb_fast)
		for time in range(self.horizon):
			conso=0
			for i in range(self.nb_slow):
				plus = self.rho_c * min(self.pslow, min((10 - loadbis[i])/self.rho_c, 40 - conso))
				loadbis[i] += plus
				conso += plus
			for i in range(self.nb_slow,self.nb_slow+self.nb_fast):
				plus=self.rho_c*min(self.pfast,min((10-loadbis[i])/self.rho_c,40-conso))
				loadbis[i]+=plus
				conso+=plus
			load[time]=conso
		compteur=self.horizon-1
		
		m = np.min(self.depart)
		prix=self.prices[:m].copy()
		arg_max=0
		compteur=0
		while compteur<m:
			arg_min = np.argmin(prix)


p.set_scenario(f)
p.set_prices(random_lambda)


l=p.compute_all_load()

#fonction de cout qui ne prend pas encore en compte les amendes si les voitures ne sont pas chargées à temps
def cout(p,l):
	c=0
	for time in range(48):
		c+=l[time]*p[time]
	return c
print(cout(p.prices,l))


# python 3
# this class combines all basic features of a generic player
import numpy as np
import pandas as pa
random_lambda = np.random.rand(48)
class Player:

	def __init__(self):
		# some player might not have parameters
		self.parameters = 0
		self.horizon = 48
		self.nb_slow=2
		self.nb_fast=2
		self.pslow=3
		self.pfast=22
		self.capacite=10
		self.rho_c=0.95


	def set_scenario(self, scenario_data):
		self.data = scenario_data
		# depart et arr contiennent respectivement la liste des heures de départ et d'arrivée des véhicules à la date d
		d="01/01/2014"
		self.depart=list(scenario_data[(scenario_data["day"] == d)]["time_slot_dep"][:p.nb_slow + p.nb_fast])
		self.arr = list(scenario_data[(scenario_data["day"] == d)]["time_slot_arr"][:p.nb_slow + p.nb_fast])

	def set_prices(self, prices):
		self.prices = prices

	def compute_all_load(self):
		load = np.zeros(self.horizon)
		# l est une liste temporaire, on reprend ses valeurs et on les réordonne avant de les mettre dans load

		#on construit l en remplissant d'abord les voitures "slow" puis les "fast" pour chaque pas de temps
		l=np.zeros(self.horizon)

		#chargement prend en compte le chargement en cours pour chacun des véhicules
		chargement=np.zeros(self.nb_slow+self.nb_fast)

		for time in range(self.horizon):
			#consom<40
			consom=0

			for i in range(self.nb_slow):
				plus = self.rho_c * min(self.pslow, min((10 - chargement[i])/self.rho_c, 40 - consom))
				chargement[i] += plus
				consom += plus

			for i in range(self.nb_slow,self.nb_slow+self.nb_fast):
				plus=self.rho_c*min(self.pfast,min((10-chargement[i])/self.rho_c,40-consom))
				chargement[i]+=plus
				consom+=plus
			l[time]=consom

		#on réordonne les consomations en mettant à chaque fois la conso la plus importante sur le prix le faible restant
		m = np.min(self.depart)
		copie_prix=self.prices[:m].copy()
		cpt=0
		while cpt<m:
			arg_min = np.argmin(copie_prix)
			arg_max=np.argmax(l)
			load[arg_min]=l[arg_max]
			copie_prix[arg_min] = np.inf
			l[arg_max] = 0
			cpt+=1
			#load[time] = self.compute_load(time)
		print(load)
		return load

	def take_decision(self, time):
		# TO BE COMPLETED
		return 0

	def compute_load(self, time):
		load = self.take_decision(time)

		return load

	def reset(self):
		# reset all observed data
		pass

f=pa.read_csv(ev_scrnario, sep = ";","ev_scenarios.csv")
p=Player()
p.__init__()
p.set_scenario(f)
p.set_prices(random_lambda)

l=p.compute_all_load()

#fonction de cout qui ne prend pas encore en compte les amendes si les voitures ne sont pas chargées à temps
def cout(p,l):
	c=0
	for time in range(48):
		c+=l[time]*p[time]
	return c
print(cout(p.prices,l))
