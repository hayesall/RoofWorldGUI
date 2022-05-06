# Copyright © 2022 Alexander L. Hayes

"""
``estimate_performance.py``
===========================

Performance 5-fold cross validation for predicting whether
a keypoint in a building is a "high point" or a "low point."
"""

from time import time
import os

from roofworld.exporter import Network
from gui import FlatWorld

from srlearn.rdn import BoostedRDNClassifier
from srlearn import Background
from relational_datasets.types import RelationalDataset

import numpy as np
from sklearn.model_selection import KFold
from sklearn.metrics import classification_report
from sklearn.metrics import f1_score



buildings = np.array([file for file in os.listdir("saved")])

bk = Background(
    modes=[
        "highpoint(+node).",
        "connected(+node,-node).",
        "connected(-node,+node).",
        "nneighbors(+node,#neighborcount).",
        "angledegrees(+node,+node,-node,#angletype).",
        "angledegrees(+node,-node,+node,#angletype).",
        "angledegrees(+node,-node,-node,#angletype).",
    ],
)

kf = KFold(n_splits=5, shuffle=True)
f1_scores = []


for i, (train_id, test_id) in enumerate(kf.split(buildings)):

    start_id = 0

    train_pos, train_neg, train_facts = [], [], []
    test_pos, test_neg, test_facts = [], [], []

    for filename in buildings[train_id]:

        fw = FlatWorld.from_json("saved/" + filename)
        net = Network(fw.points, fw.lines, start=start_id)
        data = net.describe()

        start_id += len(fw.points)

        train_pos += data.pos
        train_neg += data.neg
        train_facts += data.facts

    for filename in buildings[test_id]:

        fw = FlatWorld.from_json("saved/" + filename)
        net = Network(fw.points, fw.lines, start=start_id)
        data = net.describe()

        start_id += len(fw.points)

        test_pos += data.pos
        test_neg += data.neg
        test_facts += data.facts

    train_db = RelationalDataset(train_pos, train_neg, train_facts)
    test_db = RelationalDataset(test_pos, test_neg, test_facts)

    rdn = BoostedRDNClassifier(
        background=bk,
        target="highpoint",
        solver="SRLBoost",
    )

    ts = time()
    rdn.fit(train_db)
    te = time()
    print(f"Finished in {te - ts} seconds")

    rdn.to_json(f"highpoint_rdn_fold_{i}.json")

    y_pred = rdn.predict(test_db)
    y_true = rdn.classes_

    print(classification_report(y_true, y_pred))

    f1_scores.append(f1_score(y_true, y_pred))

print(np.mean(f1_scores))
