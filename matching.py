from scipy.optimize import linear_sum_assignment
import csv
import numpy as np
import argparse

def _parse_no_cc(reader):
    """Takes in a csv reader object. 
    Parses the csv according to a csv that does not have
    any custom counts.
    """
    cost_matrix, slots, entities = [], [], []
    for i, row in enumerate(reader):
        
        if i == 0:
            # First row, 2nd column onwards are the slots.
            slots = row[1:] 
        else:
            cost_matrix.append([int(x) for x in row[1:]])

            # First column contains the entities.
            entities.append(row[0])
    return cost_matrix, slots, entities

def _parse_cc(reader):
    """Takes in a csv reader object with custom counts 
    for each slot and each entity. Parses it accordingly.
    """
    cost_matrix, slots, entities = [], [], []

    slot_names = []
    slot_counts = []

    for i, row in enumerate(reader):
        if i == 0:
            # First row, 3nd column onwards are the slot names,
            # but, there are counts present, and the slots
            # list needs multiple copies of each slot name.
            slot_names = row[2:] 
        elif i == 1:
            # Second row contains the counts for the slots.
            # slots is now populated appropriately.
            slot_counts = [int(x) for x in row[2:]]
            
            for n, c in zip(slot_names, slot_counts):
                slots.extend([n] * c)

        else:
            # Third row onwards contains the costs.
            entity_name = row[0]
            entity_count = int(row[1])

            entities.extend([entity_name] * entity_count)

            # Initialize the row for this entity to be empty.
            cost_row = []
            for j in range(len(row[2:])):
                # Walk through the row, and fill in cost_row. 
                # Note that the number of copies of the slots needs to be
                # taken care of appropriately.
                slot_count = slot_counts[j]
                cost = int(row[j + 2])

                cost_row.extend([cost] * slot_count)

            # Create 'entity_count' duplicate rows in the cost matrix.    
            for i in range(entity_count):
                cost_matrix.append(cost_row)
                    
    return cost_matrix, slots, entities





def parse_csv(filename, no_custom_counts):
    """
    Takes in a the file name  CSV of the following format:

    - cell A1 = 'Assignment'
    - cell A2 = 'Counts'
    - cells A3-A[#] being the names of the entities that require assignments. 
    For instance, "Section 1", "Section 2", etc. 
    - cell B1 = 'Counts'
    - leave cell B2 blank
    - cells B3-B[#] being the number of assignments to be made 
    to the corresponding entity in A3-A[#]. For instance, Section 2 
    requires 3 persons assigned to it.
    - cell C1 should contain the name of a person (who needs to be 
    assigned an entity)
    - cell C2 should contain the count of entities to be assigned to this person
    - cells C3-C[#] should contain the preferences of the person to be assigned 
    to the corresponding entity. The prefernce must be {1, 2, 3, 4}, where 1 is 
    "most preferred" and 4 is "cannot make it at all."
    - follow the same thing for more persons as column C. 

    Returns 
    - cost: a 2D cost matrix. Each column corresponds to a particular 'slot', and
    each row corresponds to a particular 'entity to be assigned a slot'.
    - slots: ordered list of 'slots'. The length of this list is the number of columns
    in the cost matrix.
    - entities: ordered list of 'entities'. The length of this list is the number of
    rows in the cost matrix. 

    Note that len(slots) and len(entities) may not match len(rows) and len(cols) in the
    provided csv if the csv has custom counts.
    """
    cost_matrix = []
    slots = []
    entities = []
    with open(filename, 'r') as csvfile:
        reader = csv.reader(csvfile)

        if no_custom_counts:
            cost_matrix, slots, entities = _parse_no_cc(reader)
        else:
            cost_matrix, slots, entities = _parse_cc(reader)

    return cost_matrix, slots, entities


def solve(cost_matrix, slots, entities):
    """
    Takes in a cost matrix, a list of slots, and a list of entities. 
    Rows in the cost matrix correspond to the entities, and columns
    correspond to slots.
    """
    assert len(slots) == len(cost_matrix[0])
    assert len(entities) == len(cost_matrix)

    cost_matrix = np.array(cost_matrix)
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    for row, col in zip(row_ind, col_ind):
        entity = entities[row]
        slot = slots[col]
        priority = cost_matrix[row][col]
        print("Person {} is assigned {} with priority {}".format(entity, slot, priority))

    return row_ind, col_ind

def write_output(output_file, cost_matrix, row_ind, col_ind, slots, entities):
    """Takes in the solved row and column indices. 
    Takes in the names of the slots and the entities. 
    Outputs the result to a csv.
    """
    with open(output_file, 'w') as csvfile:
        writer = csv.writer(csvfile)

        for row, col in zip(row_ind, col_ind):
            entity = entities[row]
            slot = slots[col]
            priority = cost_matrix[row][col]
            writer.writerow([entity, slot, priority])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
    A solution for scheduling hell! 

    Create a CSV with the following properties:
    - cell A1 = 'Assignment'
    - cell A2 = 'Counts'
    - cells A3-A[#] being the names of the entities that require assignments. 
    For instance, "Section 1", "Section 2", etc. 
    - cell B1 = 'Counts'
    - leave cell B2 blank
    - cells B3-B[#] being the number of assignments to be made 
    to the corresponding entity in A3-A[#]. For instance, Section 2 
    requires 3 persons assigned to it.
    - cell C1 should contain the name of a person (who needs to be 
    assigned an entity)
    - cell C2 should contain the count of entities to be assigned to this person
    - cells C3-C[#] should contain the preferences of the person to be assigned 
    to the corresponding entity. The prefernce must be {1, 2, 3, 4}, where 1 is 
    "most preferred" and 4 is "cannot make it at all."
    - follow the same thing for more persons as column C. 
    
    This script can then be run by providing the input csv name and an 
    output csv name. 

    More options:
    - It is possible to skip column B and row 2 (the counts), and let 
    the program assume that all counts are 1.

    - If you supply an equal number of slots as persons, then every slot
    will be assigned 1 person.
    - If you supply more persons than slots, then some people will not be 
    assigned a slot.
    - If you supply more slots than persons, then some slots will not be 
    assigned a person.
    """, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('input', type=str, help='Input CSV file.')
    parser.add_argument('output', type=str, help='Output file name.')

    group_counts = parser.add_mutually_exclusive_group(required=False)
    group_counts.add_argument('--no-custom-counts', action='store_true', help='Indicates that the input CSV does not have count columns / rows, and simply assumes that each count is 1.')

    args = parser.parse_args()

    cost_matrix, slots, entities = parse_csv(args.input, args.no_custom_counts)
    row_ind, col_ind = solve(cost_matrix, slots, entities)
    write_output(args.output, cost_matrix, row_ind, col_ind, slots, entities)



