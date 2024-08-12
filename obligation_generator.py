import argparse
import re
import os 
from pprint import pprint
from pathlib import Path

import random
import graphviz
from string import ascii_lowercase

def write_obligations(obligation_list, file_name):
	with open(f'{file_name}.txt', 'w') as file: 
		file.write(f'Name: {file_name}\n')
		file.write(f'Source: \n')
		file.write(f'Comment: \n')
		file.write(f'Logic: SDL\n')
		file.write(f'Author: \n')
		file.write(f'----\n')
		full_prop = 'SDL: '
		for ind, prop in enumerate(obligation_list):
			file.write(f's{ind+1}: {prop}.\n')
			full_prop += f's{ind+1} & '
		file.write(f'{full_prop[:-3]}.')

def graph_generation(worlds, output_path):
	f = graphviz.Digraph(str(output_path))
	world_list = list(worlds.keys())

	description_list = []
	for key in worlds:
		li = worlds[key]
		li.insert(0,key)
		description_list.append('\n'.join(li))

	names = world_list
	positions = description_list
	for name, position in zip(names, positions):
	     f.node(name, position)

	for i, w in enumerate(world_list):
		if i < len(world_list)-1:
			f.edge(w, world_list[i+1])
	 
	f.view()

def generate_secondary_obs():
	pass

def check_for_infinite_loops(prop, neg, consequents, obligation_list):
	# Remove prop from consequents list to avoid infinite loops like 'r -> []r'
	if neg == False: # prop = 'a'
		conseqs = [c for c in consequents if c != prop and c != f'~{prop}']
	if neg == True: # prop = '~a'
		conseqs = [c for c in consequents if c != prop and f'~{c}' != prop]

	# How to avoid loops like 'r -> []q', 'q -> []r'?
	# We want to create a conditional of the form 'r -> []q'. 
	# So first check whether 'q -> []r' already exists.

	# Find conditionals that have the relevant consequent 
	conditionals = [st for st in obligation_list if '->' in st and st.split("]")[1] == prop] # e.g. ['q -> []r', 's -> []r']
	antecedents = [con.split()[0] for con in conditionals] # e.g. ['q', 's']
	conseqs = [c for c in conseqs if c != antecedents]

	# How to avoid loops like 'r -> []s', 's -> []q', 'q -> []r'?

	return conseqs

def recursive_conditional_generation(level, num_levels, full_obligation_list, consequents):
	# obligation_list = ['a', '[]a', 'b', '[]~b']
	# 2nd ob_list = 	['a -> []p', '[](a -> []s)', ...]
	# 3rd ob_list = 	['a -> [](p -> []q)', '[](a -> [](s -> []~r))']
	obligation_list = full_obligation_list if level == 1 else full_obligation_list[-1]
	new_ob_list = []
	for prop in obligation_list:

		def add_conditional(ante):
			cons = random.choice(consequents)
			conditional = f'{ante} -> []{cons}'
			return conditional

		def recursive_generation(prop):
			if prop[0] == '(':
				reduction = prop[1:-1]
				new = recursive_generation(reduction)
				new_statement = f'{new}'

			# Get atomic variables 'a': Generate 'a -> []p'
			elif prop[0] != '[' and '->' not in prop: 
				new_statement = add_conditional(prop)
	 
			# Get propositions of the form 'a -> []p': Generate 'a -> [](p -> []q)'
			elif prop[0] != '[' and '->' in prop:
				ante = prop.split(' ->')[0] # 'a'
				reduction = prop.split('-> []')[1] # 'p'
				cons = recursive_generation(reduction)
				new_statement = f'{ante} -> []({cons})'

			# Get propositions of the form '[]a': Generate '[](a -> []p)'
			# Get propositions of the form '[](a -> []p)': Generate '[](a -> [](p -> []~r))'
			elif prop[0] == '[':
				# Get everything after first instance of []
				index = prop.find(']')
				reduction = prop[index+1:]
				cond = recursive_generation(reduction)
				new_statement = f'[]({cond})'

			else:
				print("Error in recursive_conditional_generation: didn't capture all cases")
			return new_statement

		cond = recursive_generation(prop)
		new_ob_list.append(cond)

	full_obligation_list.append(new_ob_list)

	if level < num_levels:
		# list(set()) removes any duplicates
		full_obligation_list = recursive_conditional_generation(level+1, num_levels, obligation_list, consequents)

	flat_obligation_list = []
	for item in full_obligation_list:
		if type(item)!=list:
			flat_obligation_list.append(item)
		else:
			flat_obligation_list.extend(item)

	return flat_obligation_list

