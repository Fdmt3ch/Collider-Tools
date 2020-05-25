import bmesh
import bpy
from bpy.props import (
    EnumProperty,
    FloatProperty,
)

from bpy.types import Operator
from bpy_extras.object_utils import AddObjectHelper, object_data_add
from mathutils import Vector

from CollisionHelpers.operators.collision_helpers import alignObjects, getBoundingBox, setColliderSettings


# TODO: Global, local switch works only in edit mode
# TODO: Add transparency also to material display
# TODO: Turn rendering off for colliders
# DONE: Material options ()
# TODO: Additional spaces: view and optimal heuristic blablabla
# TODO: Support multi edit for collision creation (connected, and individual generation)
# TODO: Parenting -> add collisions to useful place in the hierarchy
# TODO: Naming -> check current naming options
# TODO: SELECT all collisions after finishing operation

def add_box_object(context, vertices, newName):
    """Generate a new object from the given vertices"""
    verts = vertices
    edges = []
    faces = [[0, 1, 2, 3], [7, 6, 5, 4], [5, 6, 2, 1], [0, 3, 7, 4], [3, 2, 6, 7], [4, 5, 1, 0]]

    mesh = bpy.data.meshes.new(name=newName)
    mesh.from_pydata(verts, edges, faces)

    # useful for development when the mesh may be invalid.
    # mesh.validate(verbose=True)
    newObj = object_data_add(context, mesh, operator=None, name=None)  # links to object instance

    return newObj


def add_box(context, space):
    """ """

    obj = context.edit_object
    me = obj.data

    # Get a BMesh representation
    bm = bmesh.from_edit_mesh(me)

    selected_verts = [v for v in bm.verts if v.select]
    vertsLoc = []

    # Modify the BMesh, can do anything here...
    positionsX = []
    positionsY = []
    positionsZ = []

    if space == 'GLOBAL':
        for v in selected_verts:
            v_local = v
            v_global = obj.matrix_world @ v_local.co

            positionsX.append(v_global[0])
            positionsY.append(v_global[1])
            positionsZ.append(v_global[2])

        # for v in selected_verts:
        #     mat = obj.matrix_world
        #     vertsLoc.append(v.transform(mat))
    else:
        for v in selected_verts:
            positionsX.append(v.co.x)
            positionsY.append(v.co.y)
            positionsZ.append(v.co.z)

    verts = [
        (max(positionsX), max(positionsY), min(positionsZ)),
        (max(positionsX), min(positionsY), min(positionsZ)),
        (min(positionsX), min(positionsY), min(positionsZ)),
        (min(positionsX), max(positionsY), min(positionsZ)),
        (max(positionsX), max(positionsY), max(positionsZ)),
        (max(positionsX), min(positionsY), max(positionsZ)),
        (min(positionsX), min(positionsY), max(positionsZ)),
        (min(positionsX), max(positionsY), max(positionsZ)),
    ]

    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (4, 0, 3, 7),
    ]

    return verts, faces


def box_Collider_from_Editmode(self, context, verts_loc, faces, nameSuf):
    """ """
    active_ob = bpy.context.object
    root_col = bpy.context.scene.collection

    mesh = bpy.data.meshes.new("Box")
    bm = bmesh.new()

    for v_co in verts_loc:
        bm.verts.new(v_co)

    bm.verts.ensure_lookup_table()
    for f_idx in faces:
        bm.faces.new([bm.verts[i] for i in f_idx])

    bm.to_mesh(mesh)
    mesh.update()

    # # add the mesh as an object into the scene with this utility module
    # from bpy_extras import object_utils
    # object_utils.object_data_add(context, mesh, operator=self)
    newCollider = bpy.data.objects.new(active_ob.name + nameSuf, mesh)
    root_col.objects.link(newCollider)

    if self.my_space == 'LOCAL':
        alignObjects(newCollider, active_ob)

    return newCollider


def box_Collider_from_Objectmode(context, name, obj, i):
    """Create box collider for every selected object in object mode"""
    colliderOb = []

    bBox = getBoundingBox(obj)  # create BoundingBox object for collider
    newCollider = add_box_object(context, bBox, name)

    # local_bbox_center = 1/8 * sum((Vector(b) for b in obj.bound_box), Vector())
    # global_bbox_center = obj.matrix_world @ local_bbox_center
    centreBase = sum((Vector(b) for b in obj.bound_box), Vector())
    # print ('CENTRE' + str(centreBase))
    centreBase /= 8
    # print ('CENTRE 2 ' + str(centreBase))
    # newCollider.matrix_world = centreBase

    alignObjects(newCollider, obj)

    return newCollider


