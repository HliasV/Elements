import numpy as np

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene

from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from OpenGL.GL import GL_LINES

import OpenGL.GL as gl
import imgui

plot_boundaries = 1, -1, 1, -1 #max X, min X, max Y, min Y
f_x = 'x**2+x*4'
f_x_y = 'x**2+y**2'
func_detail = 30

class FunctionPlotting:
    def __init__(self, function2d_entity, function3d_entity, scene, root_entity, shader_2d, shader_3d,  init_update) -> None:
        """Wrapper class for providing gui, rendering and logic for plotting 2D and 3D functions

        Args:
            function2d_entity (pyECSS.Entity): Entity to embed 2D plot into the scene
            function3d_entity (pyECSS.Entity): Entity to embed 3D plot into the scene
            scene (pyGLV.GL.Scene): Reference to the scene object
            root_entity (pyECSS.Entity): Reference to the root entity
            shader_2d (List): Wrapper for all classic shaders
            shader_3d (List): Wrapper for all phong shaders
            init_update (Function): Reference to init_update function
        """

        self.function2d_entity = function2d_entity
        self.function3d_entity = function3d_entity
        self.scene = scene
        self.rootEntity = root_entity
        self.shader_2d = shader_2d
        self.shader_3d = shader_3d
        self.initUpdate = init_update

    def render_gui_and_plots(self):
        """Function to display gui and trigger the plotting and rendering of the 2D and 3D function.
        """
        global plot_boundaries
        global f_x_y
        global f_x
        global func_detail

        imgui.begin("Plot 2D and 3D Function")

        changed, f_x = imgui.input_text('2D Function F(x)', f_x, 256)

        button_print_2D_pressed = imgui.button("Print f(x)")

        changed, f_x_y = imgui.input_text('3D Function F(x,y)', f_x_y, 256)

        button_print_3D_pressed = imgui.button("Print f(x,y)")

        imgui.text("Give plot range: max X, min X, max Y, min Y")
        changed, plot_boundaries = imgui.input_float4('', *plot_boundaries)
        # imgui.same_line()
        imgui.text("max X: %.1f, min X: %.1f, max Y: %.1f, min Y: %.1f" % (plot_boundaries[0], plot_boundaries[1], plot_boundaries[2], plot_boundaries[3]))
        changed, func_detail = imgui.input_int('Detailed', func_detail)
        if imgui.is_item_hovered():
            imgui.set_tooltip("Make sure the detail is between 4 to 100")


        if (func_detail > 100):
            func_detail = 100
        elif (func_detail < 4):
            func_detail = 4
        if button_print_2D_pressed:
            self.render_2d_plot(plot_boundaries, func_detail, f_x)
        if button_print_3D_pressed:
            self.render_3d_plot(plot_boundaries, func_detail, f_x_y)
        imgui.end()

    def render_2d_plot(self, plot_boundaries, func_detail, f_x):
        """Function for triggering computing 2D plot data and render the plot into the scene

        Args:
            plot_boundaries (List): max X, min X, max Y, min Y boundaries for the function plotting from user input
            func_detail (Integer): Number of points to plot on the function from user input
            f_x (String): F(x) function as string representation from user input
        """
        plotting2d_vertices, plotting2d_colors, plotting2d_indices = generate_plot2d_data(plot_boundaries, func_detail, f_x)

        ## ADD / UPDATE PLOT 2D ##

        remove_entity_children(self.function2d_entity)

        plotting2d_trans = self.scene.world.addComponent(self.function2d_entity,
                                                     BasicTransform(name="plotting2d_trans", trs=util.identity()))
        plotting2d_mesh = self.scene.world.addComponent(self.function2d_entity, RenderMesh(name="plotting2d_mesh"))
        plotting2d_mesh.vertex_attributes.append(plotting2d_vertices)
        plotting2d_mesh.vertex_attributes.append(plotting2d_colors)
        plotting2d_mesh.vertex_index.append(plotting2d_indices)
        plotting2d_vArray = self.scene.world.addComponent(self.function2d_entity,
                                                      VertexArray(primitive=GL_LINES))  # note the primitive change

        plotting2d_shader = self.scene.world.addComponent(self.function2d_entity, ShaderGLDecorator(
            Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
        self.shader_2d.append(plotting2d_shader)

        self.scene.world.traverse_visit(self.initUpdate, self.scene.world.root)

    def render_3d_plot(self, plot_boundaries, func_detail, f_x_y):
        """Function for triggering computing 3D plot data and render the plot into the scene

        Args:
            plot_boundaries (List): max X, min X, max Y, min Y boundaries for the function plotting from user input
            func_detail (Integer): Number of points to plot on the function from user input
            f_x_y (String): F(x, y) function as string representation from user input
        """
        
        plotting3d_vertices, plotting3d_colors, plotting3d_indices, plotting3d_normals = generate_plot3d_data(plot_boundaries, func_detail, f_x_y)

        ## ADD / UPDATE PLOT 3D ##

        remove_entity_children(self.function3d_entity)

        plotting3d_trans = self.scene.world.addComponent(self.function3d_entity,
                                                     BasicTransform(name="plotting3d_trans", trs=util.identity()))
        plotting3d_mesh = self.scene.world.addComponent(self.function3d_entity, RenderMesh(name="plotting3d_mesh"))
        plotting3d_mesh.vertex_attributes.append(plotting3d_vertices)
        plotting3d_mesh.vertex_attributes.append(plotting3d_colors)
        plotting3d_mesh.vertex_attributes.append(plotting3d_normals)
        plotting3d_mesh.vertex_index.append(plotting3d_indices)
        plotting3d_vArray = self.scene.world.addComponent(self.function3d_entity,
                                                      VertexArray())

        plotting3d_shader = self.scene.world.addComponent(self.function3d_entity, ShaderGLDecorator(
            Shader(vertex_source=Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))
        self.shader_3d.append(plotting3d_shader)

        self.scene.world.traverse_visit(self.initUpdate, self.scene.world.root)

def generate_plot2d_data(plot_boundaries, func_detail, f_x):
    """Compute x, y value pairs for the given function and generate vertices, colors and indices accordingly.

    Args:
        plot_boundaries (List): max X, min X, max Y, min Y boundaries for the function plotting from user input
        func_detail (Integer): Number of points to plot on the function from user input
        f_x (String): F(x) function as string representation from gui input from user input

    Returns:
        List: Vertices (list), colors (list) and indices (list) for the plotted function.
    """
    x = np.linspace(plot_boundaries[0], plot_boundaries[1], func_detail)
    y = eval_f_x(f_x, x)
    
    plotting_vertices = np.empty((0, 4), np.float32)
    for i in range(0, len(x)-2):
        point1 = [x[i], y[i], 0.0, 1.0]
        point2 = [x[i+1], y[i+1], 0.0, 1.0]
        plotting_vertices = np.append(plotting_vertices, [point1, point2], axis=0)

    plotting_colors = np.array([[0.5, 0.0, 1.0, 1.0]] * len(plotting_vertices), dtype=np.float32)

    plotting_indices = np.array(range(len(plotting_vertices)), np.uint32)

    return plotting_vertices, plotting_colors, plotting_indices

def generate_plot3d_data(plot_boundaries, func_detail, f_x_y):
    """Compute x, y, z values for the given function and generate vertices, colors, indices and normals accordingly.

    Args:
        plot_boundaries (List): max X, min X, max Y, min Y boundaries for the function plotting from user input
        func_detail (Integer): Number of points to plot on the function from user input
        f_x_y (String): F(x, y) function as string representation from user input

    Returns:
        List: Vertices (list), colors (list), indices (list) and normals (list) for the plotted function.
    """
    x = np.linspace(plot_boundaries[0], plot_boundaries[1], func_detail)
    z = np.linspace(plot_boundaries[2], plot_boundaries[3], func_detail)

    triangles_vertices = np.empty((0, 4), np.float32)

    q = 0
    while (q < len(z) - 1):
        q += 1
        l = 0
        while (l < len(x) - 1):
            l += 1
            # first triangle
            point1 = x[l - 1], eval_f_x_y(f_x_y, x[l - 1], z[q - 1]), z[q - 1], 1
            point2 = x[l], eval_f_x_y(f_x_y, x[l], z[q - 1]), z[q - 1], 1
            point3 = x[l], eval_f_x_y(f_x_y, x[l], z[q]), z[q], 1

            triangles_vertices = np.append(triangles_vertices, [point1, point2, point3], axis=0)

            # second triangle
            point1 = x[l - 1], eval_f_x_y(f_x_y, x[l - 1], z[q - 1]), z[q - 1], 1
            point2 = x[l], eval_f_x_y(f_x_y, x[l], z[q]), z[q], 1
            point3 = x[l - 1], eval_f_x_y(f_x_y, x[l - 1], z[q]), z[q], 1

            triangles_vertices = np.append(triangles_vertices, [point1, point2, point3], axis=0)

    triangles_colors = np.array([[0.0, 1.0, 1.0, 1.0]] * len(triangles_vertices), dtype=np.float32)
    triangles_indices = np.array(range(len(triangles_vertices)), np.uint32)

    triangles_normals = []
    #create array of normals with size of vertices
    sumNormals = np.array([(0.,0.,0.)] * len(triangles_vertices))
    sumCounter = np.array([(0)] * len(triangles_vertices))
    for i in range(0, len(triangles_indices), 3):
        #calculate normal for each triangle
        normal = np.cross(np.subtract(triangles_vertices[triangles_indices[i+1]], triangles_vertices[triangles_indices[i]])[:-1], np.subtract(triangles_vertices[triangles_indices[i+2]], triangles_vertices[triangles_indices[i]])[:-1])
        #normalize normal
        normal = normal / np.linalg.norm(normal)
        #add normal to each vertex of the triangle
        sumNormals[triangles_indices[i]] += normal
        sumNormals[triangles_indices[i + 1]] += normal
        sumNormals[triangles_indices[i + 2]] += normal
        #increase counter for each vertex of the triangle
        sumCounter[triangles_indices[i]] += 1
        sumCounter[triangles_indices[i + 1]] += 1
        sumCounter[triangles_indices[i + 2]] += 1
    #iterrate through all triangles and set normals to average normal
    for i in range(len(sumNormals)):
        new_normal = sumNormals[i]/sumCounter[i]
        new_normal = new_normal / np.linalg.norm(new_normal)
        triangles_normals.append(new_normal)

    return triangles_vertices, triangles_colors, triangles_indices, triangles_normals


def summ(x, y):

    result = x + y

    return result



randosummenergebnis = summ(3, 5)

def remove_entity_children(entity: Entity):
    """Remove all children of one entity.

    Args:
        entity (Entity): The entity to remove all children from.
    """
    while entity.getChild(1) is not None:
        entity.remove(entity.getChild(1))

def eval_f_x_y(function, x,y):
    """Helper function to compute result for a function in string representation for given x, y values.

    Args:
        function (String): Function in string representation
        x (Float): x value
        y (Float): y value

    Returns:
        Float: Result of the function for given x and y
    """
    d= {}
    d['x'] = x
    d['y'] = y
    d['sin'] = np.sin
    d['cos'] = np.cos
    d['tan'] = np.tan
    d['pi'] = np.pi
    d['e'] = np.e
    z = eval(function,d)
    return z

def eval_f_x(function, x):
    """Helper function to compute result for a function in string representation for given x values.

    Args:
        function (String): Function in string representation
        x (Float): x value

    Returns:
        Float: Result of the function for given x
    """
    d= {}
    d['x'] = x
    d['sin'] = np.sin
    d['cos'] = np.cos
    d['tan'] = np.tan
    d['pi'] = np.pi
    d['e'] = np.e
    y = eval(function,d)
    return y