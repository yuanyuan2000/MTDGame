from mtdnetwork.state.network_state import NetworkState
from mtdnetwork.state.adversary_state import AdversaryState
from collections import deque


class StateCheckpoint:

    def __init__(self, env=None,  checkpoints=None):
        self.env = env
        self._proceed_time = 0
        self._checkpoint_stack = checkpoints

    def proceed_save(self, time_network, adversary):
        if self._checkpoint_stack is not None:
            self._checkpoint_stack = deque(self._checkpoint_stack)
        self.env.process(self.save_states(time_network, adversary))

    def save_states(self, time_network, adversary):
        last_checkpoint = self._proceed_time
        while len(self._checkpoint_stack) > 0:
            checkpoint = self._checkpoint_stack.popleft()
            if checkpoint < last_checkpoint:
                continue
            yield self.env.timeout(checkpoint - last_checkpoint)
            last_checkpoint = checkpoint
            NetworkState().save_network(time_network, self.env.now + self._proceed_time)
            AdversaryState().save_adversary(adversary, self.env.now + self._proceed_time)

    def load_states(self, time):
        self.set_proceed_time(time)
        time_network = NetworkState().load_network(time)
        adversary = AdversaryState().load_adversary(time)
        return time_network, adversary

    def set_proceed_time(self, proceed_time):
        self._proceed_time = proceed_time