class OBJECT_OT_add_box_collision(Operator, AddObjectHelper):
    """Create a new Mesh Object"""
    bl_idname = "mesh.add_box_collision"
    bl_label = "Add Box Collision"
    bl_options = {'REGISTER', 'UNDO'}

    my_collision_shading_view: EnumProperty(
        name="Axis",
        items=(
            ('SOLID', "SOLID", "SOLID"),
            ('WIRE', "WIRE", "WIRE"),
            ('BOUNDS', "BOUNDS", "BOUNDS"),
        )
    )

    my_space: EnumProperty(
        name="Axis",
        items=(
            ('LOCAL', "LOCAL", "LOCAL"),
            ('GLOBAL', "GLOBAL", "GLOBAL")),
        default="LOCAL"
    )

    my_offset: FloatProperty(
        name="Offset",
        default=0.0
    )

    my_color: bpy.props.FloatVectorProperty(
        name="Collision Color", description="", default=(0.36, 0.5, 1, 0.25), min=0.0, max=1.0,
        subtype='COLOR', size=4
    )

    def execute(self, context):
        prefs = bpy.context.preferences.addons['CollisionHelpers'].preferences
        colSuffix = prefs.colSuffix
        colPreSuffix = prefs.colPreSuffix
        boxColSuffix = prefs.boxColSuffix

        scene = context.scene
        matName = scene.CollisionMaterials

        nameSuf = colPreSuffix + boxColSuffix + colSuffix
        if context.object.mode == "EDIT":
            verts_loc, faces = add_box(context, self.my_space)
            newCollider = box_Collider_from_Editmode(self, context, verts_loc, faces, nameSuf)
            setColliderSettings(self, context, newCollider, matName)
        else:
            for i, obj in enumerate(context.selected_objects.copy()):
                newCollider = box_Collider_from_Objectmode(context, nameSuf, obj, i)
                setColliderSettings(self, context, newCollider, matName)

        return {'FINISHED'}

#
# import bpy
# import time
# from collections import defaultdict
#
#
# def GetAllVerticesNeighbors(verts, edges):
#     """Returns a dictionary with the vertex indes as key and a dictionary of all connected vertices as dictionary"""
#     # Initialize the path with all vertices indexes
#     result = {v.index: set() for v in verts}
#     # Add the possible paths via edges
#     for e in edges:
#         result[e.vertices[0]].add(e.vertices[1])
#         result[e.vertices[1]].add(e.vertices[0])
#     return result
#
#
# def FollowEdges(startingIndex, stored_vertices):
#     current_vert_idx = [startingIndex]
#
#     follow = True
#     while follow:
#         # Get indexes that are still in the stored_vertices
#         eligible = set([ind for ind in current_vert_idx if ind in stored_vertices])
#         if len(eligible) == 0:
#             follow = False  # Stops if no more
#         else:
#             # Get the corresponding links
#             next = [stored_vertices[i] for i in eligible]
#             # Remove the previous from the paths
#             for key in eligible: stored_vertices.pop(key)
#             # Get the new links as new inputs
#             current_vert_idx = set([ind for sub in next for ind in sub])
#
#
# def CountIslands(obj):
#     # Prepare the paths/links from each vertex to others
#     stored_vertices = GetAllVerticesNeighbors(obj.data.vertices, obj.data.edges)
#     print("paths" + str(stored_vertices))
#     found = True
#     n = 0
#
#     while found:
#         try:
#             # Get one input as long there is one
#             startingIndex = next(iter(stored_vertices.keys()))
#             n = n + 1
#             # Deplete the paths dictionary following this starting index
#             FollowEdges(startingIndex, stored_vertices)
#         except:
#             found = False
#     return n
#
#
# print('-------------')
#
# # The wanted object
# obj = bpy.context.object
#
# start_time = time.time()
#
# for i in range(1):  # For testing purpose in order to evaluate runtime elapse
#     print('islands', CountIslands(obj))
#
# elapsed_time = time.time() - start_time
# print(elapsed_time)