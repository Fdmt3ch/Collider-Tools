from os import path as os_path
from subprocess import Popen

import bmesh
import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty
from mathutils import Matrix
from .off_eport import off_export

from bpy.types import Operator
from ..operators.add_bounding_primitive import OBJECT_OT_add_bounding_object

collider_shapes = ['boxColSuffix','sphereColSuffix', 'convexColSuffix', 'meshColSuffix']

class VHACD_OT_convex_decomposition(OBJECT_OT_add_bounding_object, Operator):
    bl_idname = 'collision.vhacd'
    bl_label = 'Convex Decomposition'
    bl_description = 'Split the object collision into multiple convex hulls using Hierarchical Approximate Convex Decomposition'
    bl_options = {'REGISTER', 'PRESET'}

    # TODO Remove
    # pre-process options
    remove_doubles: BoolProperty(
        name='Remove Doubles',
        description='Collapse overlapping vertices in generated mesh',
        default=True
    )

    # TODO Remove
    apply_transforms: EnumProperty(
        name='Apply',
        description='Apply Transformations to generated mesh',
        items=(
            ('LRS', 'Location + Rotation + Scale', 'Apply location, rotation and scale'),
            ('RS', 'Rotation + Scale', 'Apply rotation and scale'),
            ('S', 'Scale', 'Apply scale only'),
            ('NONE', 'None', 'Do not apply transformations'),
        ),
        default='NONE'
    )

    # VHACD parameters
    resolution: IntProperty(
        name='Voxel Resolution',
        description='Maximum number of voxels generated during the voxelization stage',
        default=100000,
        min=10000,
        max=64000000
    )

    depth: IntProperty(
        name='Clipping Depth',
        description='Split the object into square of this objects',
        default=2,
        min=1,
        max=32
    )

    concavity: FloatProperty(
        name='Maximum Concavity',
        description='Maximum concavity',
        default=0.0015,
        min=0.0,
        max=1.0,
        precision=4
    )

    # Quality settings
    planeDownsampling: IntProperty(
        name='Plane Downsampling',
        description='Granularity of the search for the "best" clipping plane',
        default=4,
        min=1,
        max=16
    )

    # Quality settings
    convexhullDownsampling: IntProperty(
        name='Convex Hull Downsampling',
        description='Precision of the convex-hull generation process during the clipping plane selection stage',
        default=4,
        min=1,
        max=16
    )

    alpha: FloatProperty(
        name='Alpha',
        description='Bias toward clipping along symmetry planes',
        default=0.05,
        min=0.0,
        max=1.0,
        precision=4
    )

    beta: FloatProperty(
        name='Beta',
        description='Bias toward clipping along revolution axes',
        default=0.05,
        min=0.0,
        max=1.0,
        precision=4
    )

    gamma: FloatProperty(
        name='Gamma',
        description='Maximum allowed concavity during the merge stage',
        default=0.00125,
        min=0.0,
        max=1.0,
        precision=5
    )

    pca: BoolProperty(
        name='PCA',
        description='Enable/disable normalizing the mesh before applying the convex decomposition',
        default=False
    )

    mode: EnumProperty(
        name='ACD Mode',
        description='Approximate convex decomposition mode',
        items=(('VOXEL', 'Voxel', 'Voxel ACD Mode'),
               ('TETRAHEDRON', 'Tetrahedron', 'Tetrahedron ACD Mode')),
        default='VOXEL'
    )

    maxNumVerticesPerCH: IntProperty(
        name='Maximum Vertices Per CH',
        description='Maximum number of vertices per convex-hull',
        default=32,
        min=4,
        max=1024
    )

    minVolumePerCH: FloatProperty(
        name='Minimum Volume Per CH',
        description='Minimum volume to add vertices to convex-hulls',
        default=0.0001,
        min=0.0,
        max=0.01,
        precision=5
    )


    def set_export_path(self, path):

        self.type_suffix = self.prefs.convexColSuffix

        # Check executable path
        executable_path = bpy.path.abspath(path)
        if os_path.isdir(executable_path):
            executable_path = os_path.join(executable_path, 'testVHACD')
            return executable_path

        elif not os_path.isfile(executable_path):
            self.report({'ERROR'}, 'Path to V-HACD executable required')
            return {'CANCELLED'}

        if not os_path.exists(executable_path):
            self.report({'ERROR'}, 'Cannot find V-HACD executable at specified path')
            return {'CANCELLED'}

        return executable_path

    def set_data_path(self, path):
        # Check data path
        data_path = bpy.path.abspath(path)

        if data_path.endswith('/') or data_path.endswith('\\'):
            data_path = os_path.dirname(data_path)
            return data_path

        if not os_path.exists(data_path):
            self.report({'ERROR'}, 'Invalid data directory')
            return {'CANCELLED'}

        return data_path


    def __init__(self):
        super().__init__()

    def invoke(self, context, event):
        super().invoke(context, event)
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)
        # return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        super().invoke(context, event)
        self.collider_shapes_idx = 0
        self.collider_shapes = collider_shapes
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        status = super().modal(context, event)
        if status == {'FINISHED'}:
            return {'FINISHED'}
        if status == {'CANCELLED'}:
            return {'CANCELLED'}

        elif event.type == 'C' and event.value == 'RELEASE':
            #toggle through display modes
            self.collider_shapes_idx = (self.collider_shapes_idx + 1) % len(self.collider_shapes)
            self.set_name_suffix()
            self.update_names()
        return {'RUNNING_MODAL'}

    def execute(self, context):
        # CLEANUP
        super().execute(context)

        executable_path = self.set_export_path(self.prefs.executable_path)
        data_path = self.set_data_path(self.prefs.data_path)

        if executable_path == {'CANCELLED'} or data_path == {'CANCELLED'}:
            return {'CANCELLED'}

        selected = bpy.context.selected_objects.copy()

        if not selected:
            self.report({'ERROR'}, 'Object(s) must be selected first')
            return {'CANCELLED'}

        for ob in selected:
            ob.select_set(False)

        for ob in selected:
            if ob.type != 'MESH':
                continue

            # Base filename is object name with invalid characters removed
            filename = ''.join(c for c in ob.name if c.isalnum() or c in (' ', '.', '_')).rstrip()

            off_filename = os_path.join(data_path, '{}.off'.format(filename))
            outFileName = os_path.join(data_path, '{}.wrl'.format(filename))
            logFileName = os_path.join(data_path, '{}_log.txt'.format(filename))

            mesh = ob.data.copy()

            translation, quaternion, scale = ob.matrix_world.decompose()
            scale_matrix = Matrix(((scale.x, 0, 0, 0), (0, scale.y, 0, 0), (0, 0, scale.z, 0), (0, 0, 0, 1)))
            if self.apply_transforms in ['S', 'RS', 'LRS']:
                pre_matrix = scale_matrix
                post_matrix = Matrix()
            else:
                pre_matrix = Matrix()
                post_matrix = scale_matrix
            if self.apply_transforms in ['RS', 'LRS']:
                pre_matrix = quaternion.to_matrix().to_4x4() @ pre_matrix
            else:
                post_matrix = quaternion.to_matrix().to_4x4() @ post_matrix
            if self.apply_transforms == 'LRS':
                pre_matrix = Matrix.Translation(translation) @ pre_matrix
            else:
                post_matrix = Matrix.Translation(translation) @ post_matrix

            mesh.transform(pre_matrix)

            bm = bmesh.new()
            bm.from_mesh(mesh)
            if self.remove_doubles:
                bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)

            bmesh.ops.triangulate(bm, faces=bm.faces)
            bm.to_mesh(mesh)
            bm.free()

            print('\nExporting mesh for V-HACD: {}...'.format(off_filename))
            off_export(mesh, off_filename)
            cmd_line = ('"{}" --input "{}" --resolution {} --depth {} '
                        '--concavity {:g} --planeDownsampling {} --convexhullDownsampling {} '
                        '--alpha {:g} --beta {:g} --gamma {:g} --pca {:b} --mode {:b} '
                        '--maxNumVerticesPerCH {} --minVolumePerCH {:g} --output "{}" --log "{}"').format(
                executable_path, off_filename, self.resolution, self.depth,
                self.concavity, self.planeDownsampling, self.convexhullDownsampling,
                self.alpha, self.beta, self.gamma, self.pca, self.mode == 'TETRAHEDRON',
                self.maxNumVerticesPerCH, self.minVolumePerCH, outFileName, logFileName)

            print('Running V-HACD...\n{}\n'.format(cmd_line))

            vhacd_process = Popen(cmd_line, bufsize=-1, close_fds=True, shell=True)
            bpy.data.meshes.remove(mesh)
            vhacd_process.wait()

            if not os_path.exists(outFileName):
                continue

            bpy.ops.import_scene.x3d(filepath=outFileName, axis_forward='Y', axis_up='Z')
            imported = bpy.context.selected_objects
            self.new_colliders_list.extend(imported)

            name_template = self.prefs.name_template

            for index, hull in enumerate(imported):
                hull.select_set(False)
                hull.matrix_basis = post_matrix
                name = name_template.replace('?', ob.name, 1)
                name = name.replace('#', str(index + 1), 1)
                if name == name_template:
                    name += str(index + 1)
                hull.name = name
                hull.data.name = name
                # Display
                hull.display_type = 'SOLID'
                hull.color[3] = 0.5
                # hull.display.show_shadows = False
                # hull.show_all_edges = True

        if len(self.new_colliders_list) < 1:
            self.report({'WARNING'}, 'No meshes to process!')
            return {'CANCELLED'}

        super().reset_to_initial_state(context)

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(self, 'depth', text="Collision Number")
        row = layout.row()
        row.prop(self, 'maxNumVerticesPerCH', text="Collision Vertices")
