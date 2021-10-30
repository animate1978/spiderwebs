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
import time
import math
import mathutils
import bmesh


def create_curve(name='curve',
                 options={"dimensions": '3D',
                          "resolution_u": 12,
                          "render_resolution_u": 0,
                          # "fill_mode": 'FULL',
                          "bevel_depth": 0,
                          "bevel_resolution": 0,
                          "bevel_object": None}):
    """
    create_curve(string name, dict options) -> curve curve

        string name - The name for the curve
        dict options - A dictionary with the settings for the curve

        Creates a curve object with the specified options and returns it.
    """

    curve = bpy.data.curves.new(name, 'CURVE')
    for k in options.keys():
        try:
            setattr(curve, k, options[k])
        except (AttributeError, TypeError) as err:
            print("{}\nSkipping this setting...".format(err))

    return curve


def create_spline(curve=None,
                  points=None,
                  spline_type='NURBS',
                  options={"use_cyclic_u": False,
                           "use_bezier_u": False,
                           "use_endpoint_u": True,
                           "order_u": 3,
                           "resolution_u": 12,
                           "tilt_interpolation": 'LINEAR',
                           "radius_interpolation": 'LINEAR',
                           "use_smooth": True}):
    """
    create_spline(curve curve, list of vector points,
                  string curve_type, dict options) -> tuple (curve, spline)

        Creates/adds a spline on the given curve. Returns a tuple of the curve
        and the spline. Returns nothing if no spline was created.
        !!! For now only 'NURBS' and 'POLY' are supported.

        curve curve           - The curve to create the spline on
        list of vector points - The points to create the spline from
        string spline_type    - The type of spline to create
    """

    if not curve:
        print("No curve given to create the spline on")
        return
    if not len(points) > 1:
        print("No points to create the spline from")
        return
    # valid_spline_types = {'POLY', 'BEZIER', 'NURBS'}
    valid_spline_types = {'POLY', 'NURBS'}
    if not spline_type in valid_spline_types:
        print("Spline type: {} is not valid/supported".format(spline_type))
        return
    if curve.splines:
        if not curve.splines[0].type == spline_type:
            print("{} not compatible with other splines "
                  "on curve".format(spline_type))
            return

    spline = curve.splines.new(spline_type)

    # Create and position the points
    spline.points.add(count=len(points) - 1)
    for i, p in enumerate(points):
        spline.points[i].co = p.to_4d()

    # Set the options
    for k in options.keys():
        try:
            setattr(spline, k, options[k])
        except (AttributeError, TypeError) as err:
            print("{}\nSkipping this setting...".format(err))

    return (curve, spline)


def get_length(curve, spline):
    pass


def get_point_on_curve(curve, spline, position):
    pass


def get_spline_as_mesh(curve, spline, link_in_scene=False):
    """
    get_spline_as_mesh(object curve, int spline) -> object spline_obj

        Copies the curve object, removes all splines except the chosen one,
        converts the object to a mesh and return this new object.

        object curve - the curve object to process
        int spline   - the index of the spline to convert
    """
    scene = bpy.context.scene
    spline_obj = curve.copy()
    spline_curve = spline_obj.data.copy()
    spline_obj.data = spline_curve
    for i, _ in enumerate(curve.data.splines):
        if i != spline:
            spline_curve.splines.remove(spline_curve.splines[i])
    name = "{}_spline{}".format(curve.name, spline)
    spline_mesh = spline_obj.to_mesh(scene, True, 'RENDER')
    spline_obj = bpy.data.objects.new(name, spline_mesh)
    if link_in_scene:
        scene.objects.link(spline_obj)
    return spline_obj


