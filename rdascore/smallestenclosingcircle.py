import math
import random
from typing import NamedTuple, Iterator

# adapted from "Smallest enclosing disks (balls and ellipsoids)" by EMO WELZL, p.362


class Point(NamedTuple):
    x: float
    y: float


class Circle(NamedTuple):
    center: Point
    r: float


class AlecCircle(NamedTuple):
    x: float
    y: float
    r: float


class WelzlCircle(NamedTuple):
    circle: Circle
    defining: list[Point]


def B_MINIDISK(points: list[Point], R: list[Point]) -> WelzlCircle:
    if len(points) == 0 or len(R) == 3:
        return b_md(points, R)
    p = points[0]
    remaining: list[Point] = points[1:]
    D: WelzlCircle = B_MINIDISK(remaining, R)
    if not D.defining or not new_in_circle(D.circle, p):
        return B_MINIDISK(remaining, R + [p])
    return D


# non-recursive version of B_MINIDISK
def wl_B_MINIDISK(points: list[Point]) -> WelzlCircle:
    wl: list[tuple[tuple[int, int], list[Point]]] = [((0, 0), [])]
    retval: WelzlCircle = WelzlCircle(Circle(Point(999, 999), 999), [])  # phony value
    while wl:
        (index, phase), R = wl.pop()
        if phase == 0:
            if index >= len(points) or len(R) == 3:
                retval = b_md([], R)
            else:
                wl.append(((index, 1), R))
                wl.append(((index + 1, 0), R))
        elif phase == 1:
            if not retval.defining or not new_in_circle(retval.circle, points[index]):
                # wl.append(((index, 2), R)) # phase 2 is a no-op
                wl.append(((index + 1, 0), R + [points[index]]))
        # elif phase == 2:
        #     continue
        else:
            raise ValueError("phase out of range")

    return retval


def b_md(points: list[Point], R: list[Point]) -> WelzlCircle:
    if len(R) == 0:
        return WelzlCircle(Circle(Point(0, 0), 0), [])
    elif len(R) == 1:
        return WelzlCircle(Circle(R[0], 0), R)
    elif len(R) == 2:
        return WelzlCircle(
            Circle(
                Point((R[0].x + R[1].x) / 2, (R[0].y + R[1].y) / 2),
                math.hypot(R[0].x - R[1].x, R[0].y - R[1].y) / 2,
            ),
            R,
        )
    elif len(R) == 3:
        c: Circle = circleRadius(R[0], R[1], R[2])
        return WelzlCircle(c, R)
    else:
        raise ValueError("R is too large")


def new_in_circle(D: Circle, p: Point) -> bool:
    return math.hypot(D.center.x - p.x, D.center.y - p.y) <= D.r


# adapted from https://stackoverflow.com/questions/52990094/calculate-circle-given-3-points-code-explanation
def circleRadius(b: Point, c: Point, d: Point) -> Circle:
    temp: float = c[0] ** 2 + c[1] ** 2
    bc: float = (b[0] ** 2 + b[1] ** 2 - temp) / 2
    cd: float = (temp - d[0] ** 2 - d[1] ** 2) / 2
    det: float = (b[0] - c[0]) * (c[1] - d[1]) - (c[0] - d[0]) * (b[1] - c[1])

    if abs(det) < 1.0e-10:
        raise ValueError("The three points are colinear")

    # Center of circle
    cx: float = (bc * (c[1] - d[1]) - cd * (b[1] - c[1])) / det
    cy: float = ((b[0] - c[0]) * cd - (c[0] - d[0]) * bc) / det

    radius: float = ((cx - b[0]) ** 2 + (cy - b[1]) ** 2) ** 0.5

    return Circle(Point(cx, cy), radius)


# ----------------------------------------------------------------------------
# Todd's driver routine to marry it to Alec's code


def stride(points: list[Point]) -> Iterator[Point]:
    half = len(points) // 2
    yield from stride0([points[:half], points[half:]])


def stride0(L: list[list[Point]]) -> Iterator[Point]:
    if len(L) == 0:
        return
    left: list[list[Point]] = []
    right: list[list[Point]] = []
    for v in L:
        if len(v) == 0:
            continue
        yield v[0]
        remaining = v[1:]
        half = len(remaining) // 2
        left.append(remaining[:half])
        right.append(remaining[half:])
    yield from stride0(left + right)


def new_make_circle(points: list[tuple[float, float]]) -> AlecCircle:
    ordered: list[Point] = [Point(x, y) for x, y in points]
    random.shuffle(ordered)  # shuffle to avoid worst case
    ordered = list(stride(ordered))  # optimize for convex hull path?
    x: WelzlCircle = B_MINIDISK(ordered, [])
    return AlecCircle(x.circle.center.x, x.circle.center.y, x.circle.r)


# uses non-recursive version of B_MINIDISK
def wl_make_circle(points: list[tuple[float, float]]) -> AlecCircle:
    ordered: list[Point] = [Point(x, y) for x, y in points]
    random.shuffle(ordered)
    ordered = list(stride(ordered))
    x: WelzlCircle = wl_B_MINIDISK(ordered)
    return AlecCircle(x.circle.center.x, x.circle.center.y, x.circle.r)


# ----------------------------------------------------------------------------
# everything below this line is from Alec


#
# Smallest enclosing circle - Library (Python)
#
# Copyright (c) 2017 Project Nayuki
# https://www.nayuki.io/page/smallest-enclosing-circle
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program (see COPYING.txt and COPYING.LESSER.txt).
# If not, see <http://www.gnu.org/licenses/>.
#


