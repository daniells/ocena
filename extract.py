#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, re, csv
#function to compare dates 
from datetime import datetime
def daysBetween(d1, d2): d1 = datetime.strptime(d1, "%d.%m.%Y");d2 = datetime.strptime(d2, "%d.%m.%Y");return (d2 - d1).days
# for debugging
import pprint; pp = pprint.PrettyPrinter(indent=1)

# User help
# script_name = re.sub(r'^[[\./]', '', sys.argv[0])
script_name = 'extract.py'
usage_string = """Usage:  
	python """+script_name+""" <control file> <ratings file> <delta> [<output filename>]
		
	where:
		<control file> is your file containing lab measurement dates
		<ratings file> is your file containing serum component values
		<delta> is the minimum number of days the second measurement should be later than
		<output filename> an optional filename.  
"""
help_prompt = """
Type
	python """+script_name+""" help
for more info.
"""
help_string = usage_string + """ 
Examples:
	python """+script_name+""" kontrolni_pregledi.txt ocena_gf.txt 365

		Procuces the file 'ocena_gf_target_delta_365.csv' with a baseline rating and the rating 
		closest to 1 year from that. 

	python """+script_name+""" kontrolni_pregledi.txt ocena_gf.txt 365 my_filename.csv

		The same, but now it's 'my_filename.csv'

Function:   
	Prints a report and outputs a CSV file to the current directory. 

	This script assumes your files will be in essentially the same format as the two example files.
	
	If you get a python error, it's probably a problem with one of the files. 
	"""+script_name+""" tolerates some file format error but not a lot.  
	It silently ignores lines that don't look like: 
		• a valid DOS filepath
		• a valid serum measurment
		• a kontrol line with a valid date (some don't have these)

	If it breaks make sure the lines containg data are delimted the same as in the example files.

	Don't forget that your delta dates are (almost always) inexact.  It's just the date your delta 
	serum values are gaurenteed to be older than.  No fuzzy logic here.  The script implements the
	data extraction process exactly as specified. 
"""
# handle command line errors
if len(sys.argv) == 1: print usage_string + help_prompt; sys.exit(1)
elif sys.argv[1] == "help": print help_string  ; sys.exit(0)
elif len(sys.argv) < 4 or len(sys.argv) > 5 : print 'ERROR: Incorrect number of arguments. \n\n' + usage_string + help_prompt; sys.exit(1)
elif not re.match(r'\d{1,}', sys.argv[3]): print 'ERROR: <delta> must be an integer. \n\n' + usage_string + help_prompt; sys.exit(1)

delta = int(sys.argv[3])
output_filename = re.sub(r'\.[a-zA-Z]{3}', '_delta_' + str(delta) + '.csv', sys.argv[2]) if len(sys.argv) < 5 else sys.argv[4]



# open the files, make them processable arrays < 5 else 'output.csv'
file = open(sys.argv[2]); ratings_lines = file.readlines(); file.close() # read the file into a list where each list item is a line
file = open(sys.argv[1]); control_views = file.readlines(); file.close() # read the file into a list where each list item is a line

#regular expressions to process the lines in the arrays
filename_header_line_regex = re.compile(r'^([A-Z]{1}:.*\\(([a-zA-Z]*\d*[a-zA-Z]{1,})\d*\.[a-zA-Z]{3})).*') # 1 = full path, 2 = filename with ext, 3 patient id
rating_regex = re.compile(r'^\s*(\d*)\s*\w{1,}\s*(\w*)[\s=](\d*)') # 1 = rec num, 2 = GF val
control_views_regex = re.compile(r'^\s*(\d*)[\w\s]*\s(\d*\.\d*\.\d*)') # 1 = rec num, 2 date

# produce list index of header lines
def indexHeaders(lines):
	indices = []
	for i in range(len(lines)): 
		if filename_header_line_regex.search(lines[i]): indices.append(lines[i])
	return indices
# These functions clean the arrays of lines that don't have header or data rows.
def cleanRatingsLines(ratings_lines):
	temp = []
	for line in ratings_lines:
		if filename_header_line_regex.search(line) or rating_regex.search(line): temp.append(line)
	return temp
# remove irrelevant lines and records that are timestamped and not dated
def cleanControlviewsLines(control_views):
	temp = []
	for line in control_views:
		if filename_header_line_regex.search(line) or control_views_regex.search(line): temp.append(line)
	return temp
# combines all separated patient records from the kontrolni list, sorts them, returns a dictionary where key is patient id, value is a dictionary containing full path and record group 
def combineStructureSortControlviewRecords(control_views): 
	indices = []
	for i in range(len(control_views)): # get index of all the header lines
		if filename_header_line_regex.search(control_views[i]): 
			indices.append(i)
	patient_pools = {}
	for i in range(len(indices)): # mix all the data from multiple labs togeter for each patient
		search = filename_header_line_regex.search(control_views[indices[i]])
		pid = search.group(3)
		thisslice = control_views[indices[i]+1:indices[i+1]] if i != len(indices)-1 else control_views[indices[i]+1:len(control_views)]
		patient_pools[pid] = {
					'full header': search.group(1),
					'control views': patient_pools[pid]['control views'] + thisslice if pid in patient_pools else thisslice
		}
	def compare(a,b):# function to compare the values of the line numbers
		return int(control_views_regex.search(a).group(1))-int(control_views_regex.search(b).group(1))
	conjoined_control_views = []
	for pid in patient_pools: # now sort the entries by line number and build the new line list 
		patient_pools[pid]['control views'].sort(compare)
	return patient_pools
