class MTD:
    def __init__(self, name: str, mtd_type: str, resource_type: str, execution_time_mean: float,
                 execution_time_std: float, network):
        self._name = name
        self._mtd_type = mtd_type
        self._resource_type = resource_type
        self._execution_time_mean = execution_time_mean
        self._execution_time_std = execution_time_std
        self.network = network

    def mtd_operation(self, adversary=None):
        raise NotImplementedError

    def __str__(self):
        return self._name + ' ' + self._resource_type + ' ' + str(self._execution_time_mean)

    def get_mtd_type(self):
        return self._mtd_type

    def get_resource_type(self):
        return self._resource_type

    def get_name(self):
        return self._name

    def get_execution_time_mean(self):
        return self._execution_time_mean

    def get_execution_time_std(self):
        return self._execution_time_std
