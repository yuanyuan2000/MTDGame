import networkx as nx
from mtdnetwork.data.constants import OS_TYPES, OS_VERSION_DICT
import matplotlib.pyplot as plt
import numpy as np
from mtdnetwork.statistic.utils import powerset, remove_element
from pulp import *


class DiversityAssignment:
    def __init__(self, graph, sources, dests, services, pos, colour_map):
        """
        MIP formulation for sovling Diversity Assignment Problem

        :param N: routing nodes (hosts)
        :param M: client nodes (exposed hosts + database)
        :param V: OS variants
        :param E: E=V compromise events
        """

        self._graph = graph
        self._sources = sources
        self._dests = dests
        self._pos = pos
        self._services = services
        self._colour_map = colour_map
        self.total_nodes = len(self._pos)
        self.flag = False

    def gen_single_connection_graph(self):
        """
        single source - routing nodes - single destination
        """
        if self.flag:
            return self._graph
        total_nodes = self.total_nodes
        dap_graph = self._graph
        for i in range(1, len(self._sources), 1):
            neighbors = list(dap_graph.neighbors(i))
            for neighbor in neighbors:
                dap_graph.add_edge(0, neighbor)
            dap_graph.remove_node(i)
            del self._pos[i]
            del self._colour_map[1]

        for j in range(total_nodes - len(self._dests) - 1, total_nodes - 1, 1):
            neighbors = list(dap_graph.neighbors(j))
            for neighbor in neighbors:
                dap_graph.add_edge(total_nodes - 1, neighbor)
            dap_graph.remove_node(j)
            del self._pos[j]
            del self._colour_map[-2]
        self.flag = True
        return dap_graph

    def draw_dap_graph(self):
        dap_graph = self.gen_single_connection_graph()
        plt.figure(1, figsize=(15, 12))
        nx.draw(dap_graph, pos=self._pos, node_color=self._colour_map, with_labels=True)
        plt.savefig('data_analysis/dap_network.png')

    def calculate_variant_compromise_prob(self):
        """
        os_services: {os_type: [{os_version: [{service_name: [Service1, Service2, ...]}]}]}

        services are generated with a list of vulnerabilities
        services are compatible with certain OS Type and OS version

        Compromise Probability:
            1. calculate the mean of the mean of the cvss of vulnerabilities in each service running on each OS Type.
            2. compromise probability = 1 / AC

        Variant -> OS Type


        1 host -> 1 service -> list of vulnerabilities

        1 vulnerability -> cvss = (complexity + impact) / 2

        service cvss -> sum (vulnerability cvss)

        os cvss -> mean (service cvss)

        compromise probability -> 1 / os cvss
        """

        # initialise variants
        V = {}
        E = {}
        for os_type in OS_TYPES:
            for os_version in OS_VERSION_DICT[os_type]:
                V[os_type] = []
        # extract variants from generated services
        os_services = self._services

        for os_type in OS_TYPES:
            for os_version in OS_VERSION_DICT[os_type]:
                for service_name in os_services[os_type][os_version]:
                    for service in os_services[os_type][os_version][service_name]:
                        V[os_type].append(np.sum([vuln.cvss for vuln in service.vulnerabilities]))
            E[os_type] = 1 / np.mean(V[os_type])
        return E

    def objective(self):
        # generate single connection graph
        dap_graph = self.gen_single_connection_graph()

        # calculate compromise event E
        E = self.calculate_variant_compromise_prob()

        # get all sets of compromise events C
        C = list(powerset(E.keys()))

        # client nodes
        M = [list(dap_graph.nodes)[0], list(dap_graph.nodes)[-1]]

        # routing nodes
        N = list(dap_graph.nodes)[1:-1]

        # edges
        w = list(dap_graph.edges)

        # Create the 'prob' variable to contain the problem data
        prob = LpProblem("Diversity Assignment Problem", LpMaximize)

        # Define the decision variables
        f = LpVariable.dicts('f', [(c, a, i, j) for c in C for a in M for i in M + N for j in M + N if j != i],
                             lowBound=0, cat='Continuous')
        s = LpVariable.dicts("s", [(v, x) for v in E.keys() for x in N], lowBound=0, upBound=1, cat='Binary')

        # Define the objective function
        prob += 0.5 * (len(M) * (len(M) - 1) / 2) ** (-1) * lpSum([[
            E[e] * f[(c, a, a, x)] if e in c else (1 - E[e]) * f[(c, a, a, x)]
            for e in E.keys()] for c in C for a in M for x in N])

        # Define the constraints
        for x in N:
            prob += lpSum([s[(v, x)] for v in E.keys()]) == 1

        for c in C:
            for a in M:
                prob += lpSum(f[(c, a, x, i)] for x in N for i in remove_element(a, N + M) if x != i) - lpSum(
                    f[(c, a, i, x)] for x in N for i in N + [a] if x != i) == 0

                prob += lpSum([f[(c, a, x, b)] for b in M if b != a for x in N if x != b]) <= 1

                prob += lpSum([f[(c, a, x, a)] for a in M for x in N if x != a]) == 0

                prob += lpSum([f[(c, a, b, x)] for a in M for b in M if b != a for x in N]) == 0

                prob += lpSum([f[(c, a, i, j)] if (i, j) in w else f[(c, a, i, j)] <= (len(M) - 1) * 1
                               for i in N + M for j in N + M if i != j]) <= 0

                prob += lpSum([f[(c, a, x, i)] - 1 for x in N for i in N + M if i != x]) <= 0

                prob += lpSum([f[(c, a, i, x)] - 1 for x in N for i in N + M if i != x]) <= 0

                # prob += lpSum([f[(c, a, x, i)] - (len(M) - 1) * (1 - min([s[(v, x)] for v in E.keys() for x in N]))
                #                for x in N for i in N + M if i != x]) <= 0
                #
                # prob += lpSum([f[(c, a, i, x)] - (len(M) - 1) * (1 - min([s[(v, x)] for v in E.keys() for x in N]))
                #                for x in N for i in N + M if i != x]) <= 0

        # Solve the problem
        prob.solve()
        # Print the status of the solution
        print("Status:", LpStatus[prob.status])

        # Print the optimal value of the objective function
        print("Objective value:", value(prob.objective))

        # Print the values of the decision variables
        for v in prob.variables():
            if 's_' in v.name and v.varValue == 1.0:
                print(v.name, "=", v.varValue)

    @staticmethod
    def expected_client_connectivity(F, E, C):
        """

        :param F: a list of connectivity value corresponding to each compromise event set 'c'
                    (sum(math.comb(2, 2) ** -1))
        :param E: {variant : compromise probability}
        :param C: powerset of variants
        :return:
        """
        # todo: check if reachable to get F
        # nx.has_path(G, source, target)
        # F = [0, 1] 0: disconnected, 1: connected

        ecc = 0  # initialize expected client connectivity to 0
        for i in range(len(C)):  # iterate over all subsets of failed connections
            prod = 1  # initialize product term to 1
            for variant in E:  # iterate over all variant in E
                if variant in C[i]:  # if variant is in c
                    prod *= E[variant]  # multiply by the probability of failure
                else:
                    prod *= (1 - E[variant])  # multiply by the probability of not failing
            ecc += prod * F[i]  # add product term times sum term to ecc
        return ecc


"""
DAP

connectivity function for client a and b: binom(M, 2) ** -1

P(e): the probability of compromise event e occurring.

e.g. two variants v1, v2 -> c = (e1, e2, e3, e4)

ECC = sum( P(e)* (1-P(e))  * sum(connectivity function) )

DAP = argmax(ECC)

1. problems for connectivity function: one type (client only) vs two types (client & database)? 

2. how can we determine the probability of compromise of each variant?

 - compromise event e = OS variant v, 
 - but the variants in our model are vulnerabilities on services?


"""

"""
objective function

Relationship between DAP function and its objective function and constraints?


"""

"""
constraint

1. Routing nodes must be exactly one variant.

2. flow cannot get stuck in the middle of the network; it has to end at client nodes.

3. A client cannot accept more than one unit of flow from another client.

4. Traffic cannot start and end at the same client.

5. A destination client cannot send out flow. So, flow cannot use a client to reach other clients.

6. Any pair of nodes with no edge between them cannot have any flow directly between them.
(up to |M| - 1 units of flow originating at the same client can share the same edge.)

7. The amount of flow out of / into a routing node must be 0 if that node is compromised.

"""

"""
tools:

CPLEX, PULP


"""
