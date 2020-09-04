# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

'''
Anchored path

@date: Aug-2020
@author: Dennis Wang, Marco Facchini
'''

import numpy as np
from collections import OrderedDict
from qiskit_metal import Dict
from qiskit_metal.components.base import QRoute, QRoutePoint

# TODO: Use minimum bounding boxes and alter bounding box method for CPWs.


def intersecting(a: np.array, b: np.array, c: np.array, d: np.array) -> bool:
    """Returns whether segment ab intersects or overlaps with segment cd, where a, b, c, and d are
    all coordinates

    Args:
        a (np.array): coordinate
        b (np.array): coordinate
        c (np.array): coordinate
        d (np.array): coordinate

    Returns:
        bool: True if intersecting, False otherwise
    """

    x0_start, y0_start = a
    x0_end, y0_end = b
    x1_start, y1_start = c
    x1_end, y1_end = d
    if (x0_start == x0_end) and (x1_start == x1_end):
        # 2 vertical lines intersect only if they completely overlap at some point(s)
        if x0_end == x1_start:
            # Same x-intercept -> potential overlap, so check y coordinate
            # Distinct, non-overlapping segments if and only if min y coord of one is above max y coord of the other
            return not ((min(y0_start, y0_end) > max(y1_start, y1_end)) or (min(y1_start, y1_end) > max(y0_start, y0_end)))
        return False # Parallel lines with different x-intercepts don't overlap
    elif (x0_start == x0_end) or (x1_start == x1_end):
        # One segment is vertical, the other is not
        # Express non-vertical line in the form of y = mx + b and check y value
        if x1_start == x1_end:
            # Exchange names; the analysis below assumes that line 0 is the vertical one
            x0_start, x0_end, x1_start, x1_end = x1_start, x1_end, x0_start, x0_end
            y0_start, y0_end, y1_start, y1_end = y1_start, y1_end, y0_start, y0_end
        m = (y1_end - y1_start) / (x1_end - x1_start)
        b = (x1_end * y1_start - x1_start * y1_end) / (x1_end - x1_start)
        if min(x1_start, x1_end) <= x0_start <= max(x1_start, x1_end):
            if min(y0_start, y0_end) <= m * x0_start + b <= max(y0_start, y0_end):
                return True
        return False
    else:
        # Neither line is vertical; check slopes and y-intercepts
        b0 = (y0_start * x0_end - y0_end * x0_start) / (x0_end - x0_start) # y-intercept of line 0
        b1 = (y1_start * x1_end - y1_end * x1_start) / (x1_end - x1_start) # y-intercept of line 1
        if (x1_end - x1_start) * (y0_end - y0_start) == (x0_end - x0_start) * (y1_end - y1_start):
            # Lines have identical slopes
            if b0 == b1:
                # Same y-intercept -> potential overlap, so check x coordinate
                # Distinct, non-overlapping segments if and only if min x coord of one exceeds max x coord of the other
                return not ((min(x0_start, x0_end) > max(x1_start, x1_end)) or (min(x1_start, x1_end) > max(x0_start, x0_end)))
            return False # Parallel lines with different y-intercepts don't overlap
        else:
            # Lines not parallel so must intersect somewhere -> examine slopes m0 and m1
            m0 = (y0_end - y0_start) / (x0_end - x0_start) # slope of line 0
            m1 = (y1_end - y1_start) / (x1_end - x1_start) # slope of line 1
            x_intersect = (b1 - b0) / (m0 - m1) # x coordinate of intersection point
            if min(x0_start, x0_end) <= x_intersect <= max(x0_start, x0_end):
                if min(x1_start, x1_end) <= x_intersect <= max(x1_start, x1_end):
                    return True
            return False


