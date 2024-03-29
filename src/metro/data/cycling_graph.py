import networkx as nx
import numpy as np
import pandas as pd
from collections import defaultdict
class CyclingGraph():
    def __init__(self):
        self.graph = nx.DiGraph()
        self.node2station = {} # Contains a link from a gaph node to the corresponding station (multiple node can correspond to the same station, if they are on opposite direction or on a different line)
        self.node2station_side = {}
        self.node2line = {}
        self.n_lines = 0

    def add_line(self, stations, weight: float, cycle: bool):
        """
        Creates an independant line in the disconnected graph.
        Saves the information to join the graph afterwards.
        """
        cycle_stations = stations + stations[::-1]
        station_sides = [0]*len(stations) + [1]*len(stations)
        offset = self.graph.number_of_nodes()
        nodes = [s + offset for s, _ in enumerate(cycle_stations)]
        for station, node, station_side in zip(cycle_stations, nodes, station_sides):
            self.node2station[node] = station
            self.node2station_side[node] = station_side

        for node in nodes:
            self.node2line[node] = self.n_lines

        if cycle:
            base_nodes = nodes
            shifted_nodes = np.roll(nodes, -1)
        else:
            base_nodes = nodes[:-1]
            shifted_nodes = nodes[1:]
        for station_a, station_b in zip(base_nodes, shifted_nodes):
            self.graph.add_edge(station_a, station_b, weight=weight)
            self.graph.add_edge(station_a, station_a, weight=1-weight)

        if not cycle:
            self.graph.add_edge(shifted_nodes[-1], shifted_nodes[-1], weight=1)

        self.n_lines += 1

    def merge_graph(self):
        station2line = defaultdict(list)
        G = self.graph.copy()
        for k, v in self.node2station.items():
            station2line[v].append(k)
        for station, values in station2line.items():
            base = values[0]
            for node in values[1:]:
                G = nx.contracted_nodes(G, base, node)
        G = nx.relabel_nodes(G, self.node2station)
        return G
    
    def adjacency_matrix(self):
        A = nx.adjacency_matrix(self.graph, weight='weight').T
        return A.todense()

    def simulate_merge(self, init_vector, step_nb: int):
        """Simulates the steps of flow in the graph when initialized with a given vector."""
        A = nx.adjacency_matrix(self.graph, weight='weight').T
        x = init_vector
        X = [x]
        for _ in range(step_nb-1):
            x = A@x
            X.append(
                x
            )
        X_merged = self.merge_X(np.array(X))
        return X_merged
    
    def simulate_stack(self, init_vector, step_nb: int):
        """Simulates the steps of flow in the graph when initialized with a given vector."""
        A = nx.adjacency_matrix(self.graph, weight='weight').T
        x = init_vector
        X = [x]
        for _ in range(step_nb-1):
            x = A@x
            X.append(
                x
            )
        X_stacked = self.stack_X(np.array(X))
        return X_stacked

    def num_stations(self):
        return len(set(self.node2station.values()))

    def merge_X(self, X):
        stations = set(self.node2station.values())
        merged_X = {station: np.zeros(X.shape[0]) for station in stations}
        for x in range(X.shape[1]):
            station = self.node2station[x]
            merged_X[station] = merged_X[station] + X[:,x]
        return merged_X
    
    def stack_X(self, X):
        stations = set(self.node2station.values())
        merged_X = {station: np.zeros((2, X.shape[0])) for station in stations}
        for x in range(X.shape[1]):
            station = self.node2station[x]
            side = self.node2station_side[x]
            merged_X[station][side] = merged_X[station][side] + X[:,x]
        return merged_X
    
    def random_initialization(self, low, high):
        return np.random.randint(low, high, size=len(self.graph.nodes()))