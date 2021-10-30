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


bl_info = {
    "name": "Create spider webs",
    "author": "Jasper van Nieuwenhuizen",
    "version": (0, 2),
    "blender": (2, 83, 0),
    "location": "View3D > Add > Curve ",
    "description": "Create spider webs or wires between objects",
    "warning": "wip",
    "doc_url": "",
    "tracker_url": "",
    "support": 'COMMUNITY',
    "category": "Add Curve"}



if "bpy" in locals():
    import importlib
    importlib.reload(add_curve_spiderwebs)
else:
    from . import add_curve_spiderwebs
import bpy

# Register
classes = (
    add_curve_spiderwebs.CURVE_OT_Spiderweb,

)

# Register

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.VIEW3D_MT_curve_add.append(Spiderweb_menu_item)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    bpy.types.VIEW3D_MT_curve_add.remove(Spiderweb_menu_item)

def Spiderweb_menu_item(self, context):
    self.layout.operator(add_curve_spiderwebs.CURVE_OT_Spiderweb.bl_idname,
                         text="Create spiderweb",
                         icon="OUTLINER_DATA_CURVE")

if __name__ == "__main__":
    register()
