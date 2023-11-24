#### PLANE FITTING ####

import numpy as np
from skspatial.objects import Plane, Points, Vector
import imgui

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh

from Elements.pyGLV.GL.Shader import Shader, ShaderGLDecorator
from Elements.pyGLV.GL.VertexArray import VertexArray

from OpenGL.GL import GL_LINES, GL_POINTS, glPointSize


input_fitting_nodes = [[0, 0, 0], [1, 0, 0.5], [-1, 0.5, 1], [0.5, 0.5, 0.5], [-1, 1, 0.5], [1, 0.5, -1]]


class PlaneFitting:
    def __init__(self, planefitting_entity, scene, root_entity, all_shaders, init_update) -> None:
        """Wrapper class for providing gui, rendering and logic for fitting a plane in 3D space

        Args:
            planefitting_entity (pyECSS.Entity): Entity to embed the planefitting into the Scene
            scene (pyGLV.GL.Scene): Reference to the scene object
            root_entity (pyECSS.Entity): Reference to the root entity
            all_shaders (List): Wrapper for all shaders
            init_update (Function): Reference to init_update function
        """

        self.planefitting_entity = planefitting_entity
        self.scene = scene
        self.rootEntity = root_entity
        self.all_shaders = all_shaders
        self.initUpdate = init_update

    def render_gui_and_plane(self):
        """Function to display gui and trigger the fitting of the plane
        """
        global input_fitting_nodes

        imgui.begin("Fit Plane")

        imgui.text("Fitting nodes X, Y, Z")
        for i, control_node in enumerate(input_fitting_nodes):
            changed, input_fitting_nodes[i] = imgui.input_float3(f"Node {i + 1}", *control_node)

        button_remove_node_pressed = imgui.button("Remove Node")
        imgui.same_line()
        button_add_node_pressed = imgui.button("Add Node")
        if button_remove_node_pressed:
            input_fitting_nodes.pop()
        if button_add_node_pressed:
            input_fitting_nodes.append([0.0, 0.0, 0.0])

        button_planefitting_pressed = imgui.button("Fit Plane")

        if button_planefitting_pressed:
            input_fitting_nodes = [list(tuple) for tuple in input_fitting_nodes]
            self.fit_plane(input_fitting_nodes)

        imgui.end()

    def fit_plane(self, fitting_nodes):
        """Function for computing the plane according to fitting nodes and render plane into the scene

        Args:
            fitting_nodes (List): fitting nodes for the plane from user input
        """

        #remove old plane before rendering new one
        remove_entity_children(self.planefitting_entity)

        plane = Plane.best_fit(Points(fitting_nodes))

        planefitting_vertices, planefitting_colors, planefitting_indices = generate_planefitting_data(plane, fitting_nodes)

        # ADD / UPDATE planefitting ##

        planefitting_trans = self.scene.world.addComponent(self.planefitting_entity,
                                                     BasicTransform(name="planefitting_trans", trs=util.identity()))
        planefitting_mesh = self.scene.world.addComponent(self.planefitting_entity, RenderMesh(name="planefitting_mesh"))
        planefitting_mesh.vertex_attributes.append(planefitting_vertices)
        planefitting_mesh.vertex_attributes.append(planefitting_colors)
        planefitting_mesh.vertex_index.append(planefitting_indices)
        planefitting_vArray = self.scene.world.addComponent(self.planefitting_entity,
                                                      VertexArray()) 

        planefitting_shader = self.scene.world.addComponent(self.planefitting_entity, ShaderGLDecorator(
            Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        self.all_shaders.append(planefitting_shader)


        ## VISUALIZE planefitting FITTING NODES AND PROJECTION LINES ##

        projection_lines_entity = self.scene.world.createEntity(Entity(name="projection_lines"))
        self.scene.world.addEntityChild(self.planefitting_entity, projection_lines_entity)

        projection_lines_vertices, projection_lines_colors, projection_lines_indices = generate_projection_lines(plane, fitting_nodes)

        projection_lines_trans = self.scene.world.addComponent(projection_lines_entity,
                                                     BasicTransform(name="projection_lines_trans", trs=util.identity()))
        projection_lines_mesh = self.scene.world.addComponent(projection_lines_entity, RenderMesh(name="projection_lines_mesh"))
        projection_lines_mesh.vertex_attributes.append(projection_lines_vertices)
        projection_lines_mesh.vertex_attributes.append(projection_lines_colors)
        projection_lines_mesh.vertex_index.append(projection_lines_indices)
        projection_lines_vArray = self.scene.world.addComponent(projection_lines_entity,
                                                      VertexArray(primitive=GL_LINES)) 

        projection_lines_shader = self.scene.world.addComponent(projection_lines_entity, ShaderGLDecorator(
            Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG))) 
        self.all_shaders.append(projection_lines_shader)



        fitting_nodes_vertices = xyz_to_vertices(fitting_nodes)
        fitting_nodes_colors = np.array([[0.5, 0.5, 1.0, 1.0]] * len(fitting_nodes_vertices), dtype=np.float32)
        fitting_nodes_indices = np.array(range(len(fitting_nodes_vertices)), np.uint32)

        fitting_nodes = self.scene.world.createEntity(Entity(name="fitting_nodes"))
        self.scene.world.addEntityChild(self.planefitting_entity, fitting_nodes)
        fitting_nodes_trans = self.scene.world.addComponent(fitting_nodes,
                                                            BasicTransform(name="fitting_nodes_trans",
                                                                           trs=util.identity()))
        fitting_nodes_mesh = self.scene.world.addComponent(fitting_nodes, RenderMesh(name="fitting_nodes_mesh"))
        fitting_nodes_mesh.vertex_attributes.append(fitting_nodes_vertices)
        fitting_nodes_mesh.vertex_attributes.append(fitting_nodes_colors)
        fitting_nodes_mesh.vertex_index.append(fitting_nodes_indices)
        glPointSize(5)
        fitting_nodes_vArray = self.scene.world.addComponent(fitting_nodes, VertexArray(primitive=GL_POINTS))

        fitting_nodes_shader = self.scene.world.addComponent(fitting_nodes, ShaderGLDecorator(
            Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        self.all_shaders.append(fitting_nodes_shader)

        self.scene.world.traverse_visit(self.initUpdate, self.scene.world.root)

def generate_projection_lines(plane,fitting_nodes):
    """Generate vertices, colors and indices for the projection lines from the fitting nodes to the plane

    Args:
        plane (skspatial.objects.Plane): Scikit Plane
        fitting_nodes (List): List of nodes to generate projection lines for

    Returns:
        List: Vertices (list), colors (list) and indices (list) for the projection lines
    """
    lines_vertices = []
    for node in fitting_nodes:
        lines_vertices.append(node)
        lines_vertices.append(plane.project_point(node))

    lines_indices = range(len(lines_vertices))
    lines_color = np.array([[1.0, 1.0, 1.0, 1.0]] * len(lines_vertices), dtype=np.float32)

    print(lines_vertices)

    return lines_vertices, lines_color, lines_indices


def generate_planefitting_data(plane,fitting_nodes):
    """Generate vertices, colors and indices for the plane

    Args:
        plane (skspatial.objects.Plane): Scikit Plane
        fitting_nodes (List): List of fitting nodes

    Returns:
        List: Vertices (list), colors (list) and indices (list) for the fitted plane
    """

    min_x, max_x, min_y, max_y, min_z, max_z = find_boundaries(fitting_nodes)

    diameter = max(max_x-min_x, max_y-min_y, max_z-min_z)

    global_x = Vector([1.,0.,0.])
    global_y = Vector([0.,1,0.])
    plane_x = Vector([0.,0.,0.])
    plane_y = Vector([0.,0.,0.])
    normal = plane.normal
    #if point is not equal to the x axis, use the x axis to get a vector along the plane.
    if(global_x.dot(normal) < 1.-10e-6):
        plane_x = global_x.cross(normal)
        plane_y = plane_x.cross(normal)
    else:
        plane_x = global_y.cross(normal)
        plane_y = plane_x.cross(normal)

    point = plane.point

    bottom_left = point - diameter * plane_x - diameter * plane_y
    top_left    = point - diameter * plane_x + diameter * plane_y
    bottom_right = point + diameter * plane_x - diameter * plane_y
    top_right = point + diameter * plane_x + diameter * plane_y
    
    planefitting_vertices =  [bottom_left,top_left,bottom_right,top_right]
    planefitting_indices = [0,1,3,0,3,2]
    planefitting_colors = np.array([[0.5, 0.0, 1.0, 1.0]] * len(planefitting_vertices), dtype=np.float32)

    return planefitting_vertices, planefitting_colors, planefitting_indices



def find_boundaries(coordinates):
    """Find min and max x, y and z values from a list of coordinates

    Args:
        coordinates (List): List of coordinates in format [[x,y,z],[x,y,z],...]

    Returns:
        List: min x, max x, min y, max y, min z, max z
    """
    # Initialize min and max values with the first element
    min_x = max_x = coordinates[0][0]
    min_y = max_y = coordinates[0][1]
    min_z = max_z = coordinates[0][2]

    # Iterate over the remaining elements and update min and max values
    for sublist in coordinates[1:]:
        min_x = min(min_x, sublist[0])
        max_x = max(max_x, sublist[0])
        min_y = min(min_y, sublist[1])
        max_y = max(max_y, sublist[1])
        min_z = min(min_z, sublist[2])
        max_z = max(max_z, sublist[2])
    
    return min_x, max_x, min_y, max_y, min_z, max_z


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
