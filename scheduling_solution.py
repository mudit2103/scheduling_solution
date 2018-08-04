import csv
import logging
import pprint 

from collections import defaultdict
logging.basicConfig(filename='scheduling.log',level=logging.DEBUG)

FILENAME = "tmp.csv"

preferences_by_assignment = defaultdict(list)
preferences_by_persons = defaultdict(list)

with open(FILENAME, 'r') as csvfile:
    csvreader = csv.reader(csvfile)

    # Skip first element because it is the diagonal header.
    persons = next(csvreader)[1:]  
    logging.debug("Persons are {}".format(str(persons)))

    for row in csvreader:
        assignment = row[0]
        preferences = row[1:]
        for i, preference in enumerate(preferences):
            person = persons[i]
            preferences_by_assignment[assignment].append((person, preference))
            preferences_by_persons[person].append((assignment, preference))    
