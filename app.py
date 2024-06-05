from collections import deque

class Task:
    def __init__(self, id, processing_time):
        self.id = id
        self.processing_time = processing_time
        self.completion_time = None

class Scheduler:
    def __init__(self):
        self.queue = deque()
        self.resource_free = True
        self.current_task = None
        self.completed_tasks = []
        self.current_time = 0  # Add a time counter

    def add_task(self, task):
        self.queue.append(task)

    def schedule(self, scheduling_type):
        if scheduling_type == "FCFS":
            self.schedule_FCFS()
        elif scheduling_type == "SJF":
            self.schedule_SJF()
        else:
            raise ValueError("Invalid scheduling type")

    def schedule_FCFS(self):
        if self.resource_free and self.queue:
            self.current_task = self.queue.popleft()
            self.resource_free = False

    def schedule_SJF(self):
     if self.resource_free and self.queue:
        shortest_task = min(self.queue, key=lambda task: task.processing_time)
        self.queue.remove(shortest_task)
        self.current_task = shortest_task
        self.resource_free = False
        completion_time = self.get_time() + self.current_task.processing_time
        self.current_task.completion_time = completion_time



    def run(self, scheduling_type):  # Add scheduling_type parameter
        while self.queue or self.current_task:
            if self.current_task:
                self.current_task.processing_time -= 1
                if self.current_task.processing_time == 0:
                    self.current_task.completion_time = self.get_time()
                    self.completed_tasks.append(self.current_task)
                    self.current_task = None
                    self.resource_free = True
            self.schedule(scheduling_type)  # Use the passed scheduling_type
            # Simulate time passing
            self.increment_time()
   

    def get_time(self):
        return self.current_time

    def increment_time(self):
        self.current_time += 1


    def get_total_completion_time(self):
        total_time = 0
        for task in self.completed_tasks:
            total_time += task.completion_time
        return total_time


def main():
    scheduler = Scheduler()

    # Add some tasks (replace with your data generation)
    scheduler.add_task(Task(1, 5))
    scheduler.add_task(Task(2, 2))
    scheduler.add_task(Task(3, 8))

    # Run with FCFS
    scheduler.run("FCFS")  # Pass "FCFS" as the scheduling type
    fcfs_completion_time = scheduler.get_total_completion_time()

    # Reset scheduler state
    scheduler.queue.clear()
    scheduler.completed_tasks.clear()
    scheduler.resource_free = True
    scheduler.current_task = None

    # Run with SJF
    scheduler.run("SJF")  # Pass "SJF" as the scheduling type
    sjf_completion_time = scheduler.get_total_completion_time()

    # Print results
    print(f"FCFS Total Completion Time: {fcfs_completion_time}")
    print(f"SJF Total Completion Time: {sjf_completion_time}")

    # Compare and determine best algorithm
    if fcfs_completion_time < sjf_completion_time:
        print("FCFS minimizes completion time in this case.")
    else:
        print("SJF minimizes completion time in this case.")


if __name__ == "__main__":
    main()
