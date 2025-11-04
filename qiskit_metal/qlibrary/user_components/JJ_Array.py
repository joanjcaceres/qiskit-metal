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
        * Cj: '1fF' -- capacitance of each junction (metadata)
        * Lj: '10pH' -- inductance of each junction (metadata)
        * pos_x: '0um' -- x-coordinate of the first junction
        * pos_y: '0um' -- y-coordinate of the first junction
        * layer: '1' -- layer number for the junctions
    """
    # Default drawing options
    default_options = Dict(
        N='5',
        orientation='horizontal',
        junction_length='10um',
        junction_width='2um',
        spacing='0um',  # Por defecto, junturas yuxtapuestas (pegadas)
        Cj='1fF',
        Lj='10pH',
        pos_x='0um',
        pos_y='0um',
        layer='1'
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
        
        # List to store all junction geometries
        all_junctions = []
        
        # Create N junctions
        N = int(p.N)
        
        for i in range(N):
            # Calculate position for this junction
            if p.orientation == 'horizontal':
                # Horizontal array: junctions placed along x-axis
                offset_x = i * (p.junction_length + p.spacing)
                offset_y = 0
                
                # Create rectangle with junction_length along x, junction_width along y
                junction_center_x = p.pos_x + offset_x + p.junction_length / 2
                junction_center_y = p.pos_y + offset_y
                
                junction = draw.rectangle(
                    p.junction_length,
                    p.junction_width,
                    junction_center_x,
                    junction_center_y
                )
                
            else:  # vertical
                # Vertical array: junctions placed along y-axis
                offset_x = 0
                offset_y = i * (p.junction_length + p.spacing)
                
                # Create rectangle with junction_width along x, junction_length along y
                junction_center_x = p.pos_x + offset_x
                junction_center_y = p.pos_y + offset_y + p.junction_length / 2
                
                junction = draw.rectangle(
                    p.junction_width,
                    p.junction_length,
                    junction_center_x,
                    junction_center_y
                )
            
            all_junctions.append(junction)
        
        # Add all junctions as a single geometry
        # Create a dictionary with all junctions
        geom = {f'junction_{i}': junction for i, junction in enumerate(all_junctions)}
        self.add_qgeometry('poly', geom, layer=p.layer, subtract=False)
            
    def get_total_capacitance(self):
        """
        Calculate total capacitance of the array.
        Assumes junctions are in series, so: 1/C_total = sum(1/C_i)
        For identical junctions: C_total = Cj / N
        
        Returns:
            str: Total capacitance value with units
        """
        if 'Cj' in self.metadata and 'N' in self.metadata:
            # Parse the capacitance value
            Cj_str = str(self.metadata['Cj'])
            N = self.metadata['N']
            # For series capacitors
            return f"{Cj_str} (single junction), Total: {Cj_str}/{N} (series)"
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
            return f"{Lj_str} (single junction), Total: {Lj_str}*{N} (series)"
        return "Not defined"
