import simpy
import random
import streamlit as st
import matplotlib.pyplot as plt

# Process representing a user using a washing machine
def user(env, name, washing_machines, washing_time):
    arrival_time = env.now
    print(f'{name} arrives at {arrival_time:.2f}')
    
    with washing_machines.request() as request:
        yield request
        start_time = env.now
        print(f'{name} starts using a washing machine at {start_time:.2f}')
        yield env.timeout(random.expovariate(1.0 / washing_time))
        print(f'{name} finishes at {env.now:.2f}')
    
    turnaround_time = env.now - arrival_time
    return turnaround_time

# Generator function to create users dynamically
def user_generator(env, washing_machines, num_users, inter_arrival_time, washing_time):
    user_count = 0
    while user_count < num_users:
        yield env.timeout(random.expovariate(1.0 / inter_arrival_time))
        user_count += 1
        env.process(user(env, f'User {user_count}', washing_machines, washing_time))

# Main simulation function
def run_simulation(num_washing_machines, num_users, inter_arrival_time, washing_time):
    env = simpy.Environment()
    washing_machines = simpy.Resource(env, capacity=num_washing_machines)
    env.process(user_generator(env, washing_machines, num_users, inter_arrival_time, washing_time))
    env.run()

# Streamlit UI
def main():
    st.title("Washing Machine Simulation with Multiple Users")

    st.sidebar.header("Simulation Settings")
    num_washing_machines = st.sidebar.slider("Number of Washing Machines", min_value=1, max_value=10, value=3)
    num_users = st.sidebar.slider("Number of Users", min_value=1, max_value=50, value=20)
    inter_arrival_time = st.sidebar.slider("Average Inter-Arrival Time", min_value=1, max_value=10, value=5)
    washing_time = st.sidebar.slider("Average Washing Time", min_value=5, max_value=20, value=10)

    if st.button("Run Simulation"):
        run_simulation(num_washing_machines, num_users, inter_arrival_time, washing_time)

if __name__ == "__main__":
    main()
