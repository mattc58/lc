"""
lc.py - Python code to do some machine learning goodness with Lending Club data
 
Library Maintainer:  
    Matt Culbreth
    mattculbreth@gmail.com
    http://github.com/mattc58/lc 
#####################################################################
 
This work is distributed under an MIT License: 
http://www.opensource.org/licenses/mit-license.php
 
The MIT License
 
Copyright (c) 2011 Matt Culbreth

Permission is hereby granted, free of charge, to any person obtaining a copy 
of this software and associated documentation files (the "Software"), to deal 
in the Software without restriction, including without limitation the rights to 
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of 
the Software, and to permit persons to whom the Software is furnished to do so, 
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 
#####################################################################
 
Hello, this is an open source Python library that lets you do some interesting things 
with Lending Club data.
    
USAGE:
 
    import lc
    
    
"""
import csv
import os
import sys
import json
import random
import treepredict

class LC(object):
	'''
	The main class we use for our exploration
	'''

	BAD_STATUS = ('Late (31-120 days)', 'Default', 'Performing Payment Plan', 'Charged Off')


	def __init__(self):
		'''
		Create some of the lists we'll use
		'''
		self.all = []
		self.good = []
		self.bad = []

	def make_training_sample(self, k=.1):
		'''
		Make a sample of size k of the data. This is used in the decision tree.
		'''
		return (self.transform_data(random.sample(self.all, int(k * len(self.all)))))

	def transform_data(self, data):
		'''
		Transform a given dataset into something ready for the decision tree
		'''
		for item in data:
			if item['Status'] in self.BAD_STATUS:
				item['Status'] = 'BAD'
			else:
				item['Status'] = 'GOOD'

		cols = sorted(data[0].keys())
		cols.remove('Status')
		cols.append('Status')
		return [[item[col] for col in cols] for item in data]

	def make_tree(self, data):
		'''
		Make a decision tree with the supplied data
		'''
		return treepredict.buildtree(data)

	def load_data(self, file_name):
		'''
		Load the data from file_name and make the all, good, and bad lists
		'''
		with open(file_name) as f:
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
							try:
								json.dumps(v)
							except UnicodeDecodeError:
								line[k] = v.decode('latin-1')
							continue
						if has_percent:
							line[k] /= 100.0


				self.all.append(line)
				if line.get('Status') in self.BAD_STATUS:
					self.bad.append(line)
				else:
					self.good.append(line)
	

if __name__ == '__main__':
	lc = LC()
	lc.load_data(sys.argv[0])
