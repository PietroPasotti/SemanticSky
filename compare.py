import semanticsky as ss

def compare(sky):
	
	holder = {}
	
	index = 0
	for clouda in sky.clouds():
		for cloudb in sky.sky[index+1]:
			if cloudb is clouda:
				continue
		
			prox = clouda.proximity(cloudb)
			pv = sum(prox.values()) 
			
			if pv: holder[(clouda,cloudb)] = float(pv)
		index += 1
	
	return holder
