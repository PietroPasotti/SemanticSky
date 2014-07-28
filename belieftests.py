#!/usr/bin/python3

import tests

wrap = tests.wrap
table = tests.table
bmag = tests.bmag
bar = tests.clues.ss.bar

def setup_new_god():
	
	tests.load_sky()
	sky = tests.sky
	
	God = tests.clues.God(sky)
	return God
	
def interactive_setup(god):
	"""
	Allows for semi-interactive picking of guardianangels for a given god.
	"""
	
	if god.guardianangels:
		pass
	else:
		god.spawn_servants()
		
	servs = []
	
	n = 0
	for ga in god.guardianangels:
		servs.append([n,ga])
		n += 1
		
	tdict = {number:serv for number,serv in servs}
	
	chosen = []
	
	print()
	table(servs)
	print()
	print('Enter the GuardianAngels you want to assign to {} '.format(god),'using the syntax "0,1,2,3...". "A" == All. Intervals accepted ("-").')
	while True:
		choice = input(bmag('\t>>: '))
		
		if not choice: # require an explicit choice
			continue
			
		if choice.strip() == 'A':
			chosen = god.guardianangels						
		else:			
			tolist = choice.split(',')
			for elem in tolist:
				tolist[tolist.index(elem)] = elem.strip()
					
			while '' in tolist:
				tolist.remove('')
			
			chosen = []
			
			for elem in tolist:
				if elem.isdigit() and '.' not in elem and int(elem) < len(tdict):
					n = int(elem)
					chosen.append(tdict[n])
				elif '-' in elem: # parsing for intervals
					ch = elem.split('-')
					
					ini = ch[0]
					end = ch[1]
					
					top = len(tdict)
			
					try:
						ini = int(ini)
						end = int(end)
						if not 0<ini<end or not 0<end<top:
							continue
						
						for i in range(ini,end+1,1):
							chosen.append(tdict[i])
					except BaseException:
						continue
				else:
					print('Unrecognized input {}; skipping...'.format(elem))
					
		print("\t>> Selected:")
		for i in chosen:
			print('\t\t\t',repr(i))
		
		if input(bmag('\t>> Confirm? ')) in 'yesYES':
			break
			
	god.guardianangels = chosen
	
	tests.load_evaluations_to_gas(god.guardianangels)
	
	if input(bmag('\t>> Do you want to load weights as well? ')) in 'yesYES':
		tests.load_weights_to_gas(god.guardianangels)
		print('\t\t[Loaded.]')
	print()
	print('\t[All ready.]')
	
	print("\tNow the guardians' evaluations will be merged...")
	print('\t\t(aliasing links...)')
	equate_all_links(god,god.guardianangels)
	
	print('\t\tExpressing...')
	express_all(god)
	
	if input(bmag('\t>> Summon the Knower and give feedback? ')) in 'yesYES':
		knower = getknower(god)
		try:
			knower.evaluate_all(express = False)
		except BaseException:
			knower.new_supervisor(god)
			pass
			
		print()
		equate_all_links(god,[knower])	
		if knower not in god.whisperers:
			god.whisperer(knower)
		knower.express()

	print('\t\t[Done.]')
	
	if input(bmag('\t>> Display trusts? ')) in 'yesYES':
		god.trusts(god.guardianangels,local = False)
	
	print(wrap('...exiting interactive environment.','red'))
	return god
	
def express_all(god):
	
	for ga in god.guardianangels:
		ga.express()

def getknower(god):
	
	return tests.clues.knower if tests.clues.knower else tests.clues.Knower(god)

def give_feedback(god,knower):
	
	knower.express()

def equate_all_links(god,angels):
	"""
	When unpickling evaluations, we often have that clouds made out of the same items
	are no longer properly indexed in dictionaries: they appear as different
	pairs altogether.

	This function only acts on evaluations of guardianangels of the given deity
	or of the default god, setting their evaluations to a common vocabulary
	of cloud pairs.
	"""
		
	pid = lambda x: (tuple(x)[0].item['id'], tuple(x)[1].item['id'])	

	print('\t\tParallelising beliefs... (May take a while)')
		
	for ga in angels:
		
		totln = len(ga.evaluation)
		print('\t\t\tAliasing links for ',ga)
		print()
		i = 0
		for link,ev in ga.evaluation.items():
			del ga.evaluation[link]
			itlinks = pid(link)
			truelink = god.sky.pair_by_id(*itlinks)

			ga.evaluation[truelink] = ev
			
			bar(i/totln)
			i+=1			
		print()
		
	return True
