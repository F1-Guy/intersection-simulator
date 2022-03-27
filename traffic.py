from enum import Flag
from typing import List, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
from os import path

####################################
# You do not need to change any values in the code itself
# All changes to lane and traffic light configuration can be done in the JSON file directly
# Make sure to include config.json file within the script folder
# Make sure that the config files includes all constans and 
# lane objects you would like to include into your code
####################################

CONFIG_PATH = "config.json"

# Backup global constatns in case the config file is inccorect or missing
# Values are defined in seconds
GREEN_CARS = 30 # Duration of green light for cars
GREEN_BIKES = 10 # Duration of green light for bikes
RED_TIME_ALL = 10 # Duration of red light for all vehicles
CYCLE_LENGTH = GREEN_CARS + GREEN_BIKES + 2 * RED_TIME_ALL # Total cycle length

# Value is defined in hours (eg. 1 means it is goig to run for 3600 seconds (1h))
SIM_LENGTH = 0.1

class LaneType:
    """Number of Car and Bikes which pass trough the intersection per time unit
    """
    CAR = 1
    BIKE = 2


class Lane:
    """Contains a defintion with attributes describing the each lane object and a method for updating the number of the vehicles in the queue
    """
    def __init__(self, lane_type : int, business: float):
        self.green_light = False # True if GREEN, False if RED
        self.vehicle_num = 0
        self.lane_type = lane_type
        self.business = business


    def update_vehicle_number(self) -> None:
        """Adds random number (based on the business value of the lane) of vehicles to the queue and removes them if conditions are met
        """
        # Add random nuber of vehicles to lane based on business
        self.vehicle_num += np.random.poisson(self.business)

        # Removes vehicles from lane per conditions
        if self.green_light and (self.vehicle_num > 0):
            #To prevent negative bike numbers snice they usually move two at a time
            if self.lane_type == LaneType.BIKE and (self.vehicle_num == 1):
                self.vehicle_num -= 1
            else:
                self.vehicle_num -= self.lane_type


class JsonReader:
    """Helper class to read the config.json file that sets the default values if the file is missing or incorrect. It can also return
    a None value in case the configuration file could not be read correctly
    """
    staticmethod
    def parse(filename : str) -> List[Lane]:
        """Takes a string with the filename as paramater and returns a list of lane object initialized to the values from the file
        """
        lanes = []

        # Varables that need to be changed outside the method
        global GREEN_CARS
        global GREEN_BIKES
        global RED_TIME_ALL
        global SIM_LENGTH
        global CYCLE_LENGTH
        
        print("Reading configuration file")

        # If the config file exsits with the proper name
        if path.exists(CONFIG_PATH):
            # Open file in read mode
            with open(filename, "r") as f:
                try:
                    j = json.load(f)
                except json.decoder.JSONDecodeError:
                    print("WARNING: Configuration file is not properly formated")
                    return lanes
                
                # Checks if values are set in JSON file otherwise it sets defaults
                GREEN_CARS = j["GREEN_CARS"] if "GREEN_CARS" in j else GREEN_CARS
                GREEN_BIKES = j["GREEN_BIKES"] if "GREEN_BIKES" in j else GREEN_BIKES
                RED_TIME_ALL = j["RED_TIME_ALL"] if "RED_TIME_ALL" in j else RED_TIME_ALL
                SIM_LENGTH = j["SIM_LENGTH"] if "SIM_LENGTH" in j else SIM_LENGTH
                CYCLE_LENGTH = GREEN_CARS + GREEN_BIKES + 2 * RED_TIME_ALL

                # If lanes in json exist it returns them, otherwise returns empty list
                if not "lanes" in j:
                    return lanes
                
                # Creates lane objects from the file and places them in a list
                for lane in j["lanes"]:
                    lane_type = LaneType.CAR if lane["type"] == "car" else LaneType.BIKE
                    lanes.append(Lane(lane_type, lane["business"]))

                return lanes     
        # If the file doesn't exist
        else:
            print(f"WARNING: File '{CONFIG_PATH}' was not found in the script folder")
            return lanes


