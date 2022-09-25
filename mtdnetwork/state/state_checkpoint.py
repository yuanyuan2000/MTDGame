from mtdnetwork.state.network_state import NetworkState
from mtdnetwork.state.adversary_state import AdversaryState
from collections import deque


class StateCheckpoint:

    def __init__(self, env=None, checkpoints=None):
        self.env = env
        self._checkpoint_stack = deque(checkpoints)

    def proceed_save(self, time_network, adversary):
        self.env.process(self.save_states(time_network, adversary))

    def save_states(self, time_network, adversary):
        while len(self._checkpoint_stack) > 0:
            checkpoint = self._checkpoint_stack.popleft()
            while self.env.now < checkpoint:
                yield self.env.timeout(1000)
            NetworkState().save_network(time_network, checkpoint)
            AdversaryState().save_adversary(adversary, checkpoint)

    @staticmethod
    def load_states(time):
        time_network = NetworkState().load_network(time)
        adversary = AdversaryState().load_adversary(time)
        return time, time_network, adversary
