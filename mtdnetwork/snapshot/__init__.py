import os

current_directory = os.getcwd()


class Snapshot:
    def __init__(self):
        if not os.path.exists(current_directory+'\\snapshots'):
            os.makedirs(current_directory+'\\snapshots')

    @staticmethod
    def get_file_by_time(file_name: str, timestamp: float):
        return current_directory+'\\snapshots\\' + file_name + '_' + str(timestamp) + '.pkl'