def copy_spline(spline):
    """
    copy_spline(spline spline) -> curve spline_obj

        Copies the specified spline of a curve and returns a curve object
        which only contains a copy of the given spline.
        (for now only works on NURBS curves)

        spline spline - the spline to copy
    """

    def copy_spline_points(spline, spline_copy):
        point_attrs = ["co",
                       "radius",
                       "select",
                       "tilt",
                       "weight",
                       "weight_softbody"]
        spline_copy.points.add(count=len(spline.points) - 1)
        for p, p_copy in zip(spline.points, spline_copy.points):
            for attr in point_attrs:
                setattr(p_copy, attr, getattr(p, attr))

    def copy_spline_attrs(spline, spline_copy):
        spline_attrs = ["order_u",
                        "order_v",
                        "radius_interpolation",
                        "resolution_u",
                        "resolution_v",
                        "tilt_interpolation",
                        "use_bezier_u",
                        "use_bezier_v",
                        "use_cyclic_u",
                        "use_cyclic_v",
                        "use_endpoint_u",
                        "use_endpoint_v",
                        "use_smooth"]
        for attr in spline_attrs:
            setattr(spline_copy, attr, getattr(spline, attr))

    if not (spline.points or spline.type == 'NURBS'):
        return
    name = "{}_copy".format(spline.id_data.name)
    # Create a new curve
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    spline_copy = curve.splines.new(spline.type)
    # Copy points
    copy_spline_points(spline, spline_copy)
    copy_spline_attrs(spline, spline_copy)
    spline_obj = bpy.data.objects.new(name, curve)
    # bpy.context.scene.objects.link(spline_obj)

    return spline_obj


def get_curve_verts(spline_obj,
                    use_modifiers=True,
                    settings='PREVIEW',
                    discard_object=True):
    scene = bpy.context.scene
    # Create a temporary mesh
    spline_mesh = spline_obj.to_mesh(scene, use_modifiers, settings)
    # Store verts of mesh
    verts = [v.co for v in spline_mesh.vertices]
    # Discard temporary mesh
    bpy.data.meshes.remove(spline_mesh)
    # Discard spline object
    if discard_object:
        bpy.data.objects.remove(spline_obj)

    return verts


def create_test_meshes(all_verts):
    context = bpy.context
    scene = context.scene
    data = bpy.data

    def create_mesh_from_vertices(points):
        mesh = bpy.data.meshes.new("test_mesh")
        verts = [(v.x, v.y, v.z) for v in points]
        edges = [(i, i + 1) for i, _ in enumerate(points[:-1])]
        mesh.from_pydata(verts, edges, [])
        return mesh

    for verts in all_verts:
        # mesh = data.meshes.new("test_mesh")
        # bm = bmesh.new()
        # bm.from_mesh(mesh)
        # for v in verts:
        #     bm.verts.new(v)
        # bm.verts.ensure_lookup_table()
        # for i, v in enumerate(bm.verts[:-1]):
        #     bm.edges.new((v, bm.verts[i + 1]))

        # bm.to_mesh(mesh)
        mesh = create_mesh_from_vertices(verts)

        obj = data.objects.new("test_obj", mesh)
        coll = context.view_layer.active_layer_collection.collection
        coll.objects.link(obj)


##############################################################################
## Function to get points on a nurbs spline. (Thanks to Pink Vertex.)
## Needs evaluation, cleanup and bladiebla, bla bla bla. But works fine!
##############################################################################

