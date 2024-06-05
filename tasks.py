import streamlit as st
import numpy as np
import itertools
import simpy
import random
import matplotlib.pyplot as plt

class Task:
    def __init__(self, task_id, completion_time, arrival_time):
        self.task_id = task_id
        self.completion_time = completion_time
        self.arrival_time = arrival_time

    def __repr__(self):
        return f"Task {self.task_id} (Completion Time: {self.completion_time}, Arrival Time: {self.arrival_time})"

# Generate a set of "n" tasks

def generate_tasks(num_tasks, mean, std_dev):
    tasks = []
    for i in range(num_tasks):
        duration = max(int(np.random.normal(mean, std_dev)), 1)  # Ensure duration is at least 1
        arrival_time = random.randint(0, mean * 2)  # Random arrival time
        task = Task(task_id=i + 1, completion_time=duration, arrival_time=arrival_time)
        tasks.append(task)
    
    return tasks

# Compute total turnaround time for the set of "n" tasks

def compute_total_time(env, tasks):
    machine = simpy.Resource(env, capacity=1)
    total_times = []
    total_turnaround_time = 0
    total_burst_time = 0
    total_waiting_time = 0

    def task_process(env, task, machine):
        nonlocal total_turnaround_time, total_burst_time, total_waiting_time
        yield env.timeout(task.arrival_time)
        with machine.request() as request:
            arrival_time = env.now  # Record the time when the task enters the queue
            yield request
            yield env.timeout(task.completion_time)
            total_time = env.now - arrival_time  # Calculate the total time spent in the system
            total_times.append(total_time)
            total_turnaround_time += total_time
            total_burst_time += task.completion_time
            total_waiting_time += total_time - task.completion_time  # Calculate the waiting time as the difference between total time and burst time

    for task in tasks:
        env.process(task_process(env, task, machine))

    env.run()
    return total_turnaround_time, total_burst_time, total_waiting_time

def find_minimum_total_time(tasks):
    min_total_time = float('inf')
    min_permutation = None

    for permutation in itertools.permutations(tasks):
        env = simpy.Environment()
        total_time, _, _ = compute_total_time(env, permutation)
        if total_time < min_total_time:
            min_total_time = total_time
            min_permutation = permutation

    return min_total_time, min_permutation

def fcfs(env, tasks):
    machine = simpy.Resource(env, capacity=1)
    total_times = []
    fcfs_order = []  
    total_turnaround_time = 0
    total_burst_time = 0
    total_waiting_time = 0

    def task_process(env, task, machine, fcfs_order):  # Add fcfs_order as an argument
        nonlocal total_turnaround_time, total_burst_time, total_waiting_time
        yield env.timeout(task.arrival_time)
        with machine.request() as request:
            arrival_time = env.now  # Record the time when the task enters the queue
            yield request
            yield env.timeout(task.completion_time)
            total_time = env.now - arrival_time  # Calculate the total time spent in the system
            total_times.append(total_time)
            fcfs_order.append(task.task_id)  # Append task_id to fcfs_order
            total_turnaround_time += total_time
            total_burst_time += task.completion_time
            total_waiting_time += total_time - task.completion_time  # Calculate the waiting time as the difference between total time and burst time

    for task in tasks:
        env.process(task_process(env, task, machine, fcfs_order))

    env.run()
    return total_turnaround_time, total_burst_time, total_waiting_time, fcfs_order

def sjf(env, tasks):
    machine = simpy.Resource(env, capacity=1)
    total_times = []
    sjf_order = []
    total_turnaround_time = 0
    total_burst_time = 0
    total_waiting_time = 0
    sorted_tasks = sorted(tasks, key=lambda task: (task.arrival_time, task.completion_time))

    def task_process(env, task, machine, sjf_order):
        nonlocal total_turnaround_time, total_burst_time, total_waiting_time
        yield env.timeout(task.arrival_time)
        with machine.request() as request:
            arrival_time = env.now  # Record the time when the task enters the queue
            yield request
            yield env.timeout(task.completion_time)
            total_time = env.now - arrival_time  # Calculate the total time spent in the system
            total_times.append(total_time)
            sjf_order.append(task.task_id)
            total_turnaround_time += total_time
            total_burst_time += task.completion_time
            total_waiting_time += total_time - task.completion_time  # Calculate the waiting time as the difference between total time and burst time

    for task in sorted_tasks:
        env.process(task_process(env, task, machine, sjf_order))

    env.run()
    return total_turnaround_time, total_burst_time, total_waiting_time, sjf_order

