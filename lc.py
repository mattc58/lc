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
import datetime
import treepredict

class LC(object):
	'''
	The main class we use for our exploration
	'''

	BAD_STATUS = ('Late (31-120 days)', 'Default', 'Performing Payment Plan', 'Charged Off')


	def __init__(self, training_fn='LoanStats.csv', testing_fn='InFundingStats.csv'):
		'''
		Create some of the lists we'll use
		'''
		self.training_data = []
		self.testing_data = []

		if training_fn:
			self.load_training_data(training_fn)
		if testing_fn:
			self.load_testing_data(testing_fn)

	def make_training_sample(self, k=.1):
		'''
		Make a sample of size k of the data. This is used in the decision tree.
		'''
		return (self.transform_data(random.sample(self.training_data, int(k * len(self.training_data)))))

	def transform_data(self, data):
		'''
		Transform a given dataset into something ready for the decision tree
		'''
		return [self.normalize_data(row) for row in data]

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
		ids = random.sample(range(len(self.training_data)), int(k * len(self.training_data)))
		sample = []
		transform_all = []
		for i, item in enumerate(self.training_data):
			row = self.normalize_data(item)
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
			guess = treepredict.classify(item[1:-1], tree)

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

	def run_tree(self, tree):
		'''
		Run the testing data against the tree
		'''
		# first get a sample to use for training and make a tree from it
		print "transforming test data"
		test_data = []
		for item in self.testing_data:
			test_data.append(self.normalize_data(item))

		print "running..."
		for item in test_data:
			guess = treepredict.classify(item[0:-1], tree)
			print "loan id=%s, results=%s" % (item[-1], guess)


	def compare_data(self):
		'''
		Compare the training and test data
		'''
		print "training data keys=%s" % self.training_data[0].keys()
		print "\n"
		print "test data keys=%s" % self.testing_data[0].keys()
		print "\n"

		print "in training, missing from test:"
		for col in self.training_data[0].keys():
			if col not in self.testing_data[0].keys():
				print col
		print "\n"
		print "in test, missing from training:"
		for col in self.testing_data[0].keys():
			if col not in self.training_data[0].keys():
				print col

	def normalize_data(self, item):
		'''
		Make the training and testing data normalized to each other such that we're
		training on data that exactly meets what we have to test.
		'''
		row = {}
		row.update(item)

		# make the status good or bad, for our purposes
		if 'Number of Lenders' not in row:
			if row['Status'] in self.BAD_STATUS:
				row['Status'] = 'BAD'
			else:
				row['Status'] = 'GOOD'
		else:
			row['Status'] = 'TEST'

		# calc monthly payment on testing based on amount requested
		for col in ('Application Date', 'Application Expiration Date', 'Issued Date', 
			'Remaining Principal Funded by Investors','Payments To Date (Funded by investors)','Remaining Principal ', 
			' Payments To Date','Screen Name', 'Code', 'Total Amount Funded', 'Number of Lenders', 'Expiration Date', 'APR', 'Amount Funded',
			'Amount Funded By Investors', 'Loan Description', 'Loan Title', 'City', 'State', 'Location', 'Education'):
			if col in row:
				del row[col]

		row['Loan Length'] = row['Loan Length'].replace(' months', '')

		# rename / combine
		if 'CREDIT Grade' in row:
			val = row.pop('CREDIT Grade')
			row['CREDIT Rating'] = val
		# if 'City' in row and 'State' in row:
		# 	location = '%s, %s' % (row.pop('City'), row.pop('State'))
			# row['Location'] = location
		if 'Monthly PAYMENT' not in row:
			# calc the monthly payment for the testing data
			principal = float(row.get('Amount Requested', '0.0'))
			months = int(row['Loan Length'])
			rate = float(row['Interest Rate'].replace('%', '')) / 100.0
			# interest = principal * annual rate * # years
			interest = principal * rate * (months / 12.0)
			# mp = principal + interest / # months
			row['Monthly PAYMENT'] = round(((principal + interest) / float(months)), 2)
		ecl = datetime.datetime.strptime(row.pop('Earliest CREDIT Line'), '%Y-%m-%d')
		row['Credit Line Age'] = ((datetime.datetime.now() - ecl).days) / 365


		# convert numeric values
		for k, v in row.items():
			try:
				row[k] = int(v)
			except ValueError:
				if '%' in v:
					v = v.replace('%', '')
					has_percent = True
				else:
					has_percent = False
				try:
					row[k] = float(v)
				except ValueError:
					try:
						json.dumps(v)
					except UnicodeDecodeError:
						row[k] = v.decode('latin-1')
					continue
				if has_percent:
					row[k] /= 100.0

		# handle employment
		# set(['5 years', '4 years', '10+ years', 'n/a', '6 years', '9 years', '8 years', '3 years', '2 years', '< 1 year', '1 year', '7 years'])
		e = row['Employment Length'].replace(' years', '')
		e = e.replace(' year', '')
		e = e.replace('n/a', '0')
		e = e.replace('< 1', '0.5')
		e = e.replace('10+', '10.0')
		row['Employment Length'] = e

		# finally change some of financial figures to / 2500 to give us some more consistent bands
		for col in ('Amount Requested','Amount Funded By Investors','Total Amount Funded'):
			if col in row:
				row[col] = int(row[col]) / 2500

		# finally turn into a list and put the Loan ID at the front and Status at the end
		cols = sorted(row.keys())
		cols.remove('Loan ID')
		cols.insert(0, 'Loan ID')
		if 'Status' in cols:
			cols.remove('Status')
			cols.append('Status')
		return [row[col] for col in cols]


	def load_training_data(self, file_name):
		'''
		Load the data from file_name and make the all list
		'''
		with open(file_name) as f:
			print "loading from %s..." % file_name
			dr = csv.DictReader(f)
			for line in dr:
				# skip lines that have the older credit policy
				if not line.get('Status') or 'Does not meet the current credit policy' in line.get('Status'):
					continue

				self.training_data.append(line)
	
	def load_testing_data(self, file_name):
		'''
		Load the data from file_name and make the testing list
		'''
		with open(file_name) as f:
			print "loading from %s..." % file_name
			dr = csv.DictReader(f)
			for line in dr:
				# skip lines that have the older credit policy
				if not line.get('Status') or 'Does not meet the current credit policy' in line.get('Status'):
					continue

				# we need employment length and term
				if 'Employment Length' not in line:
					continue
				# handle term
				if 'Loan Length' not in line:
					continue

				self.testing_data.append(line)
	

if __name__ == '__main__':
	lc = LC()
	lc.load_data(sys.argv[0])