def get_nurbs_points(spline_points=None, curve=None,
                     curve_obj=None, spline_index=0, world_space=False):

    def macro_knotsu(use_cyclic_u, order_u, point_count_u):
        if use_cyclic_u:
            return order_u + point_count_u + (order_u - 1)
        else:
            return order_u + point_count_u + order_u

    def macro_segmentsu(use_cyclic_u, point_count_u):
        if use_cyclic_u:
            return point_count_u
        else:
            return point_count_u - 1

    def makeknots(use_cyclic_u, order_u, point_count_u,
                  use_endpoint_u, use_bezier_u):
        knots = [0.0] * (4 + macro_knotsu(use_cyclic_u,
                                          order_u,
                                          point_count_u))
        flag = use_endpoint_u + (use_bezier_u << 1)
        if use_cyclic_u:
            calcknots(knots, point_count_u, order_u, 0)
            makecyclicknots(knots, point_count_u, order_u)
        else:
            calcknots(knots, point_count_u, order_u, flag)
        return knots

    def calcknots(knots, pnts, order, flag):
        pnts_order = pnts + order
        if flag == 1:
            k = 0.0
            for a in range(1, pnts_order + 1):
                knots[a - 1] = k
                if a >= order and a <= pnts:
                    k += 1.0
        elif flag == 2:
            if order == 4:
                k = 0.34
                for a in range(pnts_order):
                    knots[a] = math.floor(k)
                    k += (1.0 / 3.0)
            elif order == 3:
                k = 0.6
                for a in range(pnts_order):
                    if a >= order and a <= pnts:
                        k += 0.5
                        knots[a] = math.floor(k)
        else:
            for a in range(pnts_order):
                knots[a] = a

    def makecyclicknots(knots, pnts, order):
        order2 = order - 1

        if order > 2:
            b = pnts + order2
            for a in range(1, order2):
                if knots[b] != knots[b - a]:
                    break

                if a == order2:
                    knots[pnts + order - 2] += 1.0

        b = order
        c = pnts + order + order2
        for a in range(pnts + order2, c):
            knots[a] = knots[a - 1] + (knots[b] - knots[b - 1])
            b -= 1

    def basisNurb(t, order, pnts, knots, basis, start, end):
        i1 = i2 = 0
        orderpluspnts = order + pnts
        opp2 = orderpluspnts - 1

        # this is for float inaccuracy
        if t < knots[0]:
            t = knots[0]
        elif t > knots[opp2]:
            t = knots[opp2]

        # this part is order '1'
        o2 = order + 1
        for i in range(opp2):
            if knots[i] != knots[i + 1] and t >= knots[i] and t <= knots[i + 1]:
                basis[i] = 1.0
                i1 = i - o2
                if i1 < 0:
                    i1 = 0
                i2 = i
                i += 1
                while i < opp2:
                    basis[i] = 0.0
                    i += 1
                break

            else:
                basis[i] = 0.0

        basis[i] = 0.0

        # this is order 2, 3, ...
        for j in range(2, order + 1):

            if i2 + j >= orderpluspnts:
                i2 = opp2 - j

            for i in range(i1, i2 + 1):
                if basis[i] != 0.0:
                    d = ((t - knots[i]) * basis[i]) / (knots[i + j - 1] - knots[i])
                else:
                    d = 0.0

                if basis[i + 1] != 0.0:
                    e = ((knots[i + j] - t) * basis[i + 1]) / \
                        (knots[i + j] - knots[i + 1])
                else:
                    e = 0.0

                basis[i] = d + e

        start = 1000
        end = 0

        for i in range(i1, i2 + 1):
            if basis[i] > 0.0:
                end = i
                if start == 1000:
                    start = i

        return start, end

    def nurb_make_curve(resolu, stride, nu=None, points=None):
        if not nu and not points:
            return

        if nu:
            resolution_u = nu.resolution_u
            point_count_u = nu.point_count_u
            order_u = nu.order_u
            use_cyclic_u = nu.use_cyclic_u
            points = [p.co for p in nu.points]
            use_endpoint_u = nu.use_endpoint_u
            use_bezier_u = nu.use_bezier_u
        else:
            # Values are the values I want for now :)
            resolution_u = 12
            point_count_u = len(points)
            order_u = 3
            use_cyclic_u = False
            points = points
            use_endpoint_u = True
            use_bezier_u = False
        macro_segments_u = macro_segmentsu(use_cyclic_u, point_count_u)
        macro_knots_u = macro_knotsu(use_cyclic_u, order_u, point_count_u)
        knots = makeknots(use_cyclic_u, order_u, point_count_u,
                          use_endpoint_u, use_bezier_u)

        EPS = 1e-6
        coord_index = istart = iend = 0

        coord_array = [0.0] * (3 * resolution_u * macro_segments_u)
        sum_array = [0] * point_count_u
        basisu = [0.0] * macro_knots_u

        resolu = resolu * macro_segments_u
        ustart = knots[order_u - 1]
        if use_cyclic_u:
            uend = knots[point_count_u + order_u - 1]
            ustep = (uend - ustart) / resolu
            cycl = order_u - 1
        else:
            uend = knots[point_count_u]
            ustep = (uend - ustart) / (resolu - 1)
            cycl = 0

        u = ustart
        while resolu:
            resolu -= 1
            istart, iend = basisNurb(u,
                                     order_u,
                                     point_count_u + cycl,
                                     knots,
                                     basisu,
                                     istart,
                                     iend)

            #/* calc sum */
            sumdiv = 0.0
            sum_index = 0
            pt_index = istart - 1
            for i in range(istart, iend + 1):
                if i >= point_count_u:
                    pt_index = i - point_count_u
                else:
                    pt_index += 1

                sum_array[sum_index] = basisu[i] * points[pt_index][3]
                sumdiv += sum_array[sum_index]
                sum_index += 1

            if (sumdiv != 0.0) and (sumdiv < 1.0 - EPS or sumdiv > 1.0 + EPS):
                sum_index = 0
                for i in range(istart, iend + 1):
                    sum_array[sum_index] /= sumdiv
                    sum_index += 1

            coord_array[coord_index: coord_index + 3] = (0.0, 0.0, 0.0)

            sum_index = 0
            pt_index = istart - 1
            for i in range(istart, iend + 1):
                if i >= point_count_u:
                    pt_index = i - point_count_u
                else:
                    pt_index += 1

                if sum_array[sum_index] != 0.0:
                    for j in range(3):
                        coord_array[coord_index + j] += sum_array[sum_index] * points[pt_index][j]
                sum_index += 1

            coord_index += stride
            u += ustep

        return coord_array

    if not spline_points and not curve:
        return

    if curve:
        spline = curve.splines[spline_index]
        if curve.render_resolution_u:
            resolution = curve.render_resolution_u
        else:
            resolution = curve.resolution_u
        coord_array = nurb_make_curve(resolution, 3, nu=spline)

    else:   # spline_points are given
        resolution = 12
        spline_points = [p.to_4d() for p in spline_points]
        coord_array = nurb_make_curve(resolution, 3, points=spline_points)

    points = [mathutils.Vector(coord_array[i: i + 3])
              for i in range(0, len(coord_array), 3)]

    if world_space and curve_obj:
        matrix_world = curve_obj.matrix_world
        points = [matrix_world * p for p in points]

    return points





