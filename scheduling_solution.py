import csv
import logging
import pprint 
import cvxpy as cvx
import numpy as np
import math
import pandas as pd
from collections import defaultdict

# Configuration parameters.
FILENAME = "tmp.csv"
OUTPUTFILE = "assignments.csv"
LOGGING_FILENAME = "scheduling.log"
WEIGHTS = {1: 1, 2: 4, 3: 100, 4: 10000}
logging.basicConfig(filename=LOGGING_FILENAME, level=logging.DEBUG)

def make_unique(lst):
    """This function takes a list of str items, and checks the list for 
    non-unique entries. If any non-unique entries are found, it replaces
     them by appending a _1, _2 under them to make them all unique."""
    counts = defaultdict(int)
    for item in lst:
        counts[item] += 1

    uniqified_lst = []
    for item in lst:
        if counts[item] > 1:
            # Start re-labeling item from the back.
            new_item = str(item) + "_" + str(counts[item])
            logging.warning("Found duplicate items. Rewriting {} to {}".format(item, new_item))
            uniqified_lst.append(new_item)
            counts[item] -= 1  # Decrement counts for proper future relabeling
        else:
            uniqified_lst.append(item)
    
    return uniqified_lst

def parse_csv(filename, weights=WEIGHTS):
    # Process provided CSV.
    preferences_by_assignment = defaultdict(list)
    preferences_by_persons = defaultdict(list)

    csvreader = pd.read_csv(filename)
    assignments = make_unique(csvreader.Assignment)
    # Skip first element because it is the diagonal header.
    persons = make_unique(csvreader.columns.values.tolist()[1:])

    for index, row in csvreader.iterrows():
        logging.debug("Working on row {}".format(str(row)))
        assignment = assignments[index]
        preferences = row[1:]
        for i, preference in enumerate(preferences):
            person = persons[i]
            preference = weights[int(preference)]  # Negatively weigh the preference as specified in WEIGHTS.
            preferences_by_assignment[assignment].append((person, preference))
            preferences_by_persons[person].append((assignment, preference))

    return preferences_by_persons, preferences_by_assignment
      
def create_ilp(preferences_by_persons):
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
    return variables_by_persons, cost, persons_constraint, assignments_constraint

def solve_ilp(cost, persons_constraint, assignments_constraint):
    # Perform CVX Magic.
    obj = cvx.Minimize(cost)
    prob = cvx.Problem(obj, persons_constraint+assignments_constraint)
    logging.debug("Using CVX to solve")
    prob.solve()

    logging.info("Problem Value {}".format(prob.value))
    if (prob.status != "optimal"):
        logging.warning("Problem status is not optimal but is instead {}".format(prob.status))

def set_final_assignments(variables_by_persons):
    final_assignments = dict()
    # Figure out the final assignments by checking which variables were 1.
    for person, items in variables_by_persons.items():
        for preference, assignment, variable in items:
            if math.isclose(variable.value, 1):
                final_assignments[person] = (assignment, preference)
    return final_assignments

def write_final_assignments(final_assignments, output_file=OUTPUTFILE):
    # Write out the final assignments
    with open(output_file, "w+") as csvfile:
        logging.debug("Writing to output file.")
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["Person", "Assignment", "Preference"])
        for person, item in final_assignments.items():
            assignment, preference = item
            csvwriter.writerow([person, assignment, preference])
            logging.info("Made assignment: {}, {}, {}".format(person, assignment, preference))

if __name__ == "__main__":
    preferences_by_persons, preferences_by_assignment = parse_csv(FILENAME)
    variables_by_persons, cost, persons_constraint, assignments_constraint = create_ilp(preferences_by_persons)
    solve_ilp(cost, persons_constraint, assignments_constraint)
    final_assignments = set_final_assignments(variables_by_persons)
    write_final_assignments(final_assignments)
