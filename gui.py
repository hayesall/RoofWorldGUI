# Copyright 2022 Alexander L. Hayes
# MIT License

"""
Controls:

- Left Mouse: Place points or toggle point color
- Right Mouse: Draw lines connecting two points

- `b`: Turn off graph paper / gray background mode (helpful for taking screenshots)
- `c`: Reset
- `s`: Save. TODO(hayesall)
"""

from copy import deepcopy
from enum import Enum
import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

from roofworld.exporter import Network

import matplotlib.pyplot as plt
import pygame
from srlearn.rdn import BoostedRDN
from srlearn import Database


pygame.init()
pygame.event.set_blocked(pygame.MOUSEMOTION)

CLOCK = pygame.time.Clock()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LIGHTGRAY = (250, 250, 250)
LIGHTBLUE = (150, 173, 233)
ORANGE = (255, 165, 0)

WIDTH, HEIGHT = 1000, 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Roof World GUI")

SPACING = 25
POINTS = {}
LINES = []
LINE_MODE = None


def myround(x, base=25):
    return base * round(x / base)


def draw_background(c=LIGHTGRAY):
    screen.fill(c)


def draw_graphpaper(k):
    for i in range(WIDTH // k):
        x = k * i
        y = k * i
        pygame.draw.line(screen, LIGHTBLUE, (x, 0), (x, HEIGHT), 1)
        pygame.draw.line(screen, LIGHTBLUE, (0, y), (WIDTH, y), 1)


def draw_point(x, y, c=BLACK):
    pygame.draw.circle(screen, c, (x, y), 5)


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

    def dump_state(self):
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

        rdn = BoostedRDN()
        rdn.from_json("predict_highpoint_rdn.json")

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

        import pickle

        with open("network.pickle", "wb") as fh:
            pickle.dump(net, fh)

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

    DONE = False
    BACKGROUND = True

    fw = FlatWorld()

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
            draw_background(LIGHTGRAY)
            draw_graphpaper(SPACING)
        else:
            draw_background(WHITE)
        for ((x1, y1), (x2, y2)) in fw.lines:
            pygame.draw.line(screen, BLACK, (x1, y1), (x2, y2), 3)
        for (x, y) in fw.points:
            draw_point(x, y, fw.points[(x, y)])
        if LINE_MODE:
            pygame.draw.line(screen, BLACK, LINE_MODE, pygame.mouse.get_pos(), 1)

        pygame.display.flip()

    pygame.quit()
