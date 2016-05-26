import networkx as nx
import numpy as np

class Deployment:
	def __init__(self, adj, lookup):
		self.__idx = {}
		self.chains = []
		self.matrix = adj
		self.nodes = lookup

	def push_parent(self, val):
		found = None
		for chain in range(len(self.chains)):
			for subchain in range(len(self.chains[chain])):
				if self.nodes[val] in self.chains[chain][subchain]:
					found = (chain, subchain)

		if found is None:
			self.chains.append([[self.nodes[val]]])

	def push_sibling(self, val, sibs):
		found = None
		for chain in range(len(self.chains)):
			for subchain in range(len(self.chains[chain])):
				for sib in sibs:
					if self.nodes[sib] in self.chains[chain][subchain]:
						found = chain

		if found is None:
			self.chains.append([[self.nodes[val]]])
		else:
			self.chains[found].append([self.nodes[val]])

	def push_child(self, val, parent):

		found = None
		for chain in range(len(self.chains)):
			for subchain in range(len(self.chains[chain])):
				if self.nodes[parent] in self.chains[chain][subchain]:
					found = (chain, subchain)

		if found is None:
			self.chains.append([[self.nodes[val]]])
		else:
			self.chains[found[0]][found[1]].append(self.nodes[val])

	def get_deployment(self):
		return self.chains

class Depgraph:
	def __init__(self, constraints):
		self.graph = nx.DiGraph()
		self.__set_deps(constraints)
		self.__plan = None
		self.nodes = self.graph.nodes()
		self.matrix = nx.adjacency_matrix(self.graph)

		self.parent_counts = np.asarray(self.matrix.sum(axis=0))
		self.child_counts = np.asarray(self.matrix.sum(1))

		self.parent_counts_mutable = np.asarray(self.matrix.sum(axis=0))

	def __requires(self, cmd, deps):
		if type(deps) is not list: deps = [deps]
		self.graph.add_edges_from([(dep, cmd) for dep in deps])

	def __set_deps(self, constraints):
		[self.__requires(c[0], c[1]) for c in constraints]

	def peek(self):
		return [i for i, x in enumerate(self.parent_counts_mutable.tolist()[0]) if x == 0]

	def pop(self):
		ready = self.peek()
		for i in ready:

			# subtract the row in the adj matrix
			selected_row = self.matrix[i].toarray()
			self.parent_counts_mutable = np.subtract(self.parent_counts_mutable, selected_row)

			# subtract out the index we're processing
			old_i = self.parent_counts_mutable.item((0,i))
			new_i = old_i - 1
			self.parent_counts_mutable.itemset((0,i), new_i)
			
		return ready

	def build_plan(self):
		if self.__plan: return self.__plan

		d = Deployment(self.matrix, self.nodes)

		parent = None
		current = None
		while self.peek() != []:
			parents = current
			current = self.pop()
			has_siblings = len(current) > 1

			for val in current:
				more_than_one_parent = self.parent_counts[0][val] > 1
				
				if has_siblings:
					d.push_sibling(val, current)
				elif more_than_one_parent:
					d.push_parent(val)
				else:
					d.push_child(val, parents[0])

		self.__plan = d.get_deployment()
		return self.__plan

def example():
	constraints = [
			("publish", ["ctls"]),
			("ctls", ["package"]),
			("package", ["screenshots"]),
			("screenshots", ["sass", "templates"]),
			("sass", ["global", "local"]),
			("templates", ["global", "local"]),
			("global", ["scaffold"]),
			("local", ["scaffold", "fetch"]),
			("scaffold", ["nuke"])
		]
	b = Depgraph(constraints)
	return b.build_plan()


