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


# Import modules.

import bpy
from bpy.props import (IntProperty, FloatProperty, BoolProperty, EnumProperty)
from . import curve_tools
from . import mesh_tools
import itertools
import random



class CURVE_OT_Spiderweb(bpy.types.Operator):
    """Add a spiderweb (or wires) between the selected objects"""
    bl_idname = "curve.spiderweb"
    bl_label = "Create spiderweb"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    def __init__(self):
        # Because creating a lot of wires can take some time and slow down the
        # viewport, set the initial amount of wires to 50 if it is higher.
        self.amount = 50

    amount : IntProperty(name="Amount",
                         description="The number of strands to create",
                         default=20,
                         min=2,
                         max=999999,
                         soft_max=100)
    main_iterations : IntProperty(name="Iterations",
                                  description="Iterations",
                                  default=1,
                                  min=1,
                                  max=100)
    include_sub : BoolProperty(name="Recursive sub strands",
                               description="Sub strands will also be "
                                           "generated between already"
                                           " generated sub strands",
                               default=True)
    sub_iterations : IntProperty(name="Iterations",
                                 description="Iterations",
                                 default=3,
                                 min=0,
                                 max=999999,
                                 soft_max=100)
    method_items = [('PIVOT', 'Pivot', 'Sample from pivot points (Will not '
                                       'return more points then the number '
                                       'of selected objects'),
                    ('VOLUME', 'Volume', 'Sample from the volume(s)'),
                    ('SURFACE', 'Surface', 'Sample from surface(s)'),
                    ('EDGES', 'Edges', 'Sample from edges'),
                    ('VERTS', 'Vertices', 'Sample from vertices')]
    method : EnumProperty(name="Method",
                          description="Where to sample the end points of the "
                                      "curves from",
                          items=method_items,
                          default='SURFACE')
    seed : IntProperty(name="Seed",
                       description="The seed to use for the generation "
                                   "(change it to get a different variant "
                                   "of the web)",
                       default=0)
    drape_min : FloatProperty(name="Drape min",
                              description="The minimum drape of the strands",
                              default=-1.0,
                              soft_min=-50.0,
                              soft_max=50.0,
                              step=10)
    drape_max : FloatProperty(name="Drape max",
                              description="The maximum drape of the strands",
                              default=0,
                              soft_min=-50.0,
                              soft_max=50.0,
                              step=10)
    length_solver : BoolProperty(name="Length solver",
                                 description="The amount of drape is also "
                                             "dependent on the length of "
                                             "the strand",
                                 default=True)

    # Draw
    def draw(self, context):
        random.seed(self.seed)
        layout = self.layout

        # Options
        box = layout.box()
        box.label(text="Main strands")
        box.prop(self, 'amount')
        box.prop(self, 'main_iterations')
        box = layout.box()
        box.label(text="Sub strands")
        box.prop(self, 'include_sub')
        box.prop(self, 'sub_iterations')
        box = layout.box()
        box.label(text="General options")
        box.prop(self, 'method')
        box.prop(self, 'seed')
        box.prop(self, 'drape_min')
        box.prop(self, 'drape_max')
        box.prop(self, 'length_solver')

    # Poll
    @classmethod
    def poll(cls, context):
        if context.selected_objects:
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    return True

    # Execute
    def execute(self, context):

        def drape_spline(spline):
            drape = random.uniform(self.drape_min, self.drape_max)
            # For now only a spline with 3 points works
            if self.length_solver:
                simple_length = (spline[2] - spline[0]).length / 5
            else:
                simple_length = 1
            spline[1].z += drape * simple_length

            return spline

        def drape_splines(splines):
            draped_splines = []
            for spline in splines:
                spline = drape_spline(spline)
                draped_splines.append(spline)

            return draped_splines

        selected_objects = bpy.context.selected_objects
        web_objects = [obj for obj in selected_objects if obj.type == 'MESH']

        # Get (random) points on/in the selected objects.
        end_points = []
        # Determine how many points to create per object,
        # to get <amount> total points.
        quotient, remainder = divmod(self.amount, len(web_objects))
        # Randomize order of selected objects
        random.seed(self.seed)
        random.shuffle(web_objects)
        for i, obj in enumerate(web_objects):
            if i in range(remainder):
                obj_amount = quotient + 1
            else:
                obj_amount = quotient
            points = mesh_tools.get_points(obj, amount=obj_amount, method=self.method, apply_modifiers=True, seed=self.seed)
            end_points.append([obj, points])

        end_vectors = list(itertools.chain(*(l[1] for l in end_points)))

        # Create splines between two random points.
        #if not len(end_vectors) > 1:
            # We need at least 2 points.
            #return

        # Create the points of the main strands (every spline has 3 points)
        main_splines = []
        random.seed(self.seed)
        for i in range(self.main_iterations):
            for ip, start_point in enumerate(end_vectors):
                for _ in range(9999):
                    end_point = random.choice(end_vectors)
                    if not end_point == start_point:
                        break
                mid_point = start_point + (end_point - start_point) * 0.5
                main_splines.append((start_point, mid_point, end_point))

        # Drape main splines
        random.seed(self.seed)
        main_splines = drape_splines(main_splines)

        def sub_strands_iter(splines, count=0):
            if count >= self.sub_iterations:
                return splines
            splines += create_sub_strands(splines)
            count += 1
            return sub_strands_iter(splines, count)

        def create_sub_strands(splines, points=None):
            new_splines = []
            if not points:
                resolution_points = [curve_tools.get_nurbs_points(spline)
                                     for spline in splines]
            else:
                resolution_points = points
            for _ in range(0, len(resolution_points), 2):
                # Pick a random spline to start from
                spline1 = random.choice(resolution_points)
                # Pick a random spline to end which is not the start spline
                for _ in range(9999):
                    spline2 = random.choice(resolution_points)
                    if not spline2 == spline1:
                        break
                # Pick a random start point from spline1
                start_index = int(random.triangular(0, len(spline1)))
                start_point = spline1[start_index]
                # Pick a ranomd end point from spline2
                end_index = int(random.triangular(0, len(spline2)))
                end_point = spline2[end_index]
                # Create the mid point
                mid_point = start_point + (end_point - start_point) * 0.5
                new_spline = (start_point, mid_point, end_point)
                # Drape the spline
                new_spline = drape_spline(new_spline)
                new_splines.append(new_spline)
                splines.append(new_spline)

            return new_splines

        random.seed(self.seed)
        if self.sub_iterations and self.include_sub:
            splines = sub_strands_iter(main_splines)
        elif self.sub_iterations and not self.include_sub:
            sub_splines = []
            points = [curve_tools.get_nurbs_points(spline)
                      for spline in main_splines]
            for _ in range(self.sub_iterations):
                sub_splines += create_sub_strands(main_splines, points)
            splines = main_splines + sub_splines
        else:
            splines = main_splines

        curve = curve_tools.create_curve(name="web")
        # for spline in main_splines + sub_splines:
        for spline in splines:
            points = [p for p in spline]
            curve_tools.create_spline(curve=curve, points=points)

        web = bpy.data.objects.new("web", curve)
        bpy.context.collection.objects.link(web)
        bpy.context.view_layer.objects.active = web

        return {'FINISHED'}

    # Invoke
    def invoke(self, context, event):
        self.execute(context)

        return {'FINISHED'}
