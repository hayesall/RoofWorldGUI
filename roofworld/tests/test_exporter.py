# Copyright 2022 Alexander L. Hayes

from roofworld.exporter import discretize_angles


def test_obtuse_cases():
    assert discretize_angles(125) == "obtuseangle"
    assert discretize_angles(90.6) == "obtuseangle"
    assert discretize_angles(91) == "obtuseangle"
    assert discretize_angles(92) == "obtuseangle"
    assert discretize_angles(181) == "obtuseangle"
    assert discretize_angles(270) == "obtuseangle"
    assert discretize_angles(179) == "obtuseangle"
    assert discretize_angles(359) == "obtuseangle"

def test_rightangle_cases():
    assert discretize_angles(90) == "rightangle"
    assert discretize_angles(90.0) == "rightangle"
    assert discretize_angles(90.1) == "rightangle"
    assert discretize_angles(90.000001) == "rightangle"
    assert discretize_angles(89.999998) == "rightangle"
    assert discretize_angles(89.9) == "rightangle"

def test_straightline_cases():
    assert discretize_angles(180) == "straightline"
    assert discretize_angles(179.99998) == "straightline"
    assert discretize_angles(180.00001) == "straightline"
    assert discretize_angles(179.9) == "straightline"
    assert discretize_angles(180.1) == "straightline"
    assert discretize_angles(180.0) == "straightline"

def test_acuteangle_cases():
    assert discretize_angles(27) == "acuteangle"
    assert discretize_angles(15) == "acuteangle"
    assert discretize_angles(89.0) == "acuteangle"
    assert discretize_angles(89.1) == "acuteangle"
    assert discretize_angles(1.0) == "acuteangle"
