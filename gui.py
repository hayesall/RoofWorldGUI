# Copyright © 2022 Alexander L. Hayes

"""
Controls:

- Left Mouse: Place points or toggle point color
- Right Mouse: Draw lines connecting two points

- `b`: Turn off graph paper / gray background mode (helpful for taking screenshots)
- `c`: Reset
- `s`: Save.
"""

import argparse
from copy import deepcopy
from datetime import datetime
from enum import Enum
import json
import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

from roofworld.exporter import Network

import matplotlib.pyplot as plt
import pygame
from srlearn.rdn import BoostedRDNClassifier
from srlearn import Database


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LIGHTGRAY = (250, 250, 250)
LIGHTBLUE = (150, 173, 233)
ORANGE = (255, 165, 0)

WIDTH, HEIGHT = 1000, 600

SPACING = 25
LINE_MODE = None


def myround(x, base=25):
    return base * round(x / base)


def draw_graphpaper(screen, k):
    for i in range(WIDTH // k):
        x = k * i
        y = k * i
        pygame.draw.line(screen, LIGHTBLUE, (x, 0), (x, HEIGHT), 1)
        pygame.draw.line(screen, LIGHTBLUE, (0, y), (WIDTH, y), 1)



class Operations(Enum):
    ADD_POINT = 1
    ADD_LINE = 2
    TOGGLE_POINT = 3
    RESET = 4


class FlatWorld:
    def __init__(self):
        self.operations = []
        self.points = {}
        self.lines = []

    @staticmethod
    def from_json(file_path: str):

        with open(file_path, "r") as fh:
            points, lines = json.loads(fh.read())

        # Unmap the points
        pnts = {}
        for entry in points:
            pnts[tuple(entry["point"])] = tuple(entry["color"])

        fw = FlatWorld()
        fw.points = pnts
        fw.lines = lines

        return fw

    def to_json(self, file_path: str):

        # Remap the points to a list, since JSON doesn't recognize tuple dictionaries
        pnts_list = []
        for k, v in self.points.items():
            pnts_list.append({
                "point": k,
                "color": v,
            })

        with open(file_path, "w") as fh:
            fh.write(json.dumps([pnts_list, self.lines]))

    def dump_state(self):

        print(self.points)
        print(self.lines)

        net = Network(self.points, self.lines)
        database = net.describe()

        for example in database.pos + database.neg:
            print(example)
        print("\n")
        for fact in database.facts:
            print(fact)
        print("\n")

    def predict(self):

        net = Network(self.points, self.lines)
        database = net.describe()

        db = Database()
        db.pos = database.pos + database.neg
        db.neg = []
        db.facts = database.facts

        rdn = BoostedRDNClassifier()
        rdn.from_json("roofworld/predict_highpoint_rdn.json")

        zs = rdn.predict_proba(db)

        xs = [x for (x, _) in self.points]
        ys = [y for (_, y) in self.points]

        fig = plt.figure()
        ax = fig.add_subplot(projection="3d")
        ax.scatter(xs, ys, zs, cmap="gray")
        plt.show()

    def export(self, start=0):
        net = Network(self.points, self.lines, start=start)

        database = net.describe()

        with open("pos.txt", "a") as fh:
            for ex in database.pos:
                fh.write(ex + "\n")
        with open("neg.txt", "a") as fh:
            for ex in database.neg:
                fh.write(ex + "\n")
        with open("facts.txt", "a") as fh:
            for ex in database.facts:
                fh.write(ex + "\n")

    def add_point(self, x, y):
        self.operations.append((Operations.ADD_POINT, (x, y)))
        self.points[(x, y)] = BLACK

    def toggle_point(self, x, y):
        c = self.points[(x, y)]
        self.operations.append((Operations.TOGGLE_POINT, (x, y)))

        if c == BLACK:
            self.points[(x, y)] = ORANGE
        else:
            self.points[(x, y)] = BLACK

    def add_line(self, x1, y1, x2, y2):
        if (((x1, y1), (x2, y2)) in self.lines) or (((x2, y2), (x1, y1)) in self.lines):
            # TODO(hayesall): Is there a data structure that has better performance?
            pass
        else:
            self.operations.append((Operations.ADD_LINE, (x1, y1, x2, y2)))
            self.lines.append(((x1, y1), (x2, y2)))

    def reset(self):
        self.operations = [
            (
                Operations.RESET,
                (
                    deepcopy(self.operations),
                    deepcopy(self.points),
                    deepcopy(self.lines),
                ),
            )
        ]
        self.points = {}
        self.lines = []

    def undo(self):

        if not self.operations:
            print("Reached furthest point back in history.")
        else:

            last_op, last_value = self.operations.pop()

            match last_op:
                case Operations.ADD_POINT:
                    self.points.pop(last_value, None)
                case Operations.ADD_LINE:
                    self.lines.pop()
                case Operations.TOGGLE_POINT:
                    c = self.points[last_value]
                    if c == BLACK:
                        self.points[last_value] = ORANGE
                    else:
                        self.points[last_value] = BLACK
                case Operations.RESET:
                    ops, pnts, lns = last_value
                    self.operations = ops
                    self.points = pnts
                    self.lines = lns
                case _:
                    raise RuntimeError("Tried to undo an unknown operation.")

    def __repr__(self):
        return str(self.operations) + str(self.points) + str(self.lines)


if __name__ == "__main__":

    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("file", nargs="?", help="Load from a json file.")
    ARGS = PARSER.parse_args()

    if ARGS.file:
        fw = FlatWorld.from_json(ARGS.file)
    else:
        fw = FlatWorld()

    DONE = False
    BACKGROUND = True

    pygame.init()
    pygame.event.set_blocked(pygame.MOUSEMOTION)

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Roof World GUI")
    CLOCK = pygame.time.Clock()

    save_state = 0

    while not DONE:

        CLOCK.tick(30)

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                DONE = True

            if event.type == pygame.KEYDOWN and event.key == pygame.K_d:
                fw.dump_state()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                fw.predict()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_b:
                BACKGROUND = not BACKGROUND

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                LINE_MODE = None

            if (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_z
                and pygame.key.get_mods() & pygame.KMOD_LCTRL
            ):
                fw.undo()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_c:
                fw.reset()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_s:
                # TODO(hayesall): Save to an output directory.

                # Get a datetime + path
                save_to = f"saved/building_{int(datetime.now().timestamp())}.json"
                fw.to_json(save_to)

                fw.export(start=save_state)
                save_state += len(fw.points)
                print("Saved to network.pickle")

            if event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                # Draw the lines using right click

                if not LINE_MODE:

                    # Make sure there's a point near the right click location:
                    x, y = pygame.mouse.get_pos()

                    x_r, y_r = myround(x), myround(y)

                    if (x_r, y_r) in fw.points:
                        LINE_MODE = (x_r, y_r)

                else:

                    x, y = pygame.mouse.get_pos()
                    x_r, y_r = myround(x), myround(y)

                    # We want:
                    #   - To draw from point to a point
                    #   - Do NOT want to draw from a point to itself
                    if (x_r, y_r) in fw.points and (x_r, y_r) != LINE_MODE:
                        fw.add_line(*LINE_MODE, x_r, y_r)
                        LINE_MODE = None

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # Draw the points using left click

                x, y = pygame.mouse.get_pos()

                x_r, y_r = myround(x), myround(y)

                if fw.points.get((x_r, y_r)):
                    fw.toggle_point(x_r, y_r)
                else:
                    fw.add_point(x_r, y_r)

        # Render the scene
        if BACKGROUND:
            screen.fill(LIGHTGRAY)
            draw_graphpaper(screen, SPACING)
        else:
            screen.fill(WHITE)
        for ((x1, y1), (x2, y2)) in fw.lines:
            pygame.draw.line(screen, BLACK, (x1, y1), (x2, y2), 3)
        for (x, y) in fw.points:
            pygame.draw.circle(screen, fw.points[(x, y)], (x, y), 5)
        if LINE_MODE:
            pygame.draw.line(screen, BLACK, LINE_MODE, pygame.mouse.get_pos(), 1)

        pygame.display.flip()

    pygame.quit()
