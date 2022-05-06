# Copyright © 2022 Alexander L. Hayes
# MIT License

import argparse
import numpy as np
import cv2

if __name__ == "__main__":

    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("image", nargs="?", default="docs/one_roof.png", type=str)
    ARGS = PARSER.parse_args()

    img = cv2.imread(ARGS.image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    edges = cv2.Canny(blurred, 50, 150)
    line_image = (np.copy(img) * 0) + 255

    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 15, np.array([]), 50, 20)

    for line in lines:
        for x1, y1, x2, y2 in line:
            cv2.circle(line_image, (x1, y1), 5, (0, 0, 0))
            cv2.circle(line_image, (x2, y2), 5, (0, 0, 0))
            cv2.line(line_image, (x1, y1), (x2, y2), (0, 0, 0), 2)

    line_edges = cv2.addWeighted(img, 0.8, line_image, 1, 0)

    cv2.imshow('image', line_image)
    cv2.waitKey(0)
