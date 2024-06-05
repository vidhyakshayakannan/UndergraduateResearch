import simpy
import random
import itertools
import numpy as np

class WashTask:
    def __init__(self, user_id, washing_weight, wash_type, arrival_time):
        self.user_id = user_id
        self.washing_weight = washing_weight
        self.wash_type = wash_type
        self.arrival_time = arrival_time
        self.completion_time = self.calculate_wash_duration()

    def calculate_wash_duration(self):
        return self.washing_weight * 0.5  # How is the washing duration related to the weight of the clothes?

def generate_wash_tasks(num_tasks, mean_weight, std_dev_weight):
    tasks = []
    for i in range(num_tasks):
        washing_weight = max(int(np.random.normal(mean_weight, std_dev_weight)), 1)  # Ensure weight is at least 1
        arrival_time = random.randint(0, mean_weight * 2)  # Random arrival time
        task = WashTask(user_id=i + 1, washing_weight=washing_weight, wash_type='regular', arrival_time=arrival_time)
        tasks.append(task)
    return tasks

def wash_process(env, task, machine, total_turnaround_time, total_burst_time, total_waiting_time, order):
    yield env.timeout(task.arrival_time)
    with machine.request() as request:
        arrival_time = env.now
        yield request
        yield env.timeout(task.completion_time)
        total_time = env.now - arrival_time
        total_turnaround_time[0] += total_time
        total_burst_time[0] += task.completion_time
        total_waiting_time[0] += total_time - task.completion_time
        order.append(task.user_id)

def simulate_fcfs(env, tasks):
    machine = simpy.Resource(env, capacity=1)
    total_turnaround_time = [0]
    total_burst_time = [0]
    total_waiting_time = [0]
    order = []

    for task in tasks:
        env.process(wash_process(env, task, machine, total_turnaround_time, total_burst_time, total_waiting_time, order))

    env.run()
    return total_turnaround_time[0], total_burst_time[0], total_waiting_time[0], order

def simulate_sjf(env, tasks):
    machine = simpy.Resource(env, capacity=1)
    total_turnaround_time = [0]
    total_burst_time = [0]
    total_waiting_time = [0]
    order = []

    sorted_tasks = sorted(tasks, key=lambda task: (task.arrival_time, task.completion_time))

    for task in sorted_tasks:
        env.process(wash_process(env, task, machine, total_turnaround_time, total_burst_time, total_waiting_time, order))

    env.run()
    return total_turnaround_time[0], total_burst_time[0], total_waiting_time[0], order

def simulate_rr(env, tasks, time_slice):
    machine = simpy.Resource(env, capacity=1)
    total_turnaround_time = [0]
    total_burst_time = [0]
    total_waiting_time = [0]
    order = []
    remaining_times = {task.user_id: task.completion_time for task in tasks}
    task_queue = sorted(tasks, key=lambda task: task.arrival_time)

    def rr_task_process(env, task, machine, time_slice, remaining_times, order):
        while remaining_times[task.user_id] > 0:
            with machine.request() as request:
                yield env.timeout(task.arrival_time - env.now) if env.now < task.arrival_time else env.timeout(0)
                yield request
                run_time = min(time_slice, remaining_times[task.user_id])
                yield env.timeout(run_time)
                remaining_times[task.user_id] -= run_time
                if remaining_times[task.user_id] <= 0:
                    total_time = env.now - task.arrival_time
                    total_turnaround_time[0] += total_time
                    total_burst_time[0] += task.completion_time
                    total_waiting_time[0] += total_time - task.completion_time
                    order.append(task.user_id)
                    if task in task_queue:
                        task_queue.remove(task)

    while task_queue:
        for task in list(task_queue):
            env.process(rr_task_process(env, task, machine, time_slice, remaining_times, order))
            env.run(until=env.now + time_slice)

    return total_turnaround_time[0], total_burst_time[0], total_waiting_time[0], order

