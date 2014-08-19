#!/usr/bin/python3

def clusterize1(data):
	
	clusters =  []
	
	for tag in data:
		tdic = data[tag]
		aliases = []
		als = data[tag]['alias_of']
		if als != None:
			if isinstance(als,list):
				aliases.extend(als)
			elif isinstance(als,str):# or isinstance(als, unicode):
				aliases.append(als)
			else:
				print(tag,data)
				#raise BaseException('Wrong.')
			aliases.append(tag)
		else:
			aliases = [tag]
		
		clusters_with_some_alias = []
		for a in aliases:
			for cluster in clusters:
				if a in cluster:
					clusters_with_some_alias.append(clusters.index(cluster))
		
		ln = len(clusters_with_some_alias)
		if ln == 1:
			cluster = clusters[ clusters_with_some_alias[0] ]
			cluster.extend(aliases)
			clusters[ clusters_with_some_alias[0] ] = cluster
		elif ln == 0:
			clusters.append(aliases)
		else:
			# we have to merge different clusters which have elements now transitively aliased
			supercluster = []
			for index in clusters_with_some_alias:
				supercluster.extend(clusters[index])	
			supercluster.extend(aliases)
			
		for cluster in clusters:
			clusters[clusters.index(cluster)] = list(set(cluster)) # we remove all duplicates
		
	return clusters
