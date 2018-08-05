import csv
import logging
import pprint 
import cvxpy as cvx
import numpy as np
import math
import pandas as pd
from collections import defaultdict
import argparse


# Configuration parameters.
FILENAME = "tmp.csv"
OUTPUTFILE = "assignments.csv"
LOGGING_FILENAME = "scheduling.log"
WEIGHTS = {1: 1, 2: 4, 3: 100, 4: 10000}
WEIGHTS_TO_PREF = {1: 1, 4: 2, 100: 3, 10000: 4}
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

def parse_csv(filename, no_custom_counts=False, weights=WEIGHTS, ):
    # Process provided CSV.
    preferences_by_assignment = defaultdict(list)
    preferences_by_persons = defaultdict(list)
    counts_by_assignment = dict()
    counts_by_persons = dict()

    df = pd.read_csv(filename)
    assignments = make_unique(df.Assignment)
    # Skip first element because it is the diagonal header.
    offset = 1 if no_custom_counts else 2
    persons = make_unique(df.columns.values.tolist()[offset:])
    if no_custom_counts:
        counts_by_persons = {person: 1 for person in persons}
    else:
        counts = df[0:1].values.tolist()[0][offset:]
        counts_by_persons = {person: int(count) for person, count in zip(persons, counts)}

    for index, row in df.iterrows():
        if (index == 0): 
            continue
        logging.debug("Working on row {}".format(str(row)))
        assignment = assignments[index]
        if no_custom_counts:
            counts_by_assignment[assignment] = 1
        else:
            count = row[1]
            counts_by_assignment[assignment] = int(count) 

        preferences = row[offset:]
        for i, preference in enumerate(preferences):
            person = persons[i]
            preference = weights[int(preference)]  # Negatively weigh the preference as specified in WEIGHTS.
            preferences_by_assignment[assignment].append((person, preference))
            preferences_by_persons[person].append((assignment, preference))

    return counts_by_persons, counts_by_assignment, preferences_by_persons, preferences_by_assignment

def str_bounds_expr(left, bounds, right):
    if bounds == "equal":
        return left == right
    elif bounds == "lower":
        return left >= right
    elif bounds == "upper":
        return right >= left
    else:
        raise NotImplementedError("Bounds must be {equal, lower, upper}")      

def create_ilp(preferences_by_persons, counts_by_persons, counts_by_assignment, bounds):
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
    persons_constraint = list({k: str_bounds_expr(v, bounds, counts_by_persons[k]) for 
                             (k, v) in constraints_by_persons.items()}.values())
    # Constraint that each assignment must have only one person.
    assignments_constraint = list({k: str_bounds_expr(v, bounds, counts_by_assignment[k]) for 
                                 (k, v) in constraints_by_assignment.items()}.values())
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
    final_assignments = defaultdict(list)
    # Figure out the final assignments by checking which variables were 1.
    for person, items in variables_by_persons.items():
        for preference, assignment, variable in items:
            if math.isclose(variable.value, 1):
                final_assignments[person].append((assignment, preference))
    return final_assignments

def write_final_assignments(final_assignments, output_file=OUTPUTFILE):
    # Write out the final assignments
    with open(output_file, "w+") as csvfile:
        logging.debug("Writing to output file.")
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["Person", "Assignment", "Preference"])
        for person, items in final_assignments.items():
            for assignment, weight in items:
                csvwriter.writerow([person, assignment, WEIGHTS_TO_PREF[weight]])
                logging.info("Made assignment: {}, {}, {}".format(person, assignment, WEIGHTS_TO_PREF[weight]))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, help='Input CSV file.')
    parser.add_argument('output', type=str, help='Output file name.')

    group_counts = parser.add_mutually_exclusive_group(required=False)
    group_counts.add_argument('--no-custom-counts', action='store_true', help='Indicates that the input CSV does not have count columns / rows, and simply assumes that each count is 1.')

    group_bounds = parser.add_mutually_exclusive_group(required=False)
    group_bounds.add_argument('--bounds', choices=['lower','upper','equal'], help='Use this flag to specify that the provided counts in the CSV are merely a {lower,upper,tight} bound, and {more,fewer,exactly} persons than provided in the counts can be assigned if required. Default assumes that the requirement is tight.')
    args = parser.parse_args()
    bounds = args.bounds if args.bounds else 'equal'

    counts_by_persons, counts_by_assignment, preferences_by_persons, preferences_by_assignment = parse_csv(args.input, args.no_custom_counts)
    variables_by_persons, cost, persons_constraint, assignments_constraint = create_ilp(preferences_by_persons, counts_by_persons, counts_by_assignment, bounds)
    solve_ilp(cost, persons_constraint, assignments_constraint)
    final_assignments = set_final_assignments(variables_by_persons)
    write_final_assignments(final_assignments, args.output)
