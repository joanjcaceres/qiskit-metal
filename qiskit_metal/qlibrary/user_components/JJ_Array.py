# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""
Josephson Junction Array
Array of rectangular junctions with defined electrical properties (Cj, Lj)
"""
from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core.base import QComponent


class JJ_Array(QComponent):
    """
    Josephson Junction Array component.
    
    This creates an array of N rectangular "unit cells" representing 
    Josephson junctions. Each unit cell is a simple rectangle with 
    defined electrical properties (capacitance Cj and inductance Lj).
    
    The junctions are arranged linearly (horizontal or vertical) with
    optional spacing between them.
    
    This component is suitable for circuit simulation and analysis,
    where the electrical properties are more important than the 
    physical fabrication details.

    .. image::
        JJ_Array.png

    .. meta::
        Josephson Junction Array

    Default Options:
        * N: '5' -- number of junctions in the array
        * orientation: 'horizontal' -- array direction: 'horizontal' or 'vertical'
        * junction_length: '10um' -- length of each junction rectangle
        * junction_width: '2um' -- width of each junction rectangle
        * spacing: '0um' -- spacing between consecutive junctions (0 = yuxtapuestas/pegadas)
        * Cj: '1fF' -- capacitance of EACH individual junction
        * Lj: '10pH' -- inductance of EACH individual junction
        * pos_x: '0um' -- x-coordinate of the first junction
        * pos_y: '0um' -- y-coordinate of the first junction
        * layer: '1' -- layer number for the junctions
        * add_contact_pads: 'True' -- add metallic contact pads at both ends
        * contact_pad_width: '20um' -- width of contact pads
        * contact_pad_height: '40um' -- height of contact pads  
        * contact_pad_gap: '2um' -- gap between pad and first/last junction
        
    Note:
        The component creates individual LineString geometries for each junction.
        The HFSS renderer automatically creates rectangles with RLC boundary conditions.
        
        Pins are added at both ends of the array for connecting to other components.
    """
    # Default drawing options
    default_options = Dict(
        N='5',
        orientation='horizontal',
        junction_length='10um',
        junction_width='2um',
        spacing='0um',  # Por defecto, junturas yuxtapuestas (pegadas)
        Cj='1fF',       # Capacitancia de cada juntura individual
        Lj='10pH',      # Inductancia de cada juntura individual
        pos_x='0um',
        pos_y='0um',
        layer='1',
        chip='main',
        # For GDS export (if using junction cells)
        gds_cell_name='',
        # Mesh refinement for junction (important for accurate simulation)
        hfss_mesh_kw_jj=7e-06,  # HFSS mesh size at junction
        q3d_mesh_kw_jj=7e-06,   # Q3D mesh size at junction
    )
    """Default drawing options"""

    # Name prefix of component, if user doesn't provide name
    component_metadata = Dict(short_name='jj_array')
    """Component metadata"""

    def make(self):
        """Convert self.options into QGeometry."""

        p = self.parse_options()  # Parse the string options into numbers

        # Store electrical properties in metadata
        self.metadata['Cj'] = p.Cj
        self.metadata['Lj'] = p.Lj
        self.metadata['N'] = int(p.N)
        
        N = int(p.N)
        
        # HFSS expects: inductance in nH (as string), capacitance in Farads (as float)
        # Just pass the original string values - they're already in the correct format
        hfss_inductance = str(p.Lj)  # e.g., "10pH" or "0.01nH"
        hfss_capacitance = str(p.Cj)  # e.g., "1fF"
        
        # Create individual junction LineStrings for each junction
        # Each junction gets its own Lj and Cj values
        # NOTE: We DON'T create poly rectangles - the renderer creates them automatically
        # from the junction geometry
        junction_lines = {}
        
        for i in range(N):
            if p.orientation == 'horizontal':
                # Each junction is a short horizontal line segment
                start_x = p.pos_x + i * (p.junction_length + p.spacing)
                start_y = p.pos_y
                end_x = start_x + p.junction_length
                end_y = p.pos_y
            else:  # vertical
                # Each junction is a short vertical line segment
                start_x = p.pos_x
                start_y = p.pos_y + i * (p.junction_length + p.spacing)
                end_x = p.pos_x
                end_y = start_y + p.junction_length
            
            # Create a LineString for this individual junction
            jj_line = draw.LineString([(start_x, start_y), (end_x, end_y)])
            junction_lines[f'jj_{i}'] = jj_line
        
        # Add all junctions as separate junction geometries
        # The renderer will automatically create the rectangles (RLC boundaries) for each
        # Each junction gets the same Lj and Cj values (from the component options)
        self.add_qgeometry('junction', 
                          junction_lines,
                          width=p.junction_width,
                          chip=p.chip,
                          hfss_inductance=hfss_inductance,
                          q3d_inductance=hfss_inductance,
                          hfss_capacitance=hfss_capacitance,
                          q3d_capacitance=hfss_capacitance,
                          hfss_resistance=0,
                          q3d_resistance=0)
        
        # Add pins at both ends of the array for connections
        # Calculate array length
        array_length = (N - 1) * (p.junction_length + p.spacing) + p.junction_length
        
        if p.orientation == 'horizontal':
            # For horizontal array:
            # - Tangent line is VERTICAL (perpendicular to array direction)
            # - Normal vector will point LEFT (start pin) or RIGHT (end pin)
            # - Order of points matters: going from point1→point2, rotate 90° CCW to get normal
            
            # Pin at the start (left side) - normal points LEFT (outward)
            # Points go bottom→top, so normal points left ←
            start_pin_line = draw.LineString([
                (p.pos_x, p.pos_y - p.junction_width / 2),
                (p.pos_x, p.pos_y + p.junction_width / 2)
            ])
            start_pin_points = list(start_pin_line.coords)
            
            # Pin at the end (right side) - normal points RIGHT (outward)
            # Points go top→bottom, so normal points right →
            end_pin_line = draw.LineString([
                (p.pos_x + array_length, p.pos_y + p.junction_width / 2),
                (p.pos_x + array_length, p.pos_y - p.junction_width / 2)
            ])
            end_pin_points = list(end_pin_line.coords)
        else:  # vertical
            # For vertical array:
            # - Tangent line is HORIZONTAL (perpendicular to array direction)
            # - Normal vector will point DOWN (start pin) or UP (end pin)
            # - Order of points matters: going from point1→point2, rotate 90° CCW to get normal
            
            # Pin at the start (bottom) - normal points DOWN (outward)
            # Points go right→left, so normal points down ↓
            start_pin_line = draw.LineString([
                (p.pos_x + p.junction_width / 2, p.pos_y),
                (p.pos_x - p.junction_width / 2, p.pos_y)
            ])
            start_pin_points = list(start_pin_line.coords)
            
            # Pin at the end (top) - normal points UP (outward)
            # Points go left→right, so normal points up ↑
            end_pin_line = draw.LineString([
                (p.pos_x - p.junction_width / 2, p.pos_y + array_length),
                (p.pos_x + p.junction_width / 2, p.pos_y + array_length)
            ])
            end_pin_points = list(end_pin_line.coords)
        
        # Add the pins
        # Note: input_as_norm=False (default) means points define the TANGENT line
        # The normal (connection direction) is calculated as perpendicular to this tangent
        self.add_pin('start', start_pin_points, p.junction_width)
        self.add_pin('end', end_pin_points, p.junction_width)

            
    def get_total_capacitance(self):
        """
        Calculate total capacitance of the array.
        Assumes junctions are in series, so: 1/C_total = sum(1/C_i)
        For identical junctions: C_total = Cj / N
        
        Returns:
            str: Total capacitance value with units
        """
        if 'Cj' in self.metadata and 'N' in self.metadata:
            Cj_str = str(self.metadata['Cj'])
            N = self.metadata['N']
            # For series capacitors
            if 'fF' in Cj_str:
                Cj_single_fF = float(Cj_str.replace('fF', '').strip())
                C_total_fF = Cj_single_fF / N
                return f"Individual Cj: {Cj_single_fF}fF, Total (series): {C_total_fF:.4f}fF"
            return f"Individual Cj: {Cj_str}, Total: {Cj_str}/{N}"
        return "Not defined"
    
    def get_total_inductance(self):
        """
        Calculate total inductance of the array.
        Assumes junctions are in series, so: L_total = sum(L_i)
        For identical junctions: L_total = Lj * N
        
        Returns:
            str: Total inductance value with units
        """
        if 'Lj' in self.metadata and 'N' in self.metadata:
            Lj_str = str(self.metadata['Lj'])
            N = self.metadata['N']
            # For series inductors
            if 'pH' in Lj_str:
                Lj_single_pH = float(Lj_str.replace('pH', '').strip())
                L_total_pH = Lj_single_pH * N
                L_total_nH = L_total_pH / 1000.0
                return f"Individual Lj: {Lj_single_pH}pH ({Lj_single_pH/1000.0}nH), Total (series): {L_total_nH:.4f}nH ({L_total_pH}pH)"
            elif 'nH' in Lj_str:
                Lj_single_nH = float(Lj_str.replace('nH', '').strip())
                L_total_nH = Lj_single_nH * N
                return f"Individual Lj: {Lj_single_nH}nH, Total (series): {L_total_nH:.4f}nH"
            return f"Individual Lj: {Lj_str}, Total: {Lj_str}*{N}"
        return "Not defined"
