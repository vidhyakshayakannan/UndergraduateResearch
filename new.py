import simpy
import random
import numpy as np
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Parameters for cost and detergent
COST_PER_MINUTE = 0.5  # Cost per minute of washing
DETERGENT_COST_PER_UNIT = 0.1  # Cost per unit of detergent
DETERGENT_UNITS_PER_KG = 0.1  # Units of detergent per kg of clothes

class WashingTask:
    def __init__(self, user_id, weight, fabric_type, wash_type, arrival_time):
        self.user_id = user_id
        self.weight = weight
        self.fabric_type = fabric_type
        self.wash_type = wash_type
        self.arrival_time = arrival_time
        self.detergent_units = weight * DETERGENT_UNITS_PER_KG
        self.detergent_cost = self.detergent_units * DETERGENT_COST_PER_UNIT
        self.wash_duration = self.calculate_wash_duration()
        self.wash_cost = self.wash_duration * COST_PER_MINUTE

    def calculate_wash_duration(self):
        # Different wash types can have different durations
        if self.wash_type == 'quick':
            return max(10, int(np.random.normal(15, 2)))
        elif self.wash_type == 'normal':
            return max(20, int(np.random.normal(30, 5)))
        elif self.wash_type == 'heavy':
            return max(30, int(np.random.normal(45, 10)))
        else:
            return max(15, int(np.random.normal(25, 5)))

def generate_wash_tasks(num_users, mean_weight, std_dev_weight):
    tasks = []
    for i in range(num_users):
        weight = max(1, int(np.random.normal(mean_weight, std_dev_weight)))  # Ensure weight is at least 1
        fabric_type = random.choice(['cotton', 'polyester', 'silk'])  # Add fabric type
        wash_type = random.choice(['quick', 'normal', 'heavy'])
        arrival_time = random.randint(0, 10)
        task = WashingTask(user_id=i + 1, weight=weight, fabric_type=fabric_type, wash_type=wash_type, arrival_time=arrival_time)
        tasks.append(task)
    return tasks

def simulate_washing(env, tasks, scheduling_algorithm, time_slice=3):
    machine = simpy.Resource(env, capacity=1)
    order = []
    data = []  # Data collection for regression analysis
    completion_times = []

    def washing_process(env, task, machine, order, data):
        yield env.timeout(task.arrival_time)
        with machine.request() as request:
            yield request
            start_time = env.now
            order.append(task.user_id)
            for remaining_time in range(task.wash_duration, 0, -1):
                yield env.timeout(1)
            completion_time = env.now
            data.append((task.weight, task.wash_duration, task.fabric_type, task.wash_type, completion_time - start_time))
            completion_times.append(completion_time - task.arrival_time)

    def rr_process(env, tasks, time_slice, machine, order, data):
        task_queue = sorted(tasks, key=lambda task: task.arrival_time)
        remaining_times = {task.user_id: task.wash_duration for task in tasks}
        task_end_times = {task.user_id: None for task in tasks}

        while task_queue:
            for task in list(task_queue):
                if task.arrival_time <= env.now:
                    with machine.request() as request:
                        yield request
                        run_time = min(time_slice, remaining_times[task.user_id])
                        for remaining_time in range(run_time, 0, -1):
                            yield env.timeout(1)
                            remaining_times[task.user_id] -= 1
                            if remaining_times[task.user_id] == 0:
                                task_end_times[task.user_id] = env.now
                                task_queue.remove(task)
                                break
                        if task.user_id not in order:
                            order.append(task.user_id)
                else:
                    yield env.timeout(task.arrival_time - env.now)
            if not task_queue:
                break

    def fcfs_process(env, tasks, machine, order, data):
        for task in tasks:
            env.process(washing_process(env, task, machine, order, data))

    def sjf_process(env, tasks, machine, order, data):
        sorted_tasks = sorted(tasks, key=lambda task: (task.arrival_time, task.wash_duration))
        for task in sorted_tasks:
            env.process(washing_process(env, task, machine, order, data))

    def srtn_process(env, tasks, machine, order, data):
        task_queue = sorted(tasks, key=lambda task: task.arrival_time)
        remaining_times = {task.user_id: task.wash_duration for task in tasks}

        while task_queue:
            task_queue.sort(key=lambda t: (remaining_times[t.user_id], t.arrival_time))
            for task in list(task_queue):
                if task.arrival_time <= env.now:
                    with machine.request() as request:
                        yield request
                        run_time = remaining_times[task.user_id]
                        for remaining_time in range(run_time, 0, -1):
                            yield env.timeout(1)
                            remaining_times[task.user_id] -= 1
                            if remaining_times[task.user_id] == 0:
                                order.append(task.user_id)
                                task_queue.remove(task)
                                break
                else:
                    yield env.timeout(task.arrival_time - env.now)
            if not task_queue:
                break

    def hrrn_process(env, tasks, machine, order, data):
        task_queue = sorted(tasks, key=lambda task: task.arrival_time)
        remaining_times = {task.user_id: task.wash_duration for task in tasks}
        arrival_times = {task.user_id: task.arrival_time for task in tasks}

        while task_queue:
            available_tasks = [task for task in task_queue if task.arrival_time <= env.now]
            if available_tasks:
                hrrn_values = [(task, ((env.now - task.arrival_time + remaining_times[task.user_id]) / remaining_times[task.user_id])) for task in available_tasks]
                hrrn_values.sort(key=lambda x: x[1], reverse=True)
                highest_task = hrrn_values[0][0]
                with machine.request() as request:
                    yield request
                    run_time = remaining_times[highest_task.user_id]
                    for remaining_time in range(run_time, 0, -1):
                        yield env.timeout(1)
                        remaining_times[highest_task.user_id] -= 1
                        if remaining_times[highest_task.user_id] == 0:
                            order.append(highest_task.user_id)
                            task_queue.remove(highest_task)
                            break
            else:
                yield env.timeout(min(task.arrival_time for task in task_queue) - env.now)
            if not task_queue:
                break

    def brute_force_process(env, tasks, machine, order, data):
        sorted_tasks = sorted(tasks, key=lambda task: (task.arrival_time, task.wash_duration))
        for task in sorted_tasks:
            env.process(washing_process(env, task, machine, order, data))

    if scheduling_algorithm == 'FCFS':
        fcfs_process(env, tasks, machine, order, data)
    elif scheduling_algorithm == 'SJF':
        sjf_process(env, tasks, machine, order, data)
    elif scheduling_algorithm == 'RR':
        env.process(rr_process(env, tasks, time_slice, machine, order, data))
    elif scheduling_algorithm == 'SRTN':
        srtn_process(env, tasks, machine, order, data)
    elif scheduling_algorithm == 'HRRN':
        hrrn_process(env, tasks, machine, order, data)
    elif scheduling_algorithm == 'Brute Force':
        brute_force_process(env, tasks, machine, order, data)

    env.run()
    # Calculate the number of matches between SJF/FCFS order and optimal order
    def calculate_order_matches(optimal_order, algorithm_order):
        matches = sum(1 for x, y in zip(optimal_order, algorithm_order) if x == y)

