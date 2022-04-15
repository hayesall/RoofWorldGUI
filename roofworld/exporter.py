# Copyright 2022 Alexander L. Hayes
# MIT License

from relational_datasets.types import RelationalDataset
from itertools import combinations
import numpy as np
from numpy.linalg import norm


def points_to_degrees(A, B, C):
    a = np.array(A)
    b = np.array(B)
    c = np.array(C)
    ba = a - b
    bc = c - b
    return np.arccos((ba @ bc) / (norm(ba) * norm(bc))) * (180 / np.pi)


def discretize_angles(degrees: float | int):
    # Discretize degrees into categories: acute, right, obtuse, straight
    degrees = round(degrees)
    if degrees < 90:
        return "acuteangle"
    if degrees == 180:
        return "straightline"
    if degrees == 90:
        return "rightangle"
    return "obtuseangle"


class Network:

    def __init__(self, point_list, line_list, start=0):
        # We need to enumerate N = len(point_list) points
        self.size = len(point_list)

        _network = {}
        _ids = {}
        _attributes = {}

        for i, pnt in enumerate(point_list):
            _network[pnt] = []
            _ids[pnt] = i + start

            # Binarize the black/orange
            _attributes[pnt] = point_list[pnt] != (0, 0, 0)

        for ((x1, y1), (x2, y2)) in line_list:
            _network[(x1, y1)].append((x2, y2))
            _network[(x2, y2)].append((x1, y1))

        self._ids = _ids
        self._network = _network
        self._attributes = _attributes

    def describe(self):

        pos = []
        neg = []
        facts = []

        for key in self._network:

            if self._attributes[key]:
                pos.append(f"highpoint(v{self._ids[key]}).")
            else:
                neg.append(f"highpoint(v{self._ids[key]}).")

            facts.append(f"nneighbors(v{self._ids[key]},{len(self._network[key])}).")

            for pnt in self._network[key]:
                facts.append(f"connected(v{self._ids[key]},v{self._ids[pnt]}).")
                facts.append(f"connected(v{self._ids[pnt]},v{self._ids[key]}).")

            if len(self._network[key]) == 2:

                a, c = self._network[key]
                deg = discretize_angles(points_to_degrees(a, key, c))

                k_id = self._ids[key]
                a_id = self._ids[a]
                c_id = self._ids[c]

                facts.append(f"angledegrees(v{k_id},v{a_id},v{c_id},{deg}).")
                facts.append(f"angledegrees(v{k_id},v{c_id},v{a_id},{deg}).")

            if len(self._network[key]) > 2:

                k_id = self._ids[key]

                for a, c in combinations(self._network[key], 2):

                    deg = discretize_angles(points_to_degrees(a, key, c))

                    a_id = self._ids[a]
                    c_id = self._ids[c]

                    facts.append(f"angledegrees(v{k_id},v{a_id},v{c_id},{deg}).")
                    facts.append(f"angledegrees(v{k_id},v{c_id},v{a_id},{deg}).")

        return RelationalDataset(pos, neg, facts)

class PredicateLogicExporter:

    def __init__(self, n=0):
        self.n = n

    def export(self):
        pass
