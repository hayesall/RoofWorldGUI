# Copyright © 2022 Alexander L. Hayes
# MIT License

"""
Perform inference on a network of 2D points and lines connecting them.

Example Usage
-------------

.. code-block:: python

    from roofworld.model import RoofPointClassifier

    points = {(400, 175): (0, 0, 0), (400, 250): (0, 0, 0), (500, 175): (0, 0, 0), (500, 250): (0, 0, 0)}
    lines = [((400, 175), (500, 175)), ((500, 175), (500, 250)), ((500, 250), (400, 250)), ((400, 250), (400, 175))]

    clf = RoofPointClassifier()
    clf.predict_proba(points, lines)


"""

import pathlib
from srlearn.rdn import BoostedRDNClassifier
from .exporter import Network


class RoofPointClassifier:

    def predict_proba(self, points, lines):

        _here = pathlib.Path(__file__).parent
        _parameters = _here.joinpath("predict_highpoint_rdn.json")

        net = Network(points, lines)
        data = net.describe()

        clf = BoostedRDNClassifier(solver="SRLBoost")
        clf.from_json(_parameters)
        return clf.predict_proba(data)