def simulate_srtn(env, tasks):
    machine = simpy.Resource(env, capacity=1)
    total_turnaround_time = [0]
    total_burst_time = [0]
    total_waiting_time = [0]
    order = []
    remaining_times = {task.user_id: task.completion_time for task in tasks}
    task_queue = sorted(tasks, key=lambda task: task.arrival_time)

    def srtn_task_process(env, task, machine, remaining_times, order):
        while remaining_times[task.user_id] > 0:
            with machine.request() as request:
                yield env.timeout(task.arrival_time - env.now) if env.now < task.arrival_time else env.timeout(0)
                yield request
                run_time = min(1, remaining_times[task.user_id])
                yield env.timeout(run_time)
                remaining_times[task.user_id] -= run_time
                if remaining_times[task.user_id] <= 0:
                    total_time = env.now - task.arrival_time
                    total_turnaround_time[0] += total_time
                    total_burst_time[0] += task.completion_time
                    total_waiting_time[0] += total_time - task.completion_time
                    if task.user_id not in order:
                      order.append(task.user_id)
                    if task in task_queue:
                        task_queue.remove(task)

    while task_queue:
        task_queue.sort(key=lambda t: remaining_times[t.user_id])
        env.process(srtn_task_process(env, task_queue[0], machine, remaining_times, order))
        env.run(until=env.now + 1)

    return total_turnaround_time[0], total_burst_time[0], total_waiting_time[0], order

def simulate_hrrn(env, tasks):
    machine = simpy.Resource(env, capacity=1)
    total_turnaround_time = [0]
    total_burst_time = [0]
    total_waiting_time = [0]
    order = []
    remaining_times = {task.user_id: task.completion_time for task in tasks}
    arrival_times = {task.user_id: task.arrival_time for task in tasks}
    task_queue = sorted(tasks, key=lambda task: task.arrival_time)

    def hrrn_task_process(env, task, machine, remaining_times, arrival_times, order):
        yield env.timeout(task.arrival_time)
        while remaining_times[task.user_id] > 0:
            with machine.request() as request:
                yield request
                run_time = remaining_times[task.user_id]
                yield env.timeout(run_time)
                remaining_times[task.user_id] -= run_time
                if remaining_times[task.user_id] <= 0:
                    total_time = env.now - arrival_times[task.user_id]
                    total_turnaround_time[0] += total_time
                    total_burst_time[0] += task.completion_time
                    total_waiting_time[0] += total_time - task.completion_time
                    order.append(task.user_id)
                    break

    while task_queue:
        available_tasks = [task for task in task_queue if task.arrival_time <= env.now]
        if available_tasks:
            hrrn = [(task, ((env.now - arrival_times[task.user_id] + remaining_times[task.user_id]) / remaining_times[task.user_id])) for task in available_tasks]
            task_queue.sort(key=lambda t: next((hr for task, hr in hrrn if t.user_id == task.user_id), -1), reverse=True)
            env.process(hrrn_task_process(env, task_queue[0], machine, remaining_times, arrival_times, order))
            task_queue.pop(0)
        env.run(until=env.now + 1)

    return total_turnaround_time[0], total_burst_time[0], total_waiting_time[0], order

# Simulation Parameters
num_users = 10
mean_weight = 5
std_dev_weight = 2
time_slice = 3

# Generate wash tasks
tasks = generate_wash_tasks(num_users, mean_weight, std_dev_weight)

# Run simulations
env = simpy.Environment()
fcfs_total_time, fcfs_burst_time, fcfs_waiting_time, fcfs_order = simulate_fcfs(env, tasks)
env = simpy.Environment()
sjf_total_time, sjf_burst_time, sjf_waiting_time, sjf_order = simulate_sjf(env, tasks)
env = simpy.Environment()
rr_total_time, rr_burst_time, rr_waiting_time, rr_order = simulate_rr(env, tasks, time_slice)
env = simpy.Environment()
srtn_total_time, srtn_burst_time, srtn_waiting_time, srtn_order = simulate_srtn(env, tasks)
env = simpy.Environment()
hrrn_total_time, hrrn_burst_time, hrrn_waiting_time, hrrn_order = simulate_hrrn(env, tasks)

# Display results
print("FCFS Order:", fcfs_order)
print(f"Total Turnaround Time: {fcfs_total_time}, Total Burst Time: {fcfs_burst_time}, Total Waiting Time: {fcfs_waiting_time}")

print("\nSJF Order:", sjf_order)
print(f"Total Turnaround Time: {sjf_total_time}, Total Burst Time: {sjf_burst_time}, Total Waiting Time: {sjf_waiting_time}")

print("\nRR Order:", rr_order)
print(f"Total Turnaround Time: {rr_total_time}, Total Burst Time: {rr_burst_time}, Total Waiting Time: {rr_waiting_time}")

print("\nSRTN Order:", srtn_order)
print(f"Total Turnaround Time: {srtn_total_time}, Total Burst Time: {srtn_burst_time}, Total Waiting Time: {srtn_waiting_time}")

print("\nHRRN Order:", hrrn_order)
print(f"Total Turnaround Time: {hrrn_total_time}, Total Burst Time: {hrrn_burst_time}, Total Waiting Time: {hrrn_waiting_time}")
