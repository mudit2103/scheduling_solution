import csv
import logging
import pprint 
import cvxpy as cvx
import numpy as np
import math
from collections import defaultdict

# Configuration parameters.
FILENAME = "tmp.csv"
LOGGING_FILENAME = "scheduling.log"
WEIGHTS = {1: 1, 2: 4, 3: 100, 4: 10000}

logging.basicConfig(filename=LOGGING_FILENAME, level=logging.DEBUG)

preferences_by_assignment = defaultdict(list)
preferences_by_persons = defaultdict(list)

# Process provided CSV.
with open(FILENAME, 'r') as csvfile:
    csvreader = csv.reader(csvfile)

    # Skip first element because it is the diagonal header.
    persons = next(csvreader)[1:]  
    logging.debug("Persons are {}".format(str(persons)))

    for row in csvreader:
        logging.debug("Working on row {}".format(str(row)))
        assignment = row[0]
        preferences = row[1:]
        for i, preference in enumerate(preferences):
            person = persons[i]
            preference = WEIGHTS[int(preference)]  # Negatively weigh the preference as specified in WEIGHTS.
            preferences_by_assignment[assignment].append((person, preference))
            preferences_by_persons[person].append((assignment, preference))    


cost = 0
variables_by_persons = defaultdict(list)
constraints_by_persons = defaultdict(int)
constraints_by_assignment = defaultdict(int)

# Create variables and partial constraints for assignment x person cross product.
logging.debug("Creating variables")
for person, item in preferences_by_persons.items():
    for assignment, preference in item:
        variable = cvx.Bool()
        variables_by_persons[person].append((preference, assignment, variable))
        
        cost += preference * variable

        constraints_by_persons[person] += variable
        constraints_by_assignment[assignment] += variable

# Constraint that each person must be assigned one assignment.
persons_constraint = list({k: v == 1 for (k, v) in constraints_by_persons.items()}.values())
# Constraint that each assignment must have only one person.
assignments_constraint = list({k: v == 1 for (k, v) in constraints_by_assignment.items()}.values())
logging.debug("Created constraints.")

# Perform CVX Magic.
obj = cvx.Minimize(cost)
prob = cvx.Problem(obj, persons_constraint+assignments_constraint)
logging.debug("Using CVX to solve")
prob.solve()

logging.info("Problem Value {}".format(prob.value))
if (prob.status != "optimal"):
    logging.warning("Problem status is not optimal but is instead {}".format(prob.status))

final_assignments = dict()
# Figure out the final assignments by checking which variables were 1.
for person, items in variables_by_persons.items():
    for preference, assignment, variable in items:
        if math.isclose(variable.value, 1):
            final_assignments[person] = (assignment, preference)


# Write out the final assignments
with open("assignments.csv", "w+") as csvfile:
    logging.debug("Writing to output file.")
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(["Person", "Assignment", "Preference"])
    for person, item in final_assignments.items():
        assignment, preference = item
        csvwriter.writerow([person, assignment, preference])
        logging.info("Made assignment: {}, {}, {}".format(person, assignment, preference))
