import os

current_directory = os.getcwd()


class State:
    def __init__(self):
        if not os.path.exists(current_directory+'\\mtdnetwork\\state\\data'):
            os.makedirs(current_directory+'\\mtdnetwork\\state\\data')

    @staticmethod
    def save_file_by_time(file_name: str, timestamp: float):
        return current_directory+'\\mtdnetwork\\state\\data\\' + file_name + '_' + str(timestamp) + '.pkl'

    @staticmethod
    def load_file_by_time(file_name, timestamp: float):
        return current_directory+'\\mtdnetwork\\state\\data\\' + file_name + '_' + str(timestamp) + '.pkl'
