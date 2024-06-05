import simpy
import random

class WashingMachineSystem:
    def __init__(self, env, num_machines, detergent_sizes):
        self.env = env
        self.machines = simpy.Resource(env, num_machines)
        self.detergent_sizes = detergent_sizes
        self.waiting_queue = []

    def calculate_costs(self, washing_weight, wash_type):
        # Placeholder logic for cost calculation
        base_cost = 5
        detergent_cost = washing_weight * 0.1  # Assume cost per weight unit
        wash_duration = washing_weight * 0.5  # Assume duration per weight unit
        return base_cost, detergent_cost, wash_duration

    def wash(self, user_id, machine_id, wash_duration):
        print(f'User {user_id} starts washing on machine {machine_id} at time {self.env.now}')
        yield self.env.timeout(wash_duration)
        print(f'User {user_id} finishes washing on machine {machine_id} at time {self.env.now}')

    def user(self, user_id, washing_weight, wash_type):
        arrival_time = self.env.now
        base_cost, detergent_cost, wash_duration = self.calculate_costs(washing_weight, wash_type)
        total_cost = base_cost + detergent_cost
        completion_time = self.env.now + wash_duration
        detergent_size = random.choice(self.detergent_sizes)
        
        print(f'User {user_id} arrives at time {arrival_time}')
        print(f'User {user_id} cost: ${total_cost:.2f}, detergent size: {detergent_size}g, duration: {wash_duration} mins, completion: {completion_time} mins')
        
        with self.machines.request() as request:
            yield request
            machine_start_time = self.env.now
            machine_id = request.resource.count
            print(f'User {user_id} gets machine {machine_id} at time {machine_start_time}')
            
            # Start washing
            yield self.env.process(self.wash(user_id, machine_id, wash_duration))
            
            completion_time = self.env.now
            print(f'User {user_id} leaves at time {completion_time}')

    def run(self, num_users, interarrival_time):
        for i in range(num_users):
            washing_weight = random.uniform(1, 10)  # Random washing weight
            wash_type = 'regular'  # Example wash type
            self.env.process(self.user(i, washing_weight, wash_type))
            yield self.env.timeout(interarrival_time)

# Initialize simulation environment
env = simpy.Environment()
detergent_sizes = [50, 100, 150]  # Example detergent sizes in grams
washing_machine_system = WashingMachineSystem(env, num_machines=2, detergent_sizes=detergent_sizes)
env.process(washing_machine_system.run(num_users=5, interarrival_time=2))
env.run(until=50)
