# scheduling_solution
Scheduling solution for my needs to match persons optimally to assignments based on 4 levels of preferences. 

A solution for scheduling hell! 

Create a CSV with the following properties:
* cell A1 = 'Assignment'
* cell A2 = 'Counts'
* cells A3-A[#] being the names of the entities that require assignments. 
For instance, "Section 1", "Section 2", etc. 
* cell B1 = 'Counts'
* leave cell B2 blank
* cells B3-B[#] being the number of assignments to be made 
to the corresponding entity in A3-A[#]. For instance, Section 2 
requires 3 persons assigned to it.
* cell C1 should contain the name of a person (who needs to be 
assigned an entity)
* cell C2 should contain the count of entities to be assigned to this person
* cells C3-C[#] should contain the preferences of the person to be assigned 
to the corresponding entity. The prefernce must be {1, 2, 3, 4}, where 1 is 
"most preferred" and 4 is "cannot make it at all."
* follow the same thing for more persons as column C. 

This script can then be run by providing the input csv name and an 
output csv name. 

More options:
* It is possible to skip column B and row 2 (the counts), and let 
the program assume that all counts are 1.

* It is possible to specify the minimum/maximum counts and let 
the program generate assignments that are allowed to be over/under 
the counts provided in the CSV. 
Common use case: There are 4 homework party slots, and 18 TAs. Each 
slot needs a minimum of 4 people, but the remaining 2 can be assigned 
freely to the best preferred slot. In this case, this script can be run 
with --bound lower, specifying that the counts in the CSV are a 
lower bound.
