import pickle
from mtdnetwork.event.adversary import Adversary
from mtdnetwork.state import State


class AdversaryState(State):
    def __init__(self):
        super().__init__()

    def save_adversary(self, adversary: Adversary, timestamp: float):
        """
        saving adversary state
        """
        adversary = adversary.clear_properties()
        file_name = self.save_file_by_time('adversary', timestamp)
        with open(file_name, 'wb') as f:
            pickle.dump(adversary, f, pickle.HIGHEST_PROTOCOL)

    def load_adversary(self, timestamp: float):
        """
        loading adversary based on saved state
        """
        if timestamp == 0:
            return
        file_name = self.load_file_by_time('adversary', timestamp)
        with open(file_name, 'rb') as f:
            adversary = pickle.load(f)
            return adversary
