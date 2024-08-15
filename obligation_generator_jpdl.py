import argparse
from pathlib import Path

#props = [p1,p2,p3,p4]
def gen_c_box(props):
	new_box = ''
	if len(props) == 2:
		new_box = f'[I]({props[0]} -> [Ought]{props[1]}) & [S]({props[0]} -> [Ought]{props[1]})'
	if len(props) > 2: 
		new_box = f'[I]({props[0]} -> {gen_c_box(props[1:])}) & [S]({props[0]} -> {gen_c_box(props[1:])})'
	return new_box

#props = [p1,p2,p3,p4]
def gen_d_box(props):
	new_box = ''
	if len(props) == 2:
		new_box = f'[I](~{props[0]} -> [Ought]~{props[1]}) & [S](~{props[0]} -> [Ought]~{props[1]})'
	elif len(props) > 2: 
		new_box = f'[I](~{props[0]} -> {gen_c_box(props[1:])}) & [S](~{props[0]} -> {gen_c_box(props[1:])})'
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
		obs.append(f'n{i+1}_1b: [Ought]~{fact}.')
		obs.append(f'n{i+1}_1c: [I]({fact} -> [Ought]{conseq}_1) & [S]({fact} -> [Ought]{conseq}_1).')
		obs.append(f'n{i+1}_1d: [I](~{fact} -> [Ought]~{conseq}_1) & [S](~{fact} -> [Ought]~{conseq}_1).')

		system_conj = f'n{i+1}_1a & n{i+1}_1b & n{i+1}_1c & n{i+1}_1d'

		sys.append(f'N{i+1}_1 = {system_conj}.')

		if num_levels > 1:
			conseqs = [f'{conseq}_{l}' for l in range(1, num_levels+1)] # [p_1, p_2, ...]

			for l in range(2, num_levels+1):
				cons = conseqs[:l]
				obs.append(f'n{i+1}_{l}a: {conseq}_{l-1}.')
				obs.append(f'n{i+1}_{l}b: [Ought]~{conseq}_{l-1}.')
				obs.append(f'n{i+1}_{l}c: [I]({fact} -> {gen_c_box(cons)}) & [S]({fact} -> {gen_c_box(cons)}).')
				obs.append(f'n{i+1}_{l}d: [I](~{fact} -> {gen_d_box(cons)}) & [S](~{fact} -> {gen_d_box(cons)}).')

				system_conj += f' & n{i+1}_{l}a & n{i+1}_{l}b & n{i+1}_{l}c & n{i+1}_{l}d'

				sys.append(f'N{i+1}_{l} = {system_conj}.')

	return obs, sys

def write_obligations(command, obligation_list, system_list, file_name):
	with open(f'{file_name}.txt', 'w') as file: 
		file.write(f'Name: {file_name}\n')
		file.write(f'Source: \n')
		file.write(f'Command: {command}\n')
		file.write(f'Logic: jp\n')
		file.write(f'Author: Auto generator\n')
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