# Data conventions: A point is a pair of floats (x, y). A circle is a triple of floats (center x, center y, radius).


# Returns the smallest circle that encloses all the given points. Runs in expected O(n) time, randomized.
# Input: A sequence of pairs of floats or ints, e.g. [(0,5), (3.1,-2.7)].
# Output: A triple of floats representing a circle.
# Note: If 0 points are given, None is returned. If 1 point is given, a circle of radius 0 is returned.
#
# Initially: No boundary points known
def make_circle(points):
    # Convert to float and randomize order
    shuffled = [(float(x), float(y)) for (x, y) in points]
    random.shuffle(shuffled)

    # Progressively add points to circle or recompute circle
    c = None
    for i, p in enumerate(shuffled):
        if c is None or not is_in_circle(c, p):
            c = _make_circle_one_point(shuffled[: i + 1], p)
    assert c is not None  # Added 05/05/23

    return c


# One boundary point known
def _make_circle_one_point(points, p):
    c = (p[0], p[1], 0.0)
    for i, q in enumerate(points):
        if not is_in_circle(c, q):
            if c[2] == 0.0:  # type: ignore
                c = make_diameter(p, q)
            else:
                c = _make_circle_two_points(points[: i + 1], p, q)
    return c


# Two boundary points known
def _make_circle_two_points(points, p, q):
    circ = make_diameter(p, q)
    left = None
    right = None
    px, py = p
    qx, qy = q

    # For each point not in the two-point circle
    for r in points:
        if is_in_circle(circ, r):
            continue

        # Form a circumcircle and classify it on left or right side
        cross = _cross_product(px, py, qx, qy, r[0], r[1])
        c = make_circumcircle(p, q, r)
        if c is None:
            continue
        elif cross > 0.0 and (
            left is None
            or _cross_product(px, py, qx, qy, c[0], c[1])
            > _cross_product(px, py, qx, qy, left[0], left[1])
        ):
            left = c
        elif cross < 0.0 and (
            right is None
            or _cross_product(px, py, qx, qy, c[0], c[1])
            < _cross_product(px, py, qx, qy, right[0], right[1])
        ):
            right = c

    # Select which circle to return
    if left is None and right is None:
        return circ
    elif left is None:
        return right
    elif right is None:
        return left
    else:
        return left if (left[2] <= right[2]) else right


def make_circumcircle(p0, p1, p2):
    # Mathematical algorithm from Wikipedia: Circumscribed circle
    ax, ay = p0
    bx, by = p1
    cx, cy = p2
    ox = (min(ax, bx, cx) + max(ax, bx, cx)) / 2.0
    oy = (min(ay, by, cy) + max(ay, by, cy)) / 2.0
    ax -= ox
    ay -= oy
    bx -= ox
    by -= oy
    cx -= ox
    cy -= oy
    d = (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by)) * 2.0
    if d == 0.0:
        return None
    x = (
        ox
        + (
            (ax * ax + ay * ay) * (by - cy)
            + (bx * bx + by * by) * (cy - ay)
            + (cx * cx + cy * cy) * (ay - by)
        )
        / d
    )
    y = (
        oy
        + (
            (ax * ax + ay * ay) * (cx - bx)
            + (bx * bx + by * by) * (ax - cx)
            + (cx * cx + cy * cy) * (bx - ax)
        )
        / d
    )
    ra = math.hypot(x - p0[0], y - p0[1])
    rb = math.hypot(x - p1[0], y - p1[1])
    rc = math.hypot(x - p2[0], y - p2[1])
    return (x, y, max(ra, rb, rc))


def make_diameter(p0, p1):
    cx = (p0[0] + p1[0]) / 2.0
    cy = (p0[1] + p1[1]) / 2.0
    r0 = math.hypot(cx - p0[0], cy - p0[1])
    r1 = math.hypot(cx - p1[0], cy - p1[1])
    return (cx, cy, max(r0, r1))


_MULTIPLICATIVE_EPSILON = 1 + 1e-14


def is_in_circle(c, p):
    return (
        c is not None
        and math.hypot(p[0] - c[0], p[1] - c[1]) <= c[2] * _MULTIPLICATIVE_EPSILON
    )


# Returns twice the signed area of the triangle defined by (x0, y0), (x1, y1), (x2, y2).
def _cross_product(x0, y0, x1, y1, x2, y2):
    return (x1 - x0) * (y2 - y0) - (y1 - y0) * (x2 - x0)


### END ###


def test_circles(x: tuple[float, float, float], y: tuple[float, float, float]) -> None:
    epsilon = 1e-5
    assert abs(x[0] - y[0]) < epsilon, f"{x[0]} != {y[0]}"
    assert abs(x[1] - y[1]) < epsilon, f"{x[1]} != {y[1]}"
    assert abs(x[2] - y[2]) < epsilon, f"{x[2]} != {y[2]}"


def test(N: int) -> None:
    for size in range(3, N):
        points: list[tuple[float, float]] = [
            (random.random(), random.random()) for _ in range(size)
        ]
        wl_circle: tuple[float, float, float] = wl_make_circle(points)
        their_circle: tuple[float, float, float] = make_circle(points)
        test_circles(wl_circle, their_circle)
        if N < 1000:
            my_circle: AlecCircle = new_make_circle(points)
            test_circles(my_circle, wl_circle)


def main() -> None:
    test(500)
    print("Passed")


if __name__ == "__main__":
    main()
