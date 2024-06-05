import simpy
import random
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm

# Define simulation parameters
NUM_TASKS = 100
WEIGHT_RANGE = (1, 10)  # Range of weight in kg

class Task:
    def __init__(self, env, task_id, weight):
        self.env = env
        self.task_id = task_id
        self.weight = weight
        self.computation_time = None

    def load_clothes(self):
        # Simulate loading clothes, computation time varies based on weight
        computation_time = self.weight * random.uniform(1, 2)  # Adjust multiplier based on observations
        yield self.env.timeout(computation_time)
        self.computation_time = computation_time

def task_generator(env, data):
    for i in range(NUM_TASKS):
        weight = random.randint(*WEIGHT_RANGE)
        task = Task(env, i, weight)
        env.process(task_process(env, task, data))
        yield env.timeout(0)  # Yield an event to ensure this is a generator

def task_process(env, task, data):
    yield env.process(task.load_clothes())
    data.append((task.weight, task.computation_time))

# Initialize simulation environment and start simulation
env = simpy.Environment()
data = []
env.process(task_generator(env, data))
env.run()

# Unpack data
weights, computation_times = zip(*data)

# Plot data
plt.scatter(weights, computation_times)
plt.xlabel('Weight (kg)')
plt.ylabel('Computation Time')
plt.title('Relationship between Weight and Computation Time')
plt.show()

# Analyze data (perform statistical tests, regression analysis, etc.)
# For example, you can use linear regression to model the relationship
weights_with_const = sm.add_constant(weights)  # Add constant term for intercept
model = sm.OLS(computation_times, weights_with_const)  # Create OLS model
result = model.fit()  # Fit model
print(result.summary())
