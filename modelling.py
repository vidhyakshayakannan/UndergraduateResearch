import csv
import random
from ortools.linear_solver import pywraplp

def generate_random_data(users, loads):
    processing_times = {(u, l): random.randint(1, 10) for u in users for l in loads}
    return processing_times

def solve_optimization_problem(users, loads, machines, processing_times):
    solver = pywraplp.Solver.CreateSolver('SCIP')

    # Define decision variables
    x = {}
    for u in users:
        for l in loads:
            for j in machines:
                x[u, j, l] = solver.BoolVar(f'x_{u}_{j}_{l}')

    # Define objective function
    objective = solver.Objective()
    for u in users:
        for l in loads:
            for j in machines:
                objective.SetCoefficient(x[u, j, l], 1)
    objective.SetMaximization()  # Maximize the number of users allocated

    # Add constraints
    # Machine capacity constraint
    for j in machines:
        for u in users:
            solver.Add(sum(x[u, j, l] for l in loads) <= 1)

    # Solve the problem
    solver.Solve()
    
    return solver, x

def run_simulation(num_simulations, num_users, num_loads_per_user, num_machines):
    results = []
    users = [f'User{i+1}' for i in range(num_users)]
    loads = [f'Load{j+1}' for j in range(num_loads_per_user)]
    machines = [f'Machine{k+1}' for k in range(num_machines)]
    for _ in range(num_simulations):
        processing_times = generate_random_data(users, loads)
        solver, x = solve_optimization_problem(users, loads, machines, processing_times)
        num_users_allocated = sum(x[u, j, l].solution_value() > 0.5 for u in users for j in machines for l in loads)
        allocation_results = {f'Allocation_{i}': next(j for j in machines if x[u, j, l].solution_value() > 0.5) for u in users for l in loads for i in range(1, num_users*num_loads_per_user + 1)}
        result = {'Num Users Allocated': num_users_allocated, **allocation_results}
        results.append(result)
    return results

def write_results_to_csv(results, filename, num_users, num_loads_per_user):
    with open(filename, mode='w', newline='') as file:
        fieldnames = ['Num Users Allocated'] + [f'Allocation_{i}' for i in range(1, num_users*num_loads_per_user + 1)]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)

# Example usage
num_simulations = int(input("Enter the number of simulations: "))
num_users = int(input("Enter the number of users: "))
num_loads_per_user = int(input("Enter the maximum number of loads for each user: "))
num_machines = int(input("Enter the number of machines: "))

results = run_simulation(num_simulations, num_users, num_loads_per_user, num_machines)

# Write results to CSV file
filename = 'maximize_users.csv'
write_results_to_csv(results, filename, num_users, num_loads_per_user)

print("Data written to maximize_users.csv file.")
