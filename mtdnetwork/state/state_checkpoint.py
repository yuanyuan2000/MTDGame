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
        last_checkpoint = 0
        while len(self._checkpoint_stack) > 0:
            checkpoint = self._checkpoint_stack.popleft()
            yield self.env.timeout(checkpoint - last_checkpoint)
            last_checkpoint = checkpoint
            NetworkState().save_network(time_network, self.env.now)
            AdversaryState().save_adversary(adversary, self.env.now)

    @staticmethod
    def load_states(time):
        time_network = NetworkState().load_network(time)
        adversary = AdversaryState().load_adversary(time)
        return time, time_network, adversary
