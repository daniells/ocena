#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, re, csv
#function to compare dates 
from datetime import datetime
def days_between(d1, d2):
    d1 = datetime.strptime(d1, "%d.%m.%Y")
    d2 = datetime.strptime(d2, "%d.%m.%Y")
    return (d2 - d1).days



# for debugging
import pprint 
pp = pprint.PrettyPrinter(indent=1)

# open the files, make them processables arrays
file = open('ocena_gf.txt')
ocena_lines = file.readlines() # read the file into a list where each list item is a line
file.close()
file = open('kontrolni_pregledi conjoined.txt')
kontrolni_lines = file.readlines() # read the file into a list where each list item is a line
file.close()


#regular expressions to process the lines in the arrays
filename_header_line_regex = re.compile(r'^(D:.*\\([\w\d]*)\.txt).*') # this regex finds filepath lines (i.e. 'D:\2019_clanki\ukc\text\d017sadri.txt') and returns the filename in a (captured) group 
ocena_line_regex = re.compile(r'^\s*(\d*)\s*[Oo]cena\s*GF[\s=](\d*)') # 1 = rec num, 2 = GF val
kontrolni_line_regex = re.compile(r'^\s*(\d*)[\w\s]*\s(\d*)\.(\d*)\.(\d*)') # three groups for date components: 1 = rec num, 2 = day, 3 = mo, 4 = yr

data = {} # a dictionary to hold our data (it will be nested) 

''' 1)  Under a path/file name in ocena_gf.txt (for example d002muraus.txt), read the 
	first (baseline) value measurement (Ocena GF=7) on the list under that path/file name 
'''

for i in range(len(ocena_lines)):
	line = filename_header_line_regex.search(ocena_lines[i])
	if line:
		nextdataline = ocena_line_regex.search(ocena_lines[i+1])
		data[line.group(2)] = {
			'baseline':{
				'filepath':line.group(1),
				'record number':int(nextdataline.group(1)),
				'baseline value':int(nextdataline.group(2))
			}
		}
#

# now each entry will be in the form
# 	'd002muraus': {
#
#					'baseline': {
#							'GF value': 7, 
#							'first record number': 65
#							}
#						}

''' 2) Go to  kontrolni_pregledi.txt and find the first line number that is SMALLER 
    than the first one in ocena_gf.txt- in this case we have line 65, so we need 
    to take line 54 in kontrolni_pregledi.txtand print the date next to it (29.09.2010) 
    in the same row with the value measurement from   ocena_gf.txt (Ocena GF=7). 
'''

#first we get the indexes of the list-items(lines) in [kontrolni_pregledi.txt] that are headers
header_indicies = []
for i in range(len(kontrolni_lines)):
	if filename_header_line_regex.search(kontrolni_lines[i]):
		header_indicies.append(i)


# now that we have index positions of all the header lines in the list we can step through 
# and get the value closest to the baseline in ocena_gf.txt 
matches_count =  0 # for debugging 
for i in range(len(header_indicies)):
	# patient ID (basename of the file)
	patient =  filename_header_line_regex.search(kontrolni_lines[header_indicies[i]]).group(2)
	# some records in kontrolni_pregledi.txt don't have a match in ocena_gf.txt, so I'm ignoring those
	if patient in data.keys():
		matches_count = matches_count+1 # for debugging
		line_group = []
		# slice out the lines under each header so we can scan them
		if i != len(header_indicies): # if not at the last header-line index
			# slice the list of kontrolni_pregledi.txt's lines between this header line and the next header line
			line_group = kontrolni_lines[header_indicies[i]+1:header_indicies[i+1]-1]
		else:
			# slice the list of kontrolni_pregledi.txt's lines between this header line and kontrolni_pregledi.txt's last line
			line_group = kontrolni_lines[header_indicies[i]+1:len(kontrolni_lines)-2]
		# now loop through the line_group finding the date of the first line that is SMALLER than the rating baseline
		first_record_number_from_ocena = data[patient]['baseline']['record number']
	
		"""
		3. Repeat this for all path/file names and if possible generate a delimited text file 
		   containing individual names (path/file name) in the column on the left, followed by 
		   baseline measurements, followed by dates, or the other way around, the important 
		   thing is that each individual gets a row
		"""

		# if the last line in the corresponding kontrolni group is still lower than the baseline's, use that 
		#  this also handles specia cases where there is only one kontrolni record for the paient
		if int(kontrolni_line_regex.search(line_group[-1]).group(1)) < first_record_number_from_ocena:
				this_line_regex_search = kontrolni_line_regex.search(line_group[-1])
				date = str(this_line_regex_search.group(2))+"."+str(this_line_regex_search.group(3))+"."+str(this_line_regex_search.group(4)) if this_line_regex_search else False
				data[patient]['baseline']['date'] = date
        # if this edge case didn't apply, actually search the list
		else: 
			for j in range(len(line_group)):
				this_line_regex_search = kontrolni_line_regex.search(line_group[j])
				# some of these fucking things have a time string instead of a date string. this IF test skips that bad record
				if this_line_regex_search:
					this_kontrolni_record_num = int(this_line_regex_search.group(1)) 
					if j > 0 and this_kontrolni_record_num >= first_record_number_from_ocena: #ignore the first line, compare record number
						this_line_regex_search = kontrolni_line_regex.search(line_group[j-1])
						date = str(this_line_regex_search.group(2))+"."+str(this_line_regex_search.group(3))+"."+str(this_line_regex_search.group(4)) if this_line_regex_search else False
						data[patient]['baseline']['date'] = date
						break
		"""
			Now take the date that is closest to one year from your original date - 
			
			let's take d003vamberger.txt as an example because d002muraus.txt has only one value - in this 
			case we would take ocena_gf.txt: first value measurement 
			Ocena GF=7, line number 603, kontrolni_pregledi.txt: first smaller number than 603 is 585, 
			that line has the date 18.05.2009. 
		"""
		# get the first smaller record number than the baseline reading's
		for j in range(len(line_group)):
			this_line_regex_search = kontrolni_line_regex.search(line_group[j])
			# some of these fucking things have a time string instead of a date string 
			# this IF test skips that bad record
			if this_line_regex_search:
				#print str(data[patient]['baseline']['record number']) + "  " + this_line_regex_search.group(1)
				if int(data[patient]['baseline']['record number']) > int(this_line_regex_search.group(1)) and len(line_group) > 1:  
					last_line_regex_search = kontrolni_line_regex.search(line_group[j-1])
					data[patient]['baseline']['previous record number'] = last_line_regex_search.group(1)
					data[patient]['baseline']['previous record date'] = str(this_line_regex_search.group(2))+"."+str(this_line_regex_search.group(3))+"."+str(this_line_regex_search.group(4))
					break
		"""
        	Closest to one year later would be 10.05.2010, which 
			is line number 782. 
		"""
		# This is for indexing the one-year-out reading we'll collect later from Ocena.txt
		for j in range(len(line_group)):
			this_line_regex_search = kontrolni_line_regex.search(line_group[j])
			# some of these fucking things have a time string instead of a date string 
			# this IF test skips that bad record
			if 'date' in data[patient]['baseline']:
				date = str(this_line_regex_search.group(2))+"."+str(this_line_regex_search.group(3))+"."+str(this_line_regex_search.group(4)) if this_line_regex_search else False
				if date and 'previous record date' in data[patient]['baseline']: # if this line has a date and the corresponding record has a date
					days_delta = days_between(data[patient]['baseline']['date'], date)
					if days_delta >= 365: # if this date is a year or more older
						#print "okay" + "  " + str(this_line_regex_search.group(1))
						data[patient]['next year'] = {}
						data[patient]['next year']['next year date'] = date
						data[patient]['next year']['next year record num'] = this_line_regex_search.group(1)
						break

