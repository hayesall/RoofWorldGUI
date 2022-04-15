from srlearn import Database
from srlearn.background import Background
from srlearn.rdn import BoostedRDN

train_db = Database.from_files("train_pos.txt", "train_neg.txt", "train_facts.txt")

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

rdn = BoostedRDN(
    background=bk,
    target="highpoint",
)

rdn.fit(train_db)
rdn.to_json("predict_highpoint_rdn.json")

test_db = Database.from_files("test_pos.txt", "test_neg.txt", "test_facts.txt")
y_pred = rdn.predict_proba(test_db)

print(y_pred)
