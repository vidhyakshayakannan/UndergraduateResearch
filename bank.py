import streamlit as st
import numpy as np
import itertools
import simpy
import random
from collections import deque

class Task:
    def __init__(self, task_id, arrival_time, completion_time):
        self.task_id = task_id
        self.arrival_time = arrival_time
        self.completion_time = completion_time
        self.start_time = 0
        self.end_time = 0

    def __repr__(self):
        return f"Task {self.task_id} (Arrival: {self.arrival_time}, Duration: {self.completion_time})"

def generate_tasks_poisson(num_tasks, arrival_rate, mean, std_dev):
    tasks = []
    arrival_time = 0
    for i in range(num_tasks):
        arrival_time += np.random.exponential(arrival_rate)
        duration = max(int(np.random.normal(mean, std_dev)), 1)  # Ensure duration is at least 1
        task = Task(task_id=i + 1, arrival_time=arrival_time, completion_time=duration)
        tasks.append(task)
    return tasks

def compute_completion_time(env, tasks):
    machine = simpy.Resource(env, capacity=1)
    completion_times = []

    def task_process(env, task, machine):
        yield env.timeout(task.arrival_time)
        with machine.request() as request:
            yield request
            task.start_time = env.now
            yield env.timeout(task.completion_time)
            task.end_time = env.now
            completion_times.append(task.end_time - task.arrival_time)

    for task in tasks:
        env.process(task_process(env, task, machine))

    env.run()
    total_completion_time = sum(completion_times)
    return total_completion_time, tasks

def find_minimum_completion_time_with_brute_force(tasks):
    min_completion_time = float('inf')
    min_permutation = None

    for permutation in itertools.permutations(tasks):
        env = simpy.Environment()
        completion_time, _ = compute_completion_time(env, list(permutation))
        if completion_time < min_completion_time:
            min_completion_time = completion_time
            min_permutation = permutation

    return min_completion_time, min_permutation

def compute_fcfs_completion_time_with_simpy(env, tasks):
    machine = simpy.Resource(env, capacity=1)
    completion_times = []

    def task_process(env, task, machine):
        yield env.timeout(task.arrival_time)
        with machine.request() as request:
            yield request
            task.start_time = env.now
            yield env.timeout(task.completion_time)
            task.end_time = env.now
            completion_times.append(task.end_time - task.arrival_time)

    for task in tasks:
        env.process(task_process(env, task, machine))

    env.run()
    total_completion_time = sum(completion_times)
    return total_completion_time, tasks

def compute_sjf_completion_time_with_simpy(env, tasks):
    machine = simpy.Resource(env, capacity=1)
    completion_times = []
    sorted_tasks = sorted(tasks, key=lambda task: (task.arrival_time, task.completion_time))

    def task_process(env, task, machine):
        yield env.timeout(task.arrival_time)
        with machine.request() as request:
            yield request
            task.start_time = env.now
            yield env.timeout(task.completion_time)
            task.end_time = env.now
            completion_times.append(task.end_time - task.arrival_time)

    for task in sorted_tasks:
        env.process(task_process(env, task, machine))

    env.run()
    total_completion_time = sum(completion_times)
    return total_completion_time, sorted_tasks

def compute_srtn_completion_time_with_simpy(env, tasks):
    machine = simpy.Resource(env, capacity=1)
    remaining_times = {task.task_id: task.completion_time for task in tasks}
    task_queue = deque()  # Initialize task queue
    completion_times = []

    def task_process(env, task, machine):
        yield env.timeout(task.arrival_time)
        task_queue.append(task)  # Add task to the queue
        while task_queue:
            task_queue = deque(sorted(task_queue, key=lambda t: remaining_times[t.task_id]))
            current_task = task_queue.popleft()
            with machine.request() as request:
                yield request
                run_time = min(1, remaining_times[current_task.task_id])
                yield env.timeout(run_time)
                remaining_times[current_task.task_id] -= run_time
                if remaining_times[current_task.task_id] <= 0:
                    current_task.end_time = env.now
                    completion_times.append(current_task.end_time - current_task.arrival_time)
                    remaining_times.pop(current_task.task_id)

    for task in tasks:
        env.process(task_process(env, task, machine))

    env.run()
    total_completion_time = sum(completion_times)
    return total_completion_time, tasks