def rr(env, tasks, time_slice):
    machine = simpy.Resource(env, capacity=1)
    total_times = []
    rr_order = []
    total_turnaround_time = 0
    total_burst_time = 0
    total_waiting_time = 0
    remaining_times = {task.task_id: task.completion_time for task in tasks}
    task_queue = sorted(tasks, key=lambda task: task.arrival_time)

    def task_process(env, task, machine, time_slice, rr_order):
        nonlocal total_turnaround_time, total_burst_time, total_waiting_time
        while remaining_times[task.task_id] > 0:
            with machine.request() as request:
                yield env.timeout(task.arrival_time - env.now) if env.now < task.arrival_time else env.timeout(0)
                yield request
                run_time = min(time_slice, remaining_times[task.task_id])
                yield env.timeout(run_time)
                remaining_times[task.task_id] -= run_time
                if remaining_times[task.task_id] <= 0:
                    total_time = env.now - task.arrival_time
                    total_times.append(total_time)
                    rr_order.append(task.task_id)
                    total_turnaround_time += total_time
                    total_burst_time += task.completion_time
                    total_waiting_time += total_time - task.completion_time  # Calculate the waiting time as the difference between total time and burst time
                    if task in task_queue:
                        task_queue.remove(task)

    while task_queue:
        for task in list(task_queue):
            env.process(task_process(env, task, machine, time_slice, rr_order))
            env.run(until=env.now + time_slice)

    return total_turnaround_time, total_burst_time, total_waiting_time, rr_order

def srtn(env, tasks):
    machine = simpy.Resource(env, capacity=1)
    total_times = []
    srtn_order = []
    total_turnaround_time = 0
    total_burst_time = 0
    total_waiting_time = 0
    remaining_times = {task.task_id: task.completion_time for task in tasks}
    task_queue = sorted(tasks, key=lambda task: task.arrival_time)

    def task_process(env, task, machine, srtn_order):
        nonlocal total_turnaround_time, total_burst_time, total_waiting_time
        while remaining_times[task.task_id] > 0:
            with machine.request() as request:
                yield env.timeout(task.arrival_time - env.now) if env.now < task.arrival_time else env.timeout(0)
                yield request
                run_time = min(1, remaining_times[task.task_id])
                yield env.timeout(run_time)
                remaining_times[task.task_id] -= run_time
                if remaining_times[task.task_id] <= 0:
                    total_time = env.now - task.arrival_time
                    total_times.append(total_time)
                    srtn_order.append(task.task_id)
                    total_turnaround_time += total_time
                    total_burst_time += task.completion_time
                    total_waiting_time += total_time - task.completion_time  # Calculate the waiting time as the difference between total time and burst time
                    if task in task_queue:
                        task_queue.remove(task)

    while task_queue:
        task_queue.sort(key=lambda t: remaining_times[t.task_id])
        env.process(task_process(env, task_queue[0], machine, srtn_order))
        env.run(until=env.now + 1)

    return total_turnaround_time, total_burst_time, total_waiting_time, srtn_order

def hrrn(env, tasks):
    machine = simpy.Resource(env, capacity=1)
    total_times = []
    hrrn_order = []
    total_turnaround_time = 0
    total_burst_time = 0
    total_waiting_time = 0
    remaining_times = {task.task_id: task.completion_time for task in tasks}
    arrival_times = {task.task_id: task.arrival_time for task in tasks}
    task_queue = sorted(tasks, key=lambda task: task.arrival_time)

    def task_process(env, task, machine, hrrn_order):
        nonlocal total_turnaround_time, total_burst_time, total_waiting_time
        yield env.timeout(task.arrival_time)
        while remaining_times[task.task_id] > 0:
            with machine.request() as request:
                yield request
                run_time = remaining_times[task.task_id]
                yield env.timeout(run_time)
                remaining_times[task.task_id] -= run_time
                if remaining_times[task.task_id] <= 0:
                    total_time = env.now - arrival_times[task.task_id]
                    total_times.append(total_time)
                    hrrn_order.append(task.task_id)
                    total_turnaround_time += total_time
                    total_burst_time += task.completion_time
                    total_waiting_time += total_time - task.completion_time
                    break

    while task_queue:
        available_tasks = [task for task in task_queue if task.arrival_time <= env.now]
        if available_tasks:
            hrrn = [(task, ((env.now - task.arrival_time + remaining_times[task.task_id]) / remaining_times[task.task_id])) for task in available_tasks]
            task_queue.sort(key=lambda t: hrrn[available_tasks.index(t)][1], reverse=True)
            env.process(task_process(env, task_queue[0], machine, hrrn_order))
            task_queue.pop(0)
        env.run(until=env.now + 1)

    return total_turnaround_time, total_burst_time, total_waiting_time, hrrn_order