def generate_obligations(literals, consequents, num_levels):
	prop_var_list = [] 
	obligation_list = []

	# Generate initial obligations 
	for literal in literals:
		prop_var_list.append(literal)
		obligation_list.append(literal)

		# Generate unconditional obligations
		uncond_ob = f'[]{literal}'
		if random.choice([True, False]):
			uncond_ob = f'[]~{literal}'
		obligation_list.append(uncond_ob)

	# Generate conditional obligations
	level = 1
	obligation_list = recursive_conditional_generation(level, num_levels, obligation_list, consequents)
	print("full_obligation_list", obligation_list)
	return obligation_list

def recursive_world_creation(worlds, world_num, proposition_list):
	""" This function tells us what variables exist in each world, given a list of propositions. 
		E.g. With a proposition_list = ['a', '[]a', 'b', '[]~b', 'c', '[]c', 'a -> []~t', 'b -> []p', '~b -> []t', 'c -> []~r']
			this world would have ['a', '[]a', 'b', '[]~b', 'c', '[]c', '[]~t', '[]p', '[]~r']
			then the next world would be ['a', '~b', 'c', '~t', 'p', '~r', '[]~t', '[]t', '[]~r']
			and the final world would be ['~t', 't', '~r']
	"""

	""" This function tells us what variables exist in each world, given a list of propositions. 
		E.g. With a proposition_list = ['a', '[]~a', 'a -> []p', '[](~a -> []s)', 'a -> [](p -> []q)', '[](~a -> [](s -> []~r))']
			this world would have ['a', '[]~a', '[]p', [](p -> []q), '[](~a -> []s)', '[](~a -> [](s -> []~r))']
			then the next world would be ['~a', 'p', 'p -> []q', '~a -> []s', '~a -> [](s -> []~r)']
			then the next world would be ['q', 's', 's -> []~r']
			and the final world would be ['~r']
	"""


	world = f'w_{world_num}' 
	print(f'{world} proposition list', proposition_list)

	states = [x for x in proposition_list if len(x) <= 3 and x[0] != '[']
	obligations = [x for x in proposition_list if x[0] == '[']
	conditionals = [x for x in proposition_list if '->' in x]
	conseqs = [c[c.find(' -> ')+4:] for c in conditionals if c.split()[0] in states] 
	# Example: If proposition_list = ['a', '[]a', 'a -> []u'] then:
		# states = ['a']
		# obligations = ['[]a']
		# conditionals = ['a -> []u']
		# conseqs = ['[]u']

	# Get relevant obligations in the world
	worlds[world] = states + obligations + conseqs 
	# remove duplicates from the list
	worlds[world] = list(dict.fromkeys(worlds[world]))
	print(f'{world} list', worlds[world])

	new_proposition_list = obligations + conseqs
	if len(obligations + conseqs) > 0:
		# Any obligations '[]a' become 'a' in the next world
		for i, st in enumerate(new_proposition_list):
			if st[0] == '[':
				new_prop = st[2:]
				if new_prop[0] == '(':
					new_prop = new_prop[1:-1]
				new_proposition_list[i] = new_prop
		recursive_world_creation(worlds, world_num+1, new_proposition_list)

def create_worlds(obligation_list):
	print("World Generation")

	worlds = {}
	world_num = 0
	recursive_world_creation(worlds, world_num, obligation_list)
	return worlds

if __name__ == '__main__':
	literal_list = ascii_lowercase[:8] #[a,b,c,d,e,f,g,h]
	conseq_list = ascii_lowercase[15:] #[p,q,r,s,t,u,v,w,x,y,z]

	parser = argparse.ArgumentParser()
	parser.add_argument('-o', '--output', type=Path, help='output file')
	parser.add_argument('-l', '--num_levels', type=int, help='number of levels to generate')
	parser.add_argument('-w', '--world_gen', help='do you want to generate worlds?')
	args = parser.parse_args()

	num_atomics = 3
	num_conditionals = 6

	literals = literal_list[:num_atomics]
	consequents = conseq_list[:num_conditionals]
	print(f'literals: {literals}, consequents: {consequents}, num_levels: {args.num_levels}')
	consequents = [x for x in consequents] + [f'~{x}' for x in consequents]
	print(f'consequents: {consequents}')
 
	obligation_list = generate_obligations(literals, consequents, args.num_levels)
	write_obligations(obligation_list, args.output)
	if args.world_gen.lower() in ['true','yes','y']:
		worlds = create_worlds(obligation_list)
		graph_generation(worlds, args.output)
		print('Worlds')
		print(worlds)

# To call function:
# obligation_generator.py --output=outputs\graph3 --num_levels=2 --world_gen=False