def compute_hrrn_completion_time_with_simpy(env, tasks):
    machine = simpy.Resource(env, capacity=1)
    remaining_times = {task.task_id: task.completion_time for task in tasks}
    arrival_times = {task.task_id: task.arrival_time for task in tasks}
    task_queue = deque()  # Initialize task queue
    completion_times = []

    def task_process(env, task, machine):
        yield env.timeout(task.arrival_time)
        task_queue.append(task)  # Add task to the queue
        while task_queue:
            for t in task_queue:
                waiting_time = env.now - arrival_times[t.task_id]
                response_ratio = (waiting_time + remaining_times[t.task_id]) / remaining_times[t.task_id]
                t.response_ratio = response_ratio

            task_queue = deque(sorted(task_queue, key=lambda t: t.response_ratio, reverse=True))
            current_task = task_queue.popleft()
            with machine.request() as request:
                yield request
                current_task.start_time = env.now
                yield env.timeout(current_task.completion_time)
                current_task.end_time = env.now
                completion_times.append(current_task.end_time - current_task.arrival_time)
                remaining_times.pop(current_task.task_id)

    for task in tasks:
        env.process(task_process(env, task, machine))

    env.run()
    total_completion_time = sum(completion_times)
    return total_completion_time, tasks

def main():
    st.title("Dynamic Task Scheduling and Completion Time Analysis with SimPy")

    num_tasks = st.number_input("Number of Tasks", min_value=1, value=5)
    arrival_rate = st.number_input("Arrival Rate (Lambda)", value=1.0)
    mean = st.number_input("Mean of Completion Time", value=5)
    std_dev = st.number_input("Standard Deviation of Completion Time", value=2)
    time_slice = st.number_input("Time Slice for Round Robin", min_value=1, value=1)
    num_simulations = st.number_input("Number of Simulations", min_value=1, value=100)

    if st.button("Generate and Analyze Tasks"):
        fcfs_match = 0
        sjf_match = 0
        srtn_match = 0
        hrrn_match = 0

        for _ in range(num_simulations):
            tasks = generate_tasks_poisson(num_tasks, arrival_rate, mean, std_dev)

            brute_force_time, brute_force_order = find_minimum_completion_time_with_brute_force(tasks)

            env = simpy.Environment()
            fcfs_time, fcfs_order = compute_fcfs_completion_time_with_simpy(env, tasks.copy())
            if [task.task_id for task in fcfs_order] == [task.task_id for task in brute_force_order]:
                fcfs_match += 1

            env = simpy.Environment()
            sjf_time, sjf_order = compute_sjf_completion_time_with_simpy(env, tasks.copy())
            if [task.task_id for task in sjf_order] == [task.task_id for task in brute_force_order]:
                sjf_match += 1

            env = simpy.Environment()
            srtn_time, srtn_order = compute_srtn_completion_time_with_simpy(env, tasks.copy())
            if [task.task_id for task in srtn_order] == [task.task_id for task in brute_force_order]:
                srtn_match += 1

            env = simpy.Environment()
            hrrn_time, hrrn_order = compute_hrrn_completion_time_with_simpy(env, tasks.copy())
            if [task.task_id for task in hrrn_order] == [task.task_id for task in brute_force_order]:
                hrrn_match += 1

        matches = {
            'FCFS': fcfs_match,
            'SJF': sjf_match,
            'SRTN': srtn_match,
            'HRRN': hrrn_match
        }

        best_discipline = max(matches, key=matches.get)

        st.subheader("Optimal Task Order Matching Results")
        st.write(f"FCFS matches: {fcfs_match}")
        st.write(f"SJF matches: {sjf_match}")
        st.write(f"SRTN matches: {srtn_match}")
        st.write(f"HRRN matches: {hrrn_match}")

        st.subheader("Best Scheduling Discipline")
        st.write(f"The scheduling discipline with the most optimal outputs is: {best_discipline} with {matches[best_discipline]} matches out of {num_simulations} simulations")

        st.subheader("Optimal Task Order")
        st.write(f"Optimal order of tasks: {[task.task_id for task in brute_force_order]}")

if __name__ == "__main__":
    main()