# Calculate optimal order (assuming tasks are sorted based on arrival time)
optimal_order = [task.user_id for task in sorted(tasks, key=lambda x: x.arrival_time)]

# Count the number of matches for each algorithm
fcfs_matches = calculate_order_matches(optimal_order, order_fcfs)
sjf_matches = calculate_order_matches(optimal_order, order_sjf)

# Display the number of matches
st.write(f"Optimal Order Matches for FCFS and SJF")
st.write(f"FCFS matches with optimal order {fcfs_matches} times.")
st.write(f"SJF matches with optimal order {sjf_matches} times.")

    return order, completion_times



# Streamlit interface
st.title('Washing Machine Scheduling Simulation')

st.sidebar.header('Input Parameters')
num_users = st.sidebar.slider('Number of Users', 1, 200, 5)
mean_weight = st.sidebar.slider('Mean Weight of Clothes (kg)', 1, 10, 5)
std_dev_weight = st.sidebar.slider('Standard Deviation of Weight (kg)', 1, 5, 2)
scheduling_algorithms = st.sidebar.multiselect('Scheduling Algorithms', ['FCFS', 'SJF', 'RR', 'SRTN', 'HRRN', 'Brute Force'], default=['FCFS', 'SJF'])
time_slice = st.sidebar.slider('Time Slice for Round Robin', 1, 10, 3)
num_simulations = st.sidebar.slider('Number of Simulations', 1, 100, 10)

# Data collection
completion_times_all = {alg: [] for alg in scheduling_algorithms}

for sim in range(num_simulations):
    tasks = generate_wash_tasks(num_users, mean_weight, std_dev_weight)
    for algorithm in scheduling_algorithms:
        env = simpy.Environment()
        order, completion_times = simulate_washing(env, tasks, algorithm, time_slice)
        completion_times_all[algorithm].extend(completion_times)

# Aggregate completion times for each algorithm
completion_times_aggregated = {alg: np.histogram(times, bins=20, range=(0, max(times)))[0] for alg, times in completion_times_all.items()}

# Plot completion times as line plot
fig, ax = plt.subplots()
for algorithm in scheduling_algorithms:
    ax.plot(range(1, 21), completion_times_aggregated[algorithm], label=algorithm)
ax.set_xlabel('Bins')
ax.set_ylabel('Frequency')
ax.set_title('Completion Times for Different Scheduling Algorithms')
ax.legend()

st.pyplot(fig)


