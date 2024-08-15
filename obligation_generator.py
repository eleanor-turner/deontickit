import argparse
import re
import os 
from pprint import pprint
from pathlib import Path

import random
import graphviz
from string import ascii_lowercase

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

#props = [p1,p2,p3,p4]
def gen_c_box(props):
	new_box = ''
	if len(props) == 2:
		new_box = f'[]({props[0]} -> {props[1]})'
	if len(props) > 2: 
		new_box = f'[]({props[0]} -> {gen_c_box(props[1:])})'
	return new_box

#props = [p1,p2,p3,p4]
def gen_d_box(props):
	new_box = ''
	if len(props) == 2:
		new_box = f'[](~{props[0]} -> ~{props[1]})'
	elif len(props) > 2: 
		new_box = f'[](~{props[0]} -> {gen_c_box(props[1:])})'
	return new_box

# facts = [f_1, f_2, ...]
# consequents = [p_1, p_2, ...]
def generate_obligations(facts, consequents, num_levels):
	obs = []
	sys = []

	# Generate initial obligations 
	for i, fact in enumerate(facts):
		conseq = consequents[i] # p_1

		obs.append(f'n{i+1}_1a: {fact}.')
		obs.append(f'n{i+1}_1b: []~{fact}.')
		obs.append(f'n{i+1}_1c: []({fact} -> {conseq}_1).')
		obs.append(f'n{i+1}_1d: [](~{fact} -> ~{conseq}_1).')

		system_conj = f'n{i+1}_1a & n{i+1}_1b & n{i+1}_1c & n{i+1}_1d'

		sys.append(f'N{i+1}_1 = {system_conj}.')

		if num_levels > 1:
			conseqs = [f'{conseq}_{l}' for l in range(1, num_levels+1)] # [p_1, p_2, ...]

			for l in range(2, num_levels+1):
				cons = conseqs[:l]
				obs.append(f'n{i+1}_{l}a: {conseq}_{l-1}.')
				obs.append(f'n{i+1}_{l}b: []~{conseq}_{l-1}.')
				obs.append(f'n{i+1}_{l}c: []({fact} -> {gen_c_box(cons)}.')
				obs.append(f'n{i+1}_{l}d: [](~{fact} -> {gen_d_box(cons)}.')

				system_conj += f' & n{i+1}_{l}a & n{i+1}_{l}b & n{i+1}_{l}c & n{i+1}_{l}d'

				sys.append(f'N{i+1}_{l} = {system_conj}.')

	return obs, sys

def write_obligations(command, obligation_list, system_list, file_name):
	with open(f'{file_name}.txt', 'w') as file: 
		file.write(f'Name: {file_name}\n')
		file.write(f'Source: \n')
		file.write(f'Command: {command}\n')
		file.write(f'Logic: SDL\n')
		file.write(f'Author: \n')
		file.write(f'----\n')
		for prop in obligation_list:
			file.write(f'{prop}\n')
		file.write('\n')
		for sys in system_list:
			file.write(f'{sys}\n')

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-o', '--output_folder', type=str, help='output folder')
	parser.add_argument('-f', '--num_facts', type=int, help='number of facts to initialise')
	parser.add_argument('-l', '--num_levels', type=int, help='number of ctd levels to generate')
	args = parser.parse_args()

	command = f'--num_facts={args.num_facts}, --num_levels={args.num_levels}'

	literals = [f'f_{i}' for i in range(1, args.num_facts+1)]
	consequents = [f'p_{i}' for i in range(1, args.num_facts+1)]
 
	obligation_list, system_list = generate_obligations(literals, consequents, args.num_levels)
	file_path = f"{args.output_folder}/ctd_{args.num_facts}facts_{args.num_levels}levels"

	write_obligations(command, obligation_list, system_list, Path(file_path))
	print(f"Done. Output at {file_path}.")

# To call function:
# obligation_generator.py --output=outputs\graph3 --num_levels=2 --world_gen=False