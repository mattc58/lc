import csv
import os
import sys

data = []
good = []
bad = []

def main(fn=None):
	global data, good, bad

	with open(fn or sys.argv[0]) as f:
		dr = csv.DictReader(f)
		for line in dr:
			# skip lines that have the older credit policy
			if not line.get('Status') or 'Does not meet the current credit policy' in line.get('Status'):
				continue

			# handle employment
			# set(['5 years', '4 years', '10+ years', 'n/a', '6 years', '9 years', '8 years', '3 years', '2 years', '< 1 year', '1 year', '7 years'])
			if 'Employment Length' not in line:
				continue
			e = line['Employment Length'].replace(' years', '')
			e = e.replace(' year', '')
			e = e.replace('n/a', '0')
			e = e.replace('< 1', '0.5')
			e = e.replace('10+', '10.0')
			line['Employment Length'] = e

			# handle term
			if 'Loan Length' not in line:
				continue
			line['Loan Length'] = line['Loan Length'].replace(' months', '')

			# convert numeric values
			for k, v in line.items():
				try:
					line[k] = int(v)
				except ValueError:
					if '%' in v:
						v = v.replace('%', '')
						has_percent = True
					else:
						has_percent = False
					try:
						line[k] = float(v)
					except ValueError:
						continue
					if has_percent:
						line[k] /= 100.0
				except:
					continue

			data.append(line)
			if line.get('Status') in ('Late (31-120 days)', 'Default', 'Performing Payment Plan', 'Charged Off'):
				bad.append(line)
			else:
				good.append(line)
	

if __name__ == '__main__':
	main()