# start = time.time()
# source_object = bpy.context.object
# all_verts = []
# for spline in source_object.data.splines:
#     # spline = bpy.context.object.data.splines[i]
#     spline_obj = copy_spline(spline)
#     # bpy.context.scene.update()
#     if spline_obj:
#         # bpy.context.scene.update()
#         verts = get_curve_verts(spline_obj, discard_object=True)
#         # bpy.context.scene.update()
#         all_verts.append(verts)
# print("Processed in {} seconds...".format(time.time() - start))
# for verts in all_verts:
#     print()
#     for v in verts:
#         print(v)

# bpy.context.scene.update()
# create_test_meshes(all_verts)
# bpy.context.scene.update()




# Copy 1 spline of a curve to another curve
# import bpy

# source_curve = bpy.data.objects['source']
# target_curve = bpy.data.objects['target']

# def copy_spline(spline_index):
#     source_spline = source_curve.data.splines[spline_index]
#     target_spline = target_curve.data.splines.new(source_spline.type)
#     if source_spline.type == 'BEZIER':
#         num_points = len(source_spline.bezier_points)
#         target_spline.bezier_points.add(count=num_points - 1)
#         for sp, tp in zip(source_spline.bezier_points, target_spline.bezier_points):
#             tp.co = sp.co
#             tp.handle_left = sp.handle_left
#             tp.handle_right = sp.handle_right
#             tp.handle_left_type = sp.handle_left_type
#             tp.handle_right_type = sp.handle_right_type
#             tp.hide = sp.hide
#             tp.radius = sp.radius
#             tp.tilt = sp.tilt
#             tp.weight_softbody = sp.weight_softbody

# copy_spline(1)
