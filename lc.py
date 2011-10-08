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


	def __init__(self, training_fn=None, testing_fn=None):
		'''
		Create some of the lists we'll use
		'''
		self.all = []
		self.good = []
		self.bad = []

		if training_fn:
			self.load_data(training_fn)

	def make_training_sample(self, k=.1):
		'''
		Make a sample of size k of the data. This is used in the decision tree.
		'''
		return (self.transform_data(random.sample(self.all, int(k * len(self.all)))))

	def transform_row(self, row):
		'''
		Transform a given row into something that's ready for the decision tree
		'''
		# make the status good or bad, for our purposes
		if row['Status'] in self.BAD_STATUS:
			row['Status'] = 'BAD'
		else:
			row['Status'] = 'GOOD'
		
		# remove columns we don't need
		for col in ('Loan ID', 'Application Date', 'Application Expiration Date', 'Issued Date', 
			'Remaining Principal Funded by Investors','Payments To Date (Funded by investors)','Remaining Principal ', 
			' Payments To Date','Screen Name', 'Code'):
			if col in row:
				del row[col]

		# finally change some of financial figures to / 2500 to give us some more consistent bands
		for col in ('Amount Requested','Amount Funded By Investors','Total Amount Funded'):
			row[col] = int(row[col]) / 2500

		# finally turn into a list and put the Status column at the end
		cols = sorted(row.keys())
		cols.remove('Status')
		cols.append('Status')
		return [row[col] for col in cols]


	def transform_data(self, data):
		'''
		Transform a given dataset into something ready for the decision tree
		'''
		return [self.transform_row(row) for row in data]

	def make_tree(self, data):
		'''
		Make a decision tree with the supplied data
		'''
		return treepredict.buildtree(data)

	def test_tree(self, k=.2):
		'''
		Conduct a test of decision trees
		'''
		# first get a sample to use for training and make a tree from it
		print "making sample and training tree..."
		ids = random.sample(range(len(self.all)), int(k * len(self.all)))
		sample = []
		transform_all = []
		for i, item in enumerate(self.all):
			row = self.transform_row(item)
			if i in ids:
				sample.append(row)
			else:
				transform_all.append(row)

		tree = self.make_tree(sample)

		# now go through the rest of all, seeing how it does
		num_false_positive = num_false_negative = num_right = 0

		print "testing..."
		for item in transform_all:
			status = item[-1]
			guess = treepredict.classify(item[0:-1], tree)

			# if we're right, record. if not, determine if false negative (ok) or false positive (bad)
			if status in guess:
				num_right += 1
			else:
				if status == 'GOOD':
					num_false_negative += 1
				else:
					num_false_positive += 1

		# display results
		num_processed = len(transform_all)
		print "sample size=%d, testing size=%d" % (len(sample), num_processed)
		print "%.2f correct" % ((float(num_right) / float(num_processed)) * 100.0)
		print "%.2f false negatives (kinda ok)" % ((float(num_false_negative) / float(num_processed)) * 100.0)
		print "%.2f false positives (bad)" % ((float(num_false_positive) / float(num_processed)) * 100.0)


	def load_data(self, file_name):
		'''
		Load the data from file_name and make the all, good, and bad lists
		'''
		with open(file_name) as f:
			print "loading from %s..." % file_name
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