# takes the cleaned list of Ocena lines and outputs an object whose keys are patient ids and 
def gatherBaselines(ratings_lines, control_views):
	indices = []; data = {}
	for i in range(len(ratings_lines)):
		if filename_header_line_regex.search(ratings_lines[i]): indices.append(i)
	for i in range(len(indices)):
		header_search = filename_header_line_regex.search(ratings_lines[indices[i]])
		if header_search.group(3) in control_views: # if the patient in the baseline isn't in conrol_views we don't include that one
			baseline_search = rating_regex.search(ratings_lines[indices[i]+1])
			data[header_search.group(3)] = {
				'baseline line number':baseline_search.group(1),
				'baseline rating':baseline_search.group(3),
				'rating type':baseline_search.group(2),
				'rating filepath':header_search.group(1)
			}
	return data
# takes a dict of baselinse and a dict of control views. returns the dict of baslines with year added
def addBaselineYear(baselines, control_views):
	for patient in baselines:
		if patient in control_views:
			for i in range(len(control_views[patient]['control views'])):
				search = control_views_regex.search(control_views[patient]['control views'][i])
				if int(search.group(1)) > int(baselines[patient]['baseline line number']): 
					baselines[patient]['baseline date'] = control_views_regex.search(control_views[patient]['control views'][i-1]).group(2) if i > 0 else control_views_regex.search(control_views[patient]['control views'][i]).group(2)
					break
	temp = {} # with deltas values collected, remove those patients who didn't have a valid delta val 
	for patient in baselines.keys(): 
		if 'baseline date' in baselines[patient]: 
			temp[patient] = baselines[patient]
	return temp

def addDeltaDate(delta_days, baselines, control_views):
	for patient in baselines:
		baseline_date = baselines[patient]['baseline date']
		if patient in control_views:
			for i in range(len(control_views[patient]['control views'])):
				view_match = control_views_regex.search((control_views[patient]['control views'][i]))
				view_date = view_match.group(2)
				if daysBetween(baseline_date, view_date) >= delta_days:
					baselines[patient]['delta date'] =  view_date
					baselines[patient]['delta line number (kontrol)'] = view_match.group(1)
					baselines[patient]['delta from delta'] = str(daysBetween(baseline_date, view_date) - delta_days)
					break
	temp = {} # with deltas gathered, remove those patients who didn't have a valid delta 
	for patient in baselines.keys(): 
		if 'delta date' in baselines[patient]: 
			temp[patient] = baselines[patient]
	return temp

# structure cleaned ratings lines into an easily-iterable dictionary. 
def structureRatingsRecords(ratings_lines): 
	indices = []; ratings_data = {}
	for i in range(len(ratings_lines)): # get index of all the header lines
		if filename_header_line_regex.search(ratings_lines[i]): 
			indices.append(i)
	for i in range(len(indices)): # mix all the data from multiple labs togeter for each patient
		search = filename_header_line_regex.search(ratings_lines[indices[i]])
		pid = search.group(3)
		thisslice = ratings_lines[indices[i]+1:indices[i+1]] if i != len(indices)-1 else ratings_lines[indices[i]+1:len(control_views)]
		ratings_data[pid] = {
					'full header': search.group(1),
					'control views': ratings_data[pid]['control views'] + thisslice if pid in ratings_data else thisslice
		}
	return ratings_data
exact_line_number_matches = 0 #debugging
# add the newest rating gaurenteed to be one year out.  takes two dictionaries: the well-populated baselines(ratings) dict wih next year dates, and a structured ratings line dict (built just like the control_views dict)
def findNextDeltaReading(baselines, ratings_lines_dict): 
	for patient in baselines:
		for i in range(len(ratings_lines_dict[patient]['control views'])):
			search = rating_regex.search(ratings_lines_dict[patient]['control views'][i])
			if int(search.group(1)) >= int(baselines[patient]['delta line number (kontrol)']):
				baselines[patient]['delta rating'] = search.group(3)
				baselines[patient]['delta line number (rating)'] = search.group(1)
				#debugging
				#if int(search.group(1)) == int(baselines[patient]['delta line number (kontrol)']): exact_line_number_matches+=1
				break
	temp = {} # with deltas values collected, remove those patients who didn't have a valid delta val 
	for patient in baselines.keys(): 
		if 'delta rating' in baselines[patient]: 
			temp[patient] = baselines[patient]
	return temp

#def outputCSV(baselines, header_row, output_filename):




control_views = combineStructureSortControlviewRecords(cleanControlviewsLines(control_views))
baselines = gatherBaselines(cleanRatingsLines(ratings_lines),control_views)
baselines = addBaselineYear(baselines, control_views)
#pp.pprint(baselines) # for debugging
baselines = addDeltaDate(delta, baselines, control_views)
ratings_lines_dict =  structureRatingsRecords(cleanRatingsLines(ratings_lines))
baselines = findNextDeltaReading(baselines, ratings_lines_dict)

header_row = ['rating filepath','baseline rating','baseline date','delta rating','delta date', 'delta from delta','rating type']

#outputCSV(baselines, header_row, output_filename) # why can't I encapsulate the filewriter in a function?

with open(output_filename, 'wb') as csvfile:
	filewriter = csv.writer(csvfile, delimiter=',')
   	filewriter.writerow(['patient']+header_row)
   	for patient in baselines:
   		row = [patient] 
		for item in header_row:
			row.append(baselines[patient][item])
		filewriter.writerow(row)

# Print report
#print str(exact_line_number_matches) + 'exact line number matches'
print
print str(len(indexHeaders(ratings_lines)))+ ' total patients in ratings file.'
print str(len(ratings_lines_dict.keys())) + ' total patients with any match in the control file.'
print str(len(baselines.keys())) + ' patients with a second rating >= ' + str(delta) + ' days after the baseline measurement.'
print
print 'Output file written as ' + output_filename
print


#print sys.argv # debugging
#pp.pprint()

sys.exit(0) # exit with no error