import simpy
import random
import statistics

# Global vars
user_wait_times = []
admin_wait_times = []
SIMULATION_TIME = 180
WEBSITE_SIZE = 150

# count of entities
user = 0
admin = 0

# waiting variables
user_who_wait = 0
admin_who_wait = 0


class CloudProvider:
    def __init__(self, env, num_of_nodes, num_of_helpdesks, num_of_seniors):
        self.env = env
        self.node = simpy.Resource(env, num_of_nodes)
        self.helpdesk = simpy.Resource(env, num_of_helpdesks)
        self.senior = simpy.Resource(env, num_of_seniors)
        self.masternode = simpy.Resource(env, 1)
    
    def edit_cluster_config(self, user, service_time):
        yield self.env.timeout(service_time)

    def utilize_web_service(self, user, service_time):
        yield self.env.timeout(service_time) 

    def utilize_bucket_service(self, user, service_time):
        yield self.env.timeout(service_time)

    def call_help_service(self, user, service_time):
        yield self.env.timeout(service_time)

    def call_senior_help(self, user, service_time):
        yield self.env.timeout(service_time)

def esclate_to_senior(env, user, CloudProvider, problem, service_time):
    arrival_time = env.now
    # Request senior
    with CloudProvider.senior.request() as request:
        yield request
        yield env.process(CloudProvider.call_senior_help(user, service_time))
    
    time = env.now - arrival_time - service_time
    if time <= 0:
        user_wait_times.append(0)
    else:
        global user_who_wait
        user_who_wait = user_who_wait + 1
        user_wait_times.append(time)

def admin_panel(env, user, CloudProvider):
    service_time = random.randint(50,100)
    arrival_time = env.now
    # Request adminpanel
    with CloudProvider.masternode.request() as request:
        yield request
        yield env.process(CloudProvider.edit_cluster_config(user, service_time))

    time = env.now - arrival_time - service_time
    if time <= 0:
        admin_wait_times.append(0)
    else:
        global admin_who_wait
        admin_who_wait = admin_who_wait + 1
        admin_wait_times.append(time)

def open_website(env, user, is_admin, CloudProvider, internet_speed):
    service_time = random.randint(1,3) + WEBSITE_SIZE/internet_speed # Random time to browse + the speed of loading
    arrival_time = env.now
    # Request a node for web
    with CloudProvider.node.request() as request:
        yield request
        yield env.process(CloudProvider.utilize_web_service(user, service_time))

    time = env.now - arrival_time - service_time

    if time  <= 0:
        user_wait_times.append(0)
    elif is_admin:
        global admin_who_wait
        admin_who_wait = admin_who_wait + 1
        admin_wait_times.append(time)
    else:
        global user_who_wait
        user_who_wait = user_who_wait + 1
        user_wait_times.append(time)

def access_bucket(env, user, CloudProvider, internet_speed):
    file_size = random.randint(5,100) # Generate random file size
    service_time = file_size/internet_speed
    arrival_time = env.now
    # Request a node for web
    with CloudProvider.node.request() as request:
        yield request
        yield env.process(CloudProvider.utilize_bucket_service(user, service_time))
    
    time = env.now - arrival_time - service_time
    if time  <= 0:
        user_wait_times.append(0)
    else:
        global user_who_wait
        user_who_wait = user_who_wait + 1
        user_wait_times.append(time)

def call_helpdesk(env, user, CloudProvider):
    service_time = random.randint(2,5)
    senior_wait = 0
    arrival_time = env.now
    # Request for help desk
    with CloudProvider.helpdesk.request() as request:
            yield request
            yield env.process(CloudProvider.call_help_service(user, service_time))
    
    help_wait = env.now - arrival_time - service_time

    if random.randint(1,1) == 1:
        problem = random.choice(["software", "hardware"])
        if problem == "software":
            senior_time = random.randint(1,2)
        elif problem == "hardware":
            senior_time = random.randint(2,10)

        print(f"Esclated to senior with a {problem} problem")

        arrival_time = env.now
        esclate_to_senior(env, user, CloudProvider, problem, senior_time)
        senior_wait = env.now - arrival_time - senior_time

    time = help_wait + senior_wait

    if time  <= 0:
        user_wait_times.append(0)
    else:
        global user_who_wait
        user_who_wait = user_who_wait + 1
        user_wait_times.append(time)

def run_cloud(env, num_of_nodes, num_of_helpdesks, num_of_seniors):
    # Initlize the cloud
    cloud = CloudProvider(env, num_of_nodes, num_of_helpdesks, num_of_seniors)
    
    global user
    global admin

    while True:
        waited = 0
        user = user + 1 # Increment user
        if (random.randint(1,10) == 1):
            admin = admin + 1
            is_admin = True
            internet_speed = 1000 # Give admin internet speed
        else:
            is_admin = False
            internet_speed = random.randint(1, 10) # Give internet speed
   
        # The customer arrived right now
        arrival_time = env.now;
        print(f"user {user} (admin? {is_admin}) connected with internet speed {internet_speed} mb/s at time {round(arrival_time, 4)}")
        
        if is_admin:
            print("Accessed admin panel")
            env.process(admin_panel(env, user, cloud)) # Request admin panel

            if random.choice([True, False]):
                # Access site
                print("Accessed site")
                env.process(open_website(env, user, is_admin, cloud, internet_speed)) # Request website

        else:
            # Begin Customer cycle

            # Get help desk
            if random.choice([True, False]):
                print("Called help desk")
                env.process(call_helpdesk(env, user, cloud)) # Request help desk

            # Access site
            print("Accessed site")
            env.process(open_website(env, user, is_admin, cloud, internet_speed)) # Request website

            if random.choice([True, False]):
                print("Accessed bucket")
                env.process(access_bucket(env, user, cloud, internet_speed)) # Request help desk
            # End Customer cycle

        yield env.timeout(random.randint(10, 50)/60) # Randomized interarrival times
        
def get_avg_wait_time(wait_times, dividor):
    arrsum = sum(wait_times)
    avg_wait = arrsum/dividor
    # Calculate time
    minutes, frac_minutes = divmod(avg_wait, 1)
    seconds = frac_minutes * 60
    return round(minutes), round(seconds), arrsum

# Get user input
def user_input():
    num_of_nodes = input("Input # number of nodes: ")
    num_of_helpdesks = input("Input # number of desk employees: ")
    num_of_seniors = input("Input # number of senior employees: ")
    params = [num_of_nodes, num_of_helpdesks, num_of_seniors]
    if(all(str(i).isdigit for i in params)):
        params = [int(x) for x in params]
    else:
        print("Enter valid integer number, Simulation will use default node=1 helpdesks=1 seniors=1")
        params = [1,1,1]
    return params

def main():
    num_of_nodes, num_of_helpdesks, num_of_seniors = user_input()

    env = simpy.Environment()
    env.process(run_cloud(env, num_of_nodes, num_of_helpdesks, num_of_seniors))
    env.run(until=SIMULATION_TIME)

    umins, usecs, usum = get_avg_wait_time(user_wait_times, user)
    amins, asecs, asum = get_avg_wait_time(admin_wait_times, admin)
    print(f"The avg wait time for users is {umins} minutes and {usecs} seconds")
    print(f"The avg wait time for admins is {amins} minutes and {asecs} seconds")
    print(f"The probabity of wait time for users is {round(user_who_wait/user,2)}")
    print(f"The probabity of wait time for admins is {round(admin_who_wait/admin,2)}")
    print(f"Average time for users who wait is {round(usum/user_who_wait,2)}")
    print(f"Average time for admins who wait is {round(asum/admin_who_wait,2)}")

main()