class RouteAnchors(QRoute):
    """
    Creates and connects a series of anchors through which the CPW passes.

    Options:

    Anchors:
        * (Ordered Dictionary) - array of numpy 1x2. Points we want the route to intercept

    Advanced:
        * avoid_collision - true/false, defines if the route needs to avoid collisions (default: 'false')

    """

    component_metadata = Dict(
        short_name='cpw'
        )
    """Component metadata"""

    default_options = Dict(
        anchors=OrderedDict(),  # Intermediate anchors only; doesn't include endpoints
        # Example: {1: np.array([x1, y1]), 2: np.array([x2, y2])}
        # startpin -> startpin + leadin -> anchors -> endpin + leadout -> endpin
        advanced=Dict(
            avoid_collision='false')
    )
    """Default options"""

    def unobstructed(self, segment: list) -> bool:
        """
        Check that no component's bounding box in self.design intersects or overlaps a given segment.

        Args:
            segment (list): List comprised of vertex coordinates of the form [np.array([x0, y0]), np.array([x1, y1])]

        Returns:
            bool: True is no obstacles
        """

        # TODO: Non-rectangular bounding boxes?

        for component in self.design.components:
            xmin, ymin, xmax, ymax = self.design.components[component].qgeometry_bounds()
            # p, q, r, s are corner coordinates of each bounding box
            p, q, r, s = [np.array([xmin, ymin]),
                          np.array([xmin, ymax]),
                          np.array([xmax, ymin]),
                          np.array([xmax, ymax])]
            if any(intersecting(segment[0], segment[1], k, l) for k, l in [(p, q), (p, r), (r, s), (q, s)]):
                # At least 1 intersection present; do not proceed!
                return False
        # All clear, no intersections
        return True

    def connect_simple(self, start_pt: QRoutePoint, end_pt: QRoutePoint) -> list:
        """
        Try connecting start and end with single or 2-segment/S-shaped CPWs if possible.
        
        Args:
            start_pt (QRoutePoint): QRoutePoint of the start
            end_pt (QRoutePoint): QRoutePoint of the end

        Returns:
            List of vertices of a CPW going from start to end
        """

        avoid_collision = self.parse_options().advanced.avoid_collision

        start_direction = start_pt.direction
        start = start_pt.position
        end_direction = end_pt.direction
        end = end_pt.position

        # end_direction originates strictly from endpoint + leadout (NOT intermediate stopping anchors)
        # stop_direction aligned with longer rectangle edge regardless of nature of 2nd anchor

        # Absolute value of displacement between start and end in x direction
        offsetx = abs(end[0] - start[0])
        # Absolute value of displacement between start and end in y direction
        offsety = abs(end[1] - start[1])
        if offsetx >= offsety: # "Wide" rectangle -> end_arrow points along x
            stop_direction = np.array([end[0] - start[0], 0])
        else: # "Tall" rectangle -> end_arrow points along y
            stop_direction = np.array([0, end[1] - start[1]])

        if (start[0] == end[0]) or (start[1] == end[1]):
            # Matching x or y coordinates -> check if endpoints can be connected with a single segment
            if np.dot(start_direction, end - start) >= 0:
                # Start direction and end - start for CPW must not be anti-aligned
                if (end_direction is None) or (np.dot(end - start, end_direction) <= 0):
                    # If leadout + end has been reached, the single segment CPW must not be aligned with its direction
                    return [start, end]
        else:
            # If the endpoints don't share a common x or y value:
            # designate them as 2 corners of an axis aligned rectangle
            # and check if both start and end directions are aligned with
            # the displacement vectors between start/end and
            # either of the 2 remaining corners ("perfect alignment").
            corner1 = np.array([start[0], end[1]]) # x coordinate matches with start
            corner2 = np.array([end[0], start[1]]) # x coordinate matches with end
            if avoid_collision:
                # Check for collisions at the outset to avoid repeat work
                startc1end = bool(self.unobstructed([start, corner1]) and self.unobstructed([corner1, end]))
                startc2end = bool(self.unobstructed([start, corner2]) and self.unobstructed([corner2, end]))
            else:
                startc1end = startc2end = True
            if (np.dot(start_direction, corner1 - start) > 0) and startc1end:
                if (end_direction is None) or (np.dot(end_direction, corner1 - end) > 0):
                    return [start, corner1, end]
            elif (np.dot(start_direction, corner2 - start) > 0) and startc2end:
                if (end_direction is None) or (np.dot(end_direction, corner2 - end) > 0):
                    return [start, corner2, end]
            # In notation below, corners 3 and 4 correspond to
            # the ends of the segment bisecting the longer rectangle formed by start and end
            # while the segment formed by corners 5 and 6 bisect the shorter rectangle
            if stop_direction[0]: # "Wide" rectangle -> vertical middle segment is more natural
                corner3 = np.array([(start[0] + end[0]) / 2, start[1]])
                corner4 = np.array([(start[0] + end[0]) / 2, end[1]])
                corner5 = np.array([start[0], (start[1] + end[1]) / 2])
                corner6 = np.array([end[0], (start[1] + end[1]) / 2])
            else: # "Tall" rectangle -> horizontal middle segment is more natural
                corner3 = np.array([start[0], (start[1] + end[1]) / 2])
                corner4 = np.array([end[0], (start[1] + end[1]) / 2])
                corner5 = np.array([(start[0] + end[0]) / 2, start[1]])
                corner6 = np.array([(start[0] + end[0]) / 2, end[1]])
            if avoid_collision:
                startc3c4end = bool(self.unobstructed([start, corner3]) and self.unobstructed([corner3, corner4]) and self.unobstructed([corner4, end]))
                startc5c6end = bool(self.unobstructed([start, corner5]) and self.unobstructed([corner5, corner6]) and self.unobstructed([corner6, end]))
            else:
                startc3c4end = startc5c6end = True
            if (np.dot(start_direction, stop_direction) < 0) and (np.dot(start_direction, corner3 - start) > 0) and startc3c4end:
                if (end_direction is None) or (np.dot(end_direction, corner4 - end) > 0):
                    # Perfectly aligned S-shaped CPW
                    return [start, corner3, corner4, end]
            # Relax constraints and check if imperfect 2-segment or S-segment works,
            # where "imperfect" means 1 or more dot products of directions
            # between successive segments is 0; otherwise return an empty list
            if (np.dot(start_direction, corner1 - start) >= 0) and startc1end:
                if (end_direction is None) or (np.dot(end_direction, corner1 - end) >= 0):
                    return [start, corner1, end]
            if (np.dot(start_direction, corner2 - start) >= 0) and startc2end:
                if (end_direction is None) or (np.dot(end_direction, corner2 - end) >= 0):
                    return [start, corner2, end]
            if (np.dot(start_direction, corner3 - start) >= 0) and startc3c4end:
                if (end_direction is None) or (np.dot(end_direction, corner4 - end) >= 0):
                    return [start, corner3, corner4, end]
            if (np.dot(start_direction, corner5 - start) >= 0) and startc5c6end:
                if (end_direction is None) or (np.dot(end_direction, corner6 - end) >= 0):
                    return [start, corner5, corner6, end]
        return []

    def make(self):
        """
        Generates path from start pin to end pin.
        """
        p = self.parse_options()
        anchors = p.anchors

        # Set the CPW pins and add the points/directions to the lead-in/out arrays
        self.set_pin("start")
        self.set_pin("end")

        # Align the lead-in/out to the input options set from the user
        meander_start_point = self.set_lead("start")
        meander_end_point = self.set_lead("end")

        # TODO: find out why the make runs twice for every component and stop it.
        #  Should only run once. The line below is just a patch to work around it.
        self.intermediate_pts = None

        for coord in list(anchors.values()):
            if not self.intermediate_pts:
                self.intermediate_pts = self.connect_simple(meander_start_point, QRoutePoint(coord))[1:]
            else:
                self.intermediate_pts += self.connect_simple(self.get_tip(), QRoutePoint(coord))[1:]

        last_pt = self.connect_simple(self.get_tip(), meander_end_point)[1:]
        if self.intermediate_pts:
            self.intermediate_pts += last_pt
        else:
            self.intermediate_pts = last_pt

        # Make points into elements
        self.make_elements(self.get_points())
