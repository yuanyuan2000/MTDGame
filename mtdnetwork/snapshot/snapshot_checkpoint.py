from mtdnetwork.snapshot.network_snapshot import NetworkSnapshot
from mtdnetwork.snapshot.adversary_snapshot import AdversarySnapshot
from collections import deque


class SnapshotCheckpoint:

    def __init__(self, env=None, checkpoints=None):
        self.env = env
        self._proceed_time = 0
        self._checkpoint_stack = checkpoints

    def proceed_save(self, time_network, adversary):
        if self._checkpoint_stack is not None:
            self._checkpoint_stack = deque(self._checkpoint_stack)
        self.env.process(self.save_snapshots(time_network, adversary))

    def save_snapshots(self, time_network, adversary):
        last_checkpoint = self._proceed_time
        while len(self._checkpoint_stack) > 0:
            checkpoint = self._checkpoint_stack.popleft()
            if checkpoint < last_checkpoint:
                continue
            yield self.env.timeout(checkpoint - last_checkpoint)
            last_checkpoint = checkpoint
            NetworkSnapshot().save_network(time_network, self.env.now + self._proceed_time)
            AdversarySnapshot().save_adversary(adversary, self.env.now + self._proceed_time)

    def load_snapshots(self, time):
        self.set_proceed_time(time)
        time_network = NetworkSnapshot().load_network(time)
        adversary = AdversarySnapshot().load_adversary(time)
        return time_network, adversary

    def save_initialised(self, time_network, adversary):
        NetworkSnapshot().save_network(time_network, self._proceed_time)
        time_network.draw()
        AdversarySnapshot().save_adversary(adversary, self._proceed_time)

    def set_proceed_time(self, proceed_time):
        self._proceed_time = proceed_time
