Extract and Delta Seurm Component Readings
==========================================
A script to extract and associate serum component data from disparate files.


About
-----
For Dr Š.'s thesis project

Setup
-----

1. make sure python2.7 is installed and runs from the command line
2. cd into the directory where you saved extract.py and type
4. python extract.py help

That should get you started.

Preferably your data files are in the same directory, but it should 
work with full DOS paths.

Issues
------

There's issues with the data this produces.  This version
follows your algorithm exactly for each patient

1. top ocena row is your baseline
2. first kontronlni row # smaller than the ocena baseline row # is the
baseline date
3. closest kontrolni date past X days  is the row # you want
4. the first row # larger than that in ocena has the rating you want

Right now these are only positive deltas: readings on or past the
number of days you specify.

For various reasons some patients won't match at all.  Either only one
ocena, or no match between patients with ocena and patients in
kontrolni. These are excluded from the CSV (but I could include just
the baselines if you need them).  The script prints a report on
discrepancies to STDOUT

Other Issues
------------

Sometimes this procedure will end up selecting the exact same rating.
That's not a year in the future, it's the same day.  One of the
columns in the csv is 'delta from delta'.  That means if you told the
script you want the closest rating after 365 days out, 'delta from
delta' is how many days past a year it actually is.  Sort by that
column and you'll see only half of these results are within a year of
that.

And that's not counting how many days from the kontrolni entry the
next ocena actually was.  None of these line numbers actually match
between the two files. Are you sure the process that produced them has
any relation?

I mean.  This does what you asked, and produces numbers the way you
asked for them.  But just because it spits them out it doesn't mean
they're real.

