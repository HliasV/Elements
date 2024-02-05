#### BEZIER 3D ####

import numpy as np
import bezier
import imgui

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh

from Elements.pyGLV.GL.Shader import Shader, ShaderGLDecorator
from Elements.pyGLV.GL.VertexArray import VertexArray

from OpenGL.GL import GL_LINES, GL_POINTS, glPointSize


input_bezier_control_nodes = [[0.0, 0.0, 0.0],[0.5, 0.2, 0.8],[-0.4, 1, -0.7]]
input_render_detail = 100


class BezierCurve:
    def __init__(self, bezier_entity, scene, root_entity, all_shaders, init_update) -> None:
        """Wrapper class for providing gui, rendering and logic for rendering a bezier curve in 3D space

        Args:
            bezier_entity (pyECSS.Entity): Entity to embed bezier curve into the scene
            scene (pyGLV.GL.Scene): Reference to the scene object
            root_entity (pyECSS.Entity): Reference to the root entity
            all_shaders (List): Wrapper for all shaders
            init_update (Function): Reference to init_update function
        """

        self.bezier_entity = bezier_entity
        self.scene = scene
        self.rootEntity = root_entity
        self.all_shaders = all_shaders
        self.initUpdate = init_update

    def render_gui_and_curve(self):
        """Function to display gui and trigger the rendering of the bezier curve.
        """
        global input_render_detail
        global input_bezier_control_nodes

        imgui.begin("Print Bezier Curve")

        imgui.text("Control nodes X, Y, Z")
        for i, control_node in enumerate(input_bezier_control_nodes):
            changed, input_bezier_control_nodes[i] = imgui.input_float3(f"Control Node {i + 1}", *control_node)

        button_remove_node_pressed = imgui.button("Remove Node")
        imgui.same_line()
        button_add_node_pressed = imgui.button("Add Node")
        if button_remove_node_pressed:
            input_bezier_control_nodes.pop()
        if button_add_node_pressed:
            input_bezier_control_nodes.append([0.0, 0.0, 0.0])

        button_bezier_pressed = imgui.button("Print Bezier")

        changed, input_render_detail = imgui.input_int('Detailed', input_render_detail)
        if imgui.is_item_hovered():
            imgui.set_tooltip("Make sure the detail is between 4 to 100")

        if button_bezier_pressed:
            input_bezier_control_nodes = [list(tuple) for tuple in input_bezier_control_nodes]
            self.render_curve(input_bezier_control_nodes, input_render_detail)

        imgui.end()

    def render_curve(self, bezier_control_nodes, render_detail):
        """Function for triggering computing bezier curve data and render curve into the scene

        Args:
            bezier_control_nodes (List): control nodes for the bezier curve from user input
            render_detail (Integer): Number of points to render on the bezier curve from user input
        """

        bezier_vertices, bezier_colors, bezier_indices = generate_bezier_data(bezier_control_nodes, render_detail)

        ## ADD / UPDATE BEZIER ##

        remove_entity_children(self.bezier_entity)

        bezier_trans = self.scene.world.addComponent(self.bezier_entity,
                                                     BasicTransform(name="bezier_trans", trs=util.identity()))
        bezier_mesh = self.scene.world.addComponent(self.bezier_entity, RenderMesh(name="bezier_mesh"))
        bezier_mesh.vertex_attributes.append(bezier_vertices)
        bezier_mesh.vertex_attributes.append(bezier_colors)
        bezier_mesh.vertex_index.append(bezier_indices)
        bezier_vArray = self.scene.world.addComponent(self.bezier_entity,
                                                      VertexArray(primitive=GL_LINES))  # note the primitive change

        bezier_shader = self.scene.world.addComponent(self.bezier_entity, ShaderGLDecorator(
            Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        self.all_shaders.append(bezier_shader)

        ## VISUALIZE BEZIER CONTROL NODES ##

        control_nodes_vertices = xyz_to_vertices(bezier_control_nodes)
        control_nodes_colors = np.array([[0.5, 0.5, 1.0, 1.0]] * len(control_nodes_vertices), dtype=np.float32)
        control_nodes_indices = np.array(range(len(control_nodes_vertices)), np.uint32)

        control_nodes = self.scene.world.createEntity(Entity(name="control_nodes"))
        self.scene.world.addEntityChild(self.bezier_entity, control_nodes)
        control_nodes_trans = self.scene.world.addComponent(control_nodes,
                                                            BasicTransform(name="control_nodes_trans",
                                                                           trs=util.identity()))
        control_nodes_mesh = self.scene.world.addComponent(control_nodes, RenderMesh(name="control_nodes_mesh"))
        control_nodes_mesh.vertex_attributes.append(control_nodes_vertices)
        control_nodes_mesh.vertex_attributes.append(control_nodes_colors)
        control_nodes_mesh.vertex_index.append(control_nodes_indices)
        glPointSize(5)
        control_nodes_vArray = self.scene.world.addComponent(control_nodes, VertexArray(primitive=GL_POINTS))

        control_nodes_shader = self.scene.world.addComponent(control_nodes, ShaderGLDecorator(
            Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        self.all_shaders.append(control_nodes_shader)

        self.scene.world.traverse_visit(self.initUpdate, self.scene.world.root)


def generate_bezier_data(bezier_control_nodes, num_points):
    """Compute bezier curve and generate vertices, colors and indices accordingly.

    Args:
        bezier_control_nodes (List): control nodes for the bezier curve from user input
        render_detail (Integer): Number of points to render on the bezier curve from user input

    Returns:
        List: Vertices (list), colors (list) and indices (list) for the bezier curve
    """
    
    bezier_curve = bezier.Curve.from_nodes(separate_coordinates(bezier_control_nodes))
    print("created bezier curve:", bezier_curve)

    x_values = np.linspace(0, 1, num_points)
    bezier_points = bezier_curve.evaluate_multi(x_values)
    bezier_points_xyz = combine_coordinates(bezier_points)

    bezier_vertices = np.array(vertices_to_line_vertices(xyz_to_vertices(bezier_points_xyz)), dtype=np.float32)

    bezier_colors = np.array([[0.5, 0.0, 1.0, 1.0]] * len(bezier_vertices), dtype=np.float32)

    bezier_indices = np.array(range(len(bezier_vertices)), np.uint32)

    return bezier_vertices, bezier_colors, bezier_indices


def vertices_to_line_vertices(coordinates):
    """Takes a list of vertices and converts in into a list of vertices so that a continous line is rendered in with GL_LINES

    Args:
        coordinates (List): List of coordinates to convert

    Returns:
        List: List of vertices for GL_LINES rendering mode
    """
    vertices = [coordinates[0]]
    for coord in coordinates[1:-1]:
        vertices.extend([coord, coord])
    vertices.append(coordinates[-1])
    return vertices


def separate_coordinates(coordinates):
    """Takes a list of coordinates and converts it into a different format

    Args:
        coordinates (List): Coordinates in the format [[x,y,z],[x,y,z],...]

    Returns:
        List: Coordinates in the format [[x,x,x],[y,y,y],[z,z,z]]
    """
    x_coordinates = [coord[0] for coord in coordinates]
    y_coordinates = [coord[1] for coord in coordinates]
    z_coordinates = [coord[2] for coord in coordinates]
    return [x_coordinates, y_coordinates, z_coordinates]


def combine_coordinates(coordinates):
    """Takes a list of coordinates and converts it into a different format

    Args:
        coordinates (List): Coordinates in the format [[x,x,...],[y,y,...],[z,z,...]] 

    Returns:
        List: Coordinates in the format [[x,y,z],[x,y,z],...]
    """
    return [[coord[0], coord[1], coord[2]] for coord in zip(coordinates[0], coordinates[1], coordinates[2])]


def xyz_to_vertices(coords):
    """Takes a list of ccords and converts it into vertices

    Args:
        coords (List): Coordinates in the format [[x,y,z],[x,y,z],...]

    Returns:
        _type_: Vertices in the format [[x,y,z,1.0],[x,y,z,1.0],...]
    """
    return [coord + [1.0] for coord in coords]


def remove_entity_children(entity: Entity):
    """Remove all children of one entity.

    Args:
        entity (Entity): The entity to remove all children from.
    """
    while entity.getChild(1) is not None:
        entity.remove(entity.getChild(1))