print str(matches_count) + ' patient_id matches between kontrolni_pregledi and ocena_gf.txt'

# Clean {data} of all records that have no baseline date
cleaned = 0
for patient in data.keys():
	if 'date' not in data[patient]['baseline']: 
		del data[patient]
		cleaned = cleaned +1
print str(cleaned) + ' records have no baseline date' 


# Clean {data} of all records that have no determinable next-year date
cleaned = 0
for patient in data.keys():
	if 'next year' not in data[patient]: 
		del data[patient]
		cleaned = cleaned +1
print str(cleaned) + ' records have no determinable next-year date' 



'''
	And now we need to go back to ocena_gf.txt and fetch the value 
	measurement next to the first number LARGER than the one at the date, in this case 791>782, 
	which would be value measurement Ocena GF=6.
'''
header_indicies = []
for i in range(len(ocena_lines)):
	if filename_header_line_regex.search(ocena_lines[i]):
		header_indicies.append(i)


# Now that we have header indcies we can step through and get the reading closest to one year after the baseline 
for i in range(len(header_indicies)):
	patient =  filename_header_line_regex.search(ocena_lines[header_indicies[i]]).group(2)
	line_group = []
	# slice out the lines under each header so we can scan them
	if i != len(header_indicies)-1: # if not at the last header-line index
		# slice the list of ocena.txt's lines between this header line and the next header lines
		line_group = ocena_lines[header_indicies[i]+1:header_indicies[i+1]-1]
	else:
		# slice the list of ocena.txt's lines between this header line and ocena.txt's last line
		line_group = ocena_lines[header_indicies[i]+1:len(ocena_lines)-2]
	# now scan the line group
	for j in range(len(line_group)):
		#print str(line_group[j])
		if patient in data:
			this_line_regex_search = ocena_line_regex.search(line_group[j])
			if int(this_line_regex_search.group(1)) > int(data[patient]['next year']['next year record num']):
				data[patient]['next year']['next year value'] = this_line_regex_search.group(2)
				break



## Now print the CSV file using our data object
with open('output.csv', 'wb') as csvfile:
    filewriter = csv.writer(csvfile, delimiter=',')
    filewriter.writerow(['name','filepath','baseline record number','baseline date','baseline measurment','next year record number','next year date','next year measurement'])
    for patient in data.keys():
    	if 'date' in data[patient]['baseline']:
    		if data[patient]['baseline']['date']:
    			if 'next year' in data[patient]:
    				filewriter.writerow([
									patient,
    								data[patient]['baseline']['filepath'],
    								data[patient]['baseline']['record number'],
									data[patient]['baseline']['date'], 
    				    			data[patient]['baseline']['baseline value'],
    				    			data[patient]['next year']['next year record num'],
    				    			data[patient]['next year']['next year date'],
    				    			data[patient]['next year']['next year value'] if 'next year value' in data[patient]['next year'] else ''
    				    			])
#pp.print(data) # for debugging


