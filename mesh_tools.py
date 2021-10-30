# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


import bpy
import bpy_extras.mesh_utils
import math
import random
from mathutils import Vector

def get_random_points_on_verts(mesh, amount, transform_matrix, seed=0):
    """
    get_random_points_on_verts(mesh mesh, int amount,
                               matrix transform_matrix, int seed)
            -> list of vector points

        Gets <amount> number of random vert coordinates.

        mesh mesh               - the mesh to get the points from
        int amount              - the amount of points to return
        matrix transform_matrix - the matrix to transform the points by
        int seed                - the seed for the randomization
    """

    random.seed(seed)
    points = []
    for _ in range(amount):
        points.append(transform_matrix * random.choice(mesh.vertices).co)

    return points


def get_random_points_on_edges(mesh, amount, transform_matrix, seed=0):
    """
    get_random_points_on_edges(mesh mesh, int amount,
                               matrix transform_matrix, int seed)
            -> list of vector points

        Gets <amount> number of random points on the edges of the mesh.

        mesh mesh               - the mesh to get the points from
        int amount              - the amount of points to return
        matrix transform_matrix - the matrix to transform the points by
        int seed                - the seed for the randomization
    """

    random.seed(seed)
    points = []
    for _ in range(amount):
        edge = random.choice(mesh.edges)
        v1 = mesh.vertices[edge.vertices[0]]
        v2 = mesh.vertices[edge.vertices[1]]
        p = v1.co + random.random() * (v2.co - v1.co)
        points.append(transform_matrix * p)

    return points




def get_random_points_on_surface(obj, amount, seed=0):
    """
    get_random_points_on_surface(objet obj, int amount, int seed)
            -> list of vector points

        Gets <amount> number of random points on the surface of the object.

        object obj              - the object to get the points from
        int amount              - the amount of points to return
        int seed                - the seed for the randomization
    """

    m = obj.modifiers.new('points', 'PARTICLE_SYSTEM')
    ps = m.particle_system
    ps.seed = seed
    ps.settings.count = amount
    ps.settings.frame_start = 1
    ps.settings.frame_end = 1
    ps.settings.emit_from = 'FACE'
    ps.settings.physics_type = 'NO'
    ps.settings.use_modifier_stack = True
    bpy.context.view_layer.update()
    points = [p.location.copy() for p in ps.particles]
    obj.modifiers.remove(m)

    return points




def get_random_points_in_volume(obj, amount, seed=0):
    """
    get_random_points_in_volume(object obj, int amount, int seed)
            -> list of vector points

        Gets <amount> number of random points inside the volume of the object.

        object obj              - the object to get the points from
        int amount              - the amount of points to return
        int seed                - the seed for the randomization
    """

    m = obj.modifiers.new('points', 'PARTICLE_SYSTEM')
    ps = m.particle_system
    ps.seed = seed
    ps.settings.count = amount
    ps.settings.frame_start = 1
    ps.settings.frame_end = 1
    ps.settings.emit_from = 'VOLUME'
    ps.settings.physics_type = 'NO'
    ps.settings.use_modifier_stack = True
    bpy.context.view_layer.update()
    points = [p.location.copy() for p in ps.particles]
    obj.modifiers.remove(m)

    return points


def get_points(obj, amount=1, method='SURFACE', apply_modifiers=True, seed=0):
    """
    get_points(object obj,
               int amount,
               string method,
               bool apply_modifiers) -> tuple of vector points

        Calculates points on the object according to method in world space.
        !!! For now, apart from "pivot", they will be random.
            Later there might be an option to change this behavior. !!!

        object obj           - the object to calculate the points on
        int amount           - the amount of points to calculate
        string method        - the method to calculate the points
                               valid options: - 'VERTS'
                                              - 'EDGES'
                                              - 'SURFACE'
                                              - 'VOLUME'
                                              - 'PIVOT'
        bool apply_modifiers - use the deformed or original mesh
        int seed             - the seed for the randomization
    """

    valid_methods = {'VERTS', 'EDGES', 'SURFACE', 'VOLUME', 'PIVOT'}

    if not method in valid_methods:
        return

    if apply_modifiers and not method == 'PIVOT':
        mesh = obj.to_mesh(preserve_all_data_layers=True, depsgraph = bpy.context.evaluated_depsgraph_get())
    elif method != 'PIVOT':
        mesh = obj.data.copy()
    transform_matrix = obj.matrix_world.copy()

    if method == 'VERTS':
        return get_random_points_on_verts(mesh, amount, transform_matrix, seed=seed)
        # points.append(transform_matrix * random.choice(mesh.vertices).co)
    if method == 'EDGES':
        return get_random_points_on_edges(mesh, amount, transform_matrix, seed=seed)
        # edge = random.choice(mesh.edges)
        # points.append(get_point_on_edge(edge, transform_matrix))
    if method == 'SURFACE':
        return get_random_points_on_surface(obj, amount, seed=seed)

        # point = bpy_extras.mesh_utils.face_random_points(1, [face])[0]
        # points.append(transform_matrix * point)
    if method == 'VOLUME':
        return get_random_points_in_volume(obj, amount, seed=seed)
    if method == 'PIVOT':
        # Only return the pivot point
        return [transform_matrix.to_translation()]