class Main:
    """Main function called at program startup that contains main execution order
    """
    def __init__(self):
        # lane_count is only used if the JSON is not correctly read or is missing
        self.lane_count = 4

        self.columns = []
        self.lanes = []

        # Creates lane objects based on the numbers of lanes in the config file
        self.lanes = JsonReader.parse(CONFIG_PATH)

        # If lanes list is empty
        if self.lanes:
            # Sorts bikes and car lanes intro seperate list for graph drawing
            bikes = list(filter(lambda a: a.lane_type == LaneType.BIKE, self.lanes))
            cars = list(filter(lambda a: a.lane_type == LaneType.CAR, self.lanes))
            # Dinamically adds names for line chart for bikes
            self.columns.append("bikelight")
            for i in range(len(bikes)):
                self.columns.append("Bikes " + str(i+1))
        
            # Dinamically adds names for line chart for bikes
            self.columns.append("carlight")
            for i in range(len(cars)):
                self.columns.append("Cars " + str(i+1))
    
        # Fallbak scenario in case there are not any lanes in the config file
        else:
            print("WARNING: Using default configuration for simulation")
            self.columns = ['Bike lanes', 'Bikes 1', 'Bikes 2', 
                    'Car lanes', 'Cars 1', 'Cars 2']
            # Automatic lane generation with preset buissines values
            for i in range(self.lane_count):
                lane_type = LaneType.BIKE if i >= self.lane_count / 2 else LaneType.CAR
                self.lanes.append(Lane(lane_type, (self.lane_count - i) * 0.1))

        self.bikes = list(filter(lambda a: a.lane_type == LaneType.BIKE, self.lanes))
        self.cars = list(filter(lambda a: a.lane_type == LaneType.CAR, self.lanes))

        # Crate pandas dataframe
        self.traffic_data = pd.DataFrame(columns=self.columns)
        print("Running simulation...")
        # The loop is iterated every second for SIM_LENGTH hours
        loop_count = int(3600 * SIM_LENGTH)
        for i in range(loop_count):
            self.loop(i)
        
        # Displays the graph once the program is finished running
        self.draw_graph()
    

    def set_lanes(self, lane_type : int, status : bool) -> None:
        """Sets the status of the lane traffic light based on input parameters
        """
        for lane in self.lanes:
            if lane.lane_type == lane_type:
                lane.green_light = status
    

    # Loop is ran on every unit of time
    def loop(self, iter_count : int) -> None:
        """Runs every unit of time and checks for lane state changes
        """
        # Ticks has a domain of 0 to CYCLE_LENGTH - 1
        ticks = iter_count % CYCLE_LENGTH

        # Cycles through traffic light on specific ticks
        if ticks == 0:
            self.set_lanes(LaneType.CAR, False)
            self.set_lanes(LaneType.BIKE, True)
        elif ticks == GREEN_BIKES:
            self.set_lanes(LaneType.BIKE, False)
        elif ticks == GREEN_BIKES + RED_TIME_ALL:
            self.set_lanes(LaneType.CAR, True)
        elif ticks == GREEN_BIKES + RED_TIME_ALL + GREEN_CARS:
            self.set_lanes(LaneType.CAR, False)
        
        # Update the vehicle queues
        for lane in self.lanes:
            lane.update_vehicle_number()

        # Update traffic data
        self.add_row(iter_count)


    def draw_graph(self) -> None:
        """Draws the grpah dinamicaly based on simulation parameters
        """
        print("Displaying the graph")
        ax_traffic = self.traffic_data.plot(figsize=(20,10))
        ax_traffic.set_ylim(0,25)
        ax_traffic.set_xlim(0,SIM_LENGTH*3600) #Resizes the x axis according to simulation lenght
        ax_traffic.set_title('Lenght of the queue', size=16)
        ax_traffic.set_ylabel('Number of vehicles waiting')
        ax_traffic.set_xlabel('Amount of time passed since beginning')
        plt.show()
    

    def add_row(self, index : int) -> None:
        """Helper function for grpah drawing to draw number of vehicles in one ponit in time
        """
        final = []
        
        final.append(self.bikes[0].green_light) if len(self.bikes) > 0 else 0
        for bike in self.bikes:
            final.append(bike.vehicle_num)
        
        final.append(self.cars[0].green_light) if len(self.cars) > 0 else 0
        for car in self.cars:
            final.append(car.vehicle_num)
        
        self.traffic_data.loc[index] = final
                 

if __name__ == "__main__":
    Main()