st.title('Task Scheduling Algorithms Comparison')

st.sidebar.header('Input Parameters')
num_tasks = st.sidebar.slider('Number of Tasks', 1, 20, 5)
mean_duration = st.sidebar.slider('Mean Task Duration', 1, 10, 5)
std_dev_duration = st.sidebar.slider('Standard Deviation of Task Duration', 1, 5, 2)
time_slice = st.sidebar.slider('Time Slice for Round Robin', 1, 10, 3)

tasks = generate_tasks(num_tasks, mean_duration, std_dev_duration)

st.subheader('Generated Tasks')
for task in tasks:
    st.write(task)

env = simpy.Environment()
fcfs_total_time, fcfs_burst_time, fcfs_waiting_time, fcfs_order = fcfs(env, tasks)
env = simpy.Environment()
sjf_total_time, sjf_burst_time, sjf_waiting_time, sjf_order = sjf(env, tasks)
env = simpy.Environment()
rr_total_time, rr_burst_time, rr_waiting_time, rr_order = rr(env, tasks, time_slice)
env = simpy.Environment()
srtn_total_time, srtn_burst_time, srtn_waiting_time, srtn_order = srtn(env, tasks)
env = simpy.Environment()
hrrn_total_time, hrrn_burst_time, hrrn_waiting_time, hrrn_order = hrrn(env, tasks)

# For optimal permutation (exponential complexity), we limit to smaller tasks
if num_tasks <= 6:
    min_total_time, min_permutation = find_minimum_total_time(tasks)
    st.subheader('Optimal Permutation')
    st.write(' -> '.join([str(task.task_id) for task in min_permutation]))
    st.write(f'Total Turnaround Time: {min_total_time}')
else:
    min_total_time = None

st.subheader('First-Come, First-Served (FCFS)')
st.write('Order:', ' -> '.join(map(str, fcfs_order)))
st.write(f'Total Turnaround Time: {fcfs_total_time}, Total Burst Time: {fcfs_burst_time}, Total Waiting Time: {fcfs_waiting_time}')

st.subheader('Shortest Job First (SJF)')
st.write('Order:', ' -> '.join(map(str, sjf_order)))
st.write(f'Total Turnaround Time: {sjf_total_time}, Total Burst Time: {sjf_burst_time}, Total Waiting Time: {sjf_waiting_time}')

st.subheader('Round Robin (RR)')
st.write('Order:', ' -> '.join(map(str, rr_order)))
st.write(f'Total Turnaround Time: {rr_total_time}, Total Burst Time: {rr_burst_time}, Total Waiting Time: {rr_waiting_time}')

st.subheader('Shortest Remaining Time Next (SRTN)')
st.write('Order:', ' -> '.join(map(str, srtn_order)))
st.write(f'Total Turnaround Time: {srtn_total_time}, Total Burst Time: {srtn_burst_time}, Total Waiting Time: {srtn_waiting_time}')

st.subheader('Highest Response Ratio Next (HRRN)')
st.write('Order:', ' -> '.join(map(str, hrrn_order)))
st.write(f'Total Turnaround Time: {hrrn_total_time}, Total Burst Time: {hrrn_burst_time}, Total Waiting Time: {hrrn_waiting_time}')

# Plot the comparison
labels = ['FCFS', 'SJF', 'RR', 'SRTN', 'HRRN']
times = [fcfs_total_time, sjf_total_time, rr_total_time, srtn_total_time, hrrn_total_time]

fig, ax = plt.subplots()
ax.bar(labels, times, color=['blue', 'orange', 'green', 'red', 'purple'])
ax.set_ylabel('Total Turnaround Time')
ax.set_title('Comparison of Scheduling Algorithms')
st.pyplot(fig)
