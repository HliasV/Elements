"""
Component classes, part of the Elements.pyECSS package
    
Elements.pyECSS (Entity Component Systems in a Scenegraph) package
@Copyright 2021-2022 Dr. George Papagiannakis
    
The Compoment related classes are containers dedicated to a specific type of data in Elements.pyECSS,
based on the Composite design pattern

Based on the Composite and Iterator design patterns

* https://refactoring.guru/design-patterns/composite
* https://github.com/faif/python-patterns/blob/master/patterns/structural/composite.py
* https://refactoring.guru/design-patterns/iterator
* https://github.com/faif/python-patterns/blob/master/patterns/behavioral/iterator.py

"""

from __future__         import annotations
from abc                import ABC, abstractmethod
from math import atan2
from typing             import List
from collections.abc    import Iterable, Iterator

import Elements.pyECSS.GA.quaternion as quat
import Elements.pyECSS.System
import uuid  
import Elements.pyECSS.utilities as util
import numpy as np


class Component(ABC, Iterable):
    """
    The Interface Component class of our ECSS.
    
    Based on the Composite pattern, it is a data collection of specific
    class of data. 
    Concrete Subclass Components typically are e.g. BasicTransform, RenderMesh, Shader, RigidBody etc.
    """
    
    def __init__(self, name=None, type=None, id=None):
        """
        Initializes a Component object with optional name, type, and id parameters.

        Args:
        - name (str, optional): The name of the component. Defaults to None.
        - type (str, optional): The type of the component. Defaults to None.
        - id (str, optional): The ID of the component. Defaults to None.

        If name is None, then the component's name is set to the name of its class. If type is None, the type is set to the name of the class.
        If id is None, a unique ID is generated using the uuid.uuid1() method.

        The _parent, _children, _worldManager, and _eventManager attributes are set to None by default.

        Returns:
        - None
        """
        
        if (name is None):
            self._name = self.getClassName()
        else:
            self._name = name
        
        if (type is None):
            self._type = self.getClassName()
        else:
            self._type = type
        
        if id is None:
            self._id = uuid.uuid1().int #assign unique ID on Component
        else:
            self._id = id
        
        self._parent = self
        self._children = None
        self._worldManager = None
        self._eventManager = None
    
    #define properties for id, name, type, parent
    @property #name
    def name(self) -> str:
        """Get the name of the component."""
        return self._name
    @name.setter
    def name(self, value):
        """Set the name of the component."""
        self._name = value
        
    @property #type
    def type(self) -> str:
        """Get the type of the component."""
        return self._type
    @type.setter
    def type(self, value):
        """Set the type of the component."""
        self._type = value
        
    @property #id
    def id(self) -> int:
        """Get the ID of the component."""
        return self._id
    @id.setter
    def id(self, value):
        """Set the ID of the component."""
        self._id = value
        
    @property #parent
    def parent(self) -> Component:
        """Get the parent of the component."""
        return self._parent
    @parent.setter
    def parent(self, value):
        """Set the parent of the component."""
        self._parent = value
        
    @property #ECSSManager
    def worldManager(self):
        """ Get Component's ECSSManager """
        return self._worldManager
    @worldManager.setter
    def worldManager(self, value):
        """ Set Component's ECSSManager """
        self._worldManager = value
    
    @property #EventManager
    def eventManager(self):
        """Get the ECSSManager of the component."""
        return self._eventManager
    @eventManager.setter
    def eventManager(self, value):
        """Set the ECSSManager of the component."""
        self._eventManager = value
    
    def add(self, object: Component) ->None:
        """
        Add a Component object to the children of this Component.

        Args:
        - object (Component): The Component to add as a child.

        Returns:
        - None
        """
        pass

    def remove(self, object: Component) ->None:
        """
        Removes a Component object to the children of this Component.

        Args:
        - object (Component): The Component to remove as a child.

        Returns:
        - None
        """
        pass
        
    def getChild(self, index) ->Component:
        """
        Get the child Component object at the given index.

        Args:
        - index (int): The index of the child Component to retrieve.

        Returns:
        - Component: The child Component object at the given index.
        """
        return None
    
    def getNumberOfChildren(self) -> int:
        """
        Get the number of child Component objects for this Component.

        Returns:
        - int: The number of child Component objects for this Component.
        """
        return len(self._children)
    
    @classmethod
    def getClassName(cls):
        """
        Get the name of this Component class.

        Returns:
        - str: The name of this Component class.
        """
        return cls.__name__
    
    @abstractmethod
    def init(self):
        """
        abstract method to be subclassed for extra initialisation
        """
        raise NotImplementedError
    
    @abstractmethod
    def update(self, **kwargs):
        """
        method to be subclassed for debuging purposes only, 
        in case we need some behavioral or logic computation within the Component. 
        This violates the ECS architecture and should be avoided.
        """
        raise NotImplementedError
    
    @abstractmethod
    def accept(self, system: Elements.pyECSS.System, event = None):
        """
        Accepts a class object to operate on the Component, based on the Visitor pattern.

        :param system: [a System object]
        :type system: [System]
        """
        raise NotImplementedError
                
    def print(self):
        """
        prints out name, type, id, parent of this Component
        """
        print(f"\n {self.getClassName()} name: {self._name}, type: {self._type}, id: {self._id}, parent: {self._parent._name}")
        print(f" ______________________________________________________________")
    
    def __iter__(self):
        """ Iterable method
        makes this abstract Component an iterable. It is meant to be overidden by subclasses.
        """
        return self 
    
    def __str__(self):
        """
        Returns a string representation of this Component.

        Returns:
        - str: A string representation of this Component.
        """
        return f"\n {self.getClassName()} name: {self._name}, type: {self._type}, id: {self._id}, parent: {self._parent._name}"


class ComponentDecorator(Component):
    """Basic Component Decorator, based on the Decorator design pattern

    :param Component: [description]
    :type Component: [type]
    :return: [description]
    :rtype: [type]
    """
    
    def __init__(self, comp, name=None, type=None, id=None):
        super().__init__(name, type, id)
        self._component = comp
    
    @property
    def component(self):
        return self._component
    
    def init(self):
        self._component.init()
    
    def update(self, **kwargs):
        self._component.update(**kwargs)
    
    #def accept(self, system: Elements.pyECSS.System):
       # we want the decorator first to accept the visitor and only if needed the wrappe to accept it too
       # each component decorator has to override this method
        
    
    

class ComponentIterator(ABC):
    """Abstract component Iterator class

    :param ABC: [description]
    :type ABC: [type]
    :return: [description]
    :rtype: [type]
    """
    pass

class CompNullIterator(Iterator, ComponentIterator):
    """
    The Default Null iterator for a Concrete Component class

    :param Iterator: [description]
    :type Iterator: [type]
    """
    def __init__(self, comp: Component):
        self._comp = comp
    
    def __next__(self):
        return None
    

class BasicTransform(Component):
    """
    An example of a concrete Component Transform class
    
    Contains a basic Euclidean Translation, Rotation and Scale Homogeneous matrices
    all-in-one TRS 4x4 matrix
    
    :param Component: [description]
    :type Component: [type]
    """
   
    def __init__(self, name=None, type=None, id=None, trs=None):
        
        super().__init__(name, type, id)
        
        if (trs is None):
            self._trs = util.identity()
        else:
            self._trs = trs
            
        self._l2world = util.identity()
        self._l2cam = util.identity()
        self._parent = self
        self._children = []
         
    @property #trs
    def trs(self):
        """ Get Component's transform: translation, rotation ,scale """
        return self._trs
    @trs.setter
    def trs(self, value):
        self._trs = value

    @property #l2world
    def l2world(self):
        """ Get Component's local to world transform: translation, rotation ,scale """
        return self._l2world
    @l2world.setter
    def l2world(self, value):
        self._l2world = value
        
    @property #l2cam
    def l2cam(self):
        """ Get Component's local to camera transform: translation, rotation ,scale, projection """
        return self._l2cam
    @l2cam.setter
    def l2cam(self, value):
        self._l2cam = value                 

    @property #translation vector
    def translation(self):
        return self.trs[:3,3];
    @property #rotation vector
    def rotationEulerAngles(self):
        # First get rotation matrix from trs. Divide by scale
        rotationMatrix = self.trs.copy();
        rotationMatrix[:][0] /= self.scale[0];
        rotationMatrix[:][1] /= self.scale[1];
        rotationMatrix[:][2] /= self.scale[2];
        # Now, extract euler angles from rotation matrix
        x = atan2(rotationMatrix[1][2], rotationMatrix[2][2]);
        y = 0;
        z = 0;
        return [x, y, z];
    @property #scale vector
    def scale(self):
        x = self.trs[0, 0];
        y = self.trs[1, 1];
        z = self.trs[2, 2];
        return [x, y, z];

    def update(self, **kwargs):
        """ Local 2 world transformation calculation
        Traverses upwards whole scenegraph and multiply all transformations along this path
        
        Arguments could be "l2world=" or "trs=" or "l2cam=" to set respective matrices 
        """
        # global verbose
        # if verbose: print(self.getClassName(), ": update() called")
        arg1 = "l2world"
        arg2 = "trs"
        arg3 = "l2cam"
        if arg1 in kwargs:
            # if verbose: print("Setting: ", arg1," with: \n", kwargs[arg1])
            self._l2world = kwargs[arg1]
        if arg2 in kwargs:
            # if verbose: print("Setting: ", arg2," with: \n", kwargs[arg2])
            self._trs = kwargs[arg2]
        if arg3 in kwargs:
            # if verbose: print("Setting: ", arg3," with: \n", kwargs[arg3])
            self._l2cam = kwargs[arg3]
        
    def accept(self, system: Elements.pyECSS.System, event = None):
        """
        Accepts a class object to operate on the Component, based on the Visitor pattern.

        :param system: [a System object]
        :type system: [System]
        """
        
        system.apply2GATransform(self) # from GATransform
        system.apply2BasicTransform(self) #from TransformSystem
        system.applyCamera2BasicTransform(self) #from CameraSystem
        
        """
        if (isinstance(system, System.TransformSystem)):
            system.apply(self)
        
        if (isinstance(system, System.CameraSystem)):
            system.applyCamera(self)
        """
    
    def init(self):
        """
        abstract method to be subclassed for extra initialisation
        """
        pass

    def __str__(self):
        np.set_printoptions(formatter={'float': lambda x: "{0:0.3f}".format(x)}) # print only one 3 decimals
        return f"\n {self.getClassName()} name: {self._name}, type: {self._type}, id: {self._id}, parent: {self._parent._name}, \nl2world: \n{self.l2world}, \nl2cam: \n{self.l2cam}, \ntrs: \n{self.trs}"
    
    def __iter__(self) ->CompNullIterator:
        """ A concrete component does not have children to iterate, thus a NULL iterator
        """
        return CompNullIterator(self) 
class Camera(Component):
    """
    An example of a concrete Component Camera class
    
    Contains a basic Projection matrices (otrhographic or perspective)
    
    :param Component: [description]
    :type Component: [type]
    """
   
    def __init__(self, projMatrix=None, name=None, type=None, id=None, left=-100.0, right=100.0, bottom=-100.0, top=100.0, near=1.0, far=100.0):
        super().__init__(name, type, id)
        
        if projMatrix is not None:
            self._projMat = projMatrix
        else:
            self._projMat = util.ortho(left, right, bottom, top, near, far)
        self._root2cam = util.identity()
        self._parent = self
         
    @property #projMat
    def projMat(self):
        """ Get Component's camera Projection matrix """
        return self._projMat
    @projMat.setter
    def projMat(self, value):
        self._projMat = value
    
    @property #_root2cam
    def root2cam(self):
        """ Get Component's root to camera matrix """
        return self._root2cam
    @root2cam.setter
    def orthoroot2camMat(self, value):
        self._root2cam = value                   
    
    def update(self, **kwargs):
        """ Update Camera matrices
        
        Arguments could be "root2cam=" to set respective matrices 
        """
        arg1 = "root2cam"
        if arg1 in kwargs:
            self._root2cam = kwargs[arg1]  
       
    def accept(self, system: Elements.pyECSS.System, event = None):
        """
        Accepts a class object to operate on the Component, based on the Visitor pattern.

        :param system: [a System object]
        :type system: [System]
        """
        
        # In Python due to ducktyping, either call a System concrete method
        # or leave it generic as is and check within System apply() if the 
        #correct node is visited (there is no automatic inference which System to call 
        # due to its type. We need to call a System specific concrete method otherwise)
        system.apply2Camera(self)
    
    def init(self):
        """
        abstract method to be subclassed for extra initialisation
        """
        pass
    
    def __str__(self):
        return f"\n {self.getClassName()} name: {self._name}, type: {self._type}, id: {self._id}, parent: {self._parent._name}, \n projMat: \n{self.projMat},\n root2cam: \n{self.root2cam}"    

    def __iter__(self) ->CompNullIterator:
        """ A component does not have children to iterate, thus a NULL iterator
        """
        return CompNullIterator(self) 

class RenderMesh(Component):
    """
    A concrete RenderMesh class

    Accepts a dedicated RenderSystem to initiate rendering of the RenderMesh, using its vertex attributes (property)
    """
    def __init__(self, name=None, type=None, id=None, vertex_attributes=None, vertex_index=None):
        """ Initialize the generic RenderMesh component with the vertex attribute arrays
        this is the generic place to store all vertex attributes (vertices, colors, normals, bone weights etc.)
        specifically for OpenGL buffers, these will be passed to a VertexArray by a RenderGLShaderSystem
        then other RenderSystems could use that vertex attribute information for their rendering, 
        e.g. a RenderRayTracingSystem for backwards rayTracing, a RenderPathTracingSystem for pathTracing etc. 

        """
        super().__init__(name, type, id)
        
        self._parent = self
        if not vertex_attributes:
            self._vertex_attributes = [] #list of vertex attribute lists 
        else:
            self._vertex_attributes = vertex_attributes
            
        if not vertex_index:
                self.vertex_index = [] #list of vertex attribute lists 
        else:
            self._vertex_index = vertex_index
    
    @property
    def vertex_attributes(self):
        return self._vertex_attributes
    
    @vertex_attributes.setter
    def vertex_attributes(self, value):
        self._vertex_attributes = value
    
    @property
    def vertex_index(self):
        return self._vertex_index
    
    @vertex_index.setter
    def vertex_index(self, value):
        self._vertex_index = value
        
    def update(self):
        pass
        # print(self.getClassName(), ": update() called")
   
   
    def accept(self, system: Elements.pyECSS.System, event = None):
        """
        Accepts a class object to operate on the Component, based on the Visitor pattern.

        :param system: [a System object]
        :type system: [System]
        """
        system.apply2RenderMesh(self)
    
    
    def init(self):
        """
        abstract method to be subclassed for extra initialisation
        """
        pass
    
    def print(self):
        """
        prints out name, type, id, parent of this Component
        """
        print(f"\n {self.getClassName()} name: {self._name}, type: {self._type}, id: {self._id}, parent: {self._parent._name}, vertex_attributes: \n{self._vertex_attributes}")
        print(f" ______________________________________________________________")
    
    
    def __str__(self):
        return f"\n {self.getClassName()} name: {self._name}, type: {self._type}, id: {self._id}, parent: {self._parent._name}, vertex_attributes: \n{self._vertex_attributes}"

    
    def __iter__(self) ->CompNullIterator:
        """ A component does not have children to iterate, thus a NULL iterator
        """
        return CompNullIterator(self) 
    
    
class BasicTransformDecorator(ComponentDecorator):
    """An example of a concrete Component Decorator that wraps the component (BasicTransform) 
        and adds extra layered functionality 

    :param ComponentDecorator: [description]
    :type ComponentDecorator: [type]
    """
    def init(self):
        """
        example of a decorator
        """
        self.component.init()
        #call any extra methods before or after
    
    def accept(self, system: Elements.pyECSS.System, event = None):
        pass # we want the decorator first to accept the visitor and only if needed the wrappe to accept it too


class Keyframe(Component):

    def __init__(self, name=None, type=None, id=None, array_MM=None):
        super().__init__(name, type, id)

        self._parent = self
        if not array_MM:
            self._array_MM = [] 
        else:
            self._array_MM = array_MM
    
    @property
    def array_MM(self):
        return self._array_MM
    
    @array_MM.setter
    def array_MM(self, value):
        self._array_MM = value 

    @property #translation vector
    def translate(self):
        tempMatrix = self.array_MM.copy();
        translateMatrix = [];
        for i in range(len(tempMatrix)):
            for j in range(len(tempMatrix[i])):
                translateMatrix.append(tempMatrix[i][j][:3,3])
        return translateMatrix

    @property #rotation vector
    def rotate(self):
        # First get rotation matrix from trs. Divide by scale
        tempMatrix = self.array_MM.copy();
        rotateMatrix = [];
        for i in range(len(tempMatrix)):
            for j in range(len(tempMatrix[i])):
                rotateMatrix.append(quat.Quaternion.from_rotation_matrix(tempMatrix[i][j]))
        return rotateMatrix


    def update(self):
        pass
   
    def accept(self, system: Elements.pyECSS.System, event = None):
        #system.apply2Keyframe(self)
        pass
    
    def init(self):
        pass
    
    def print(self):
        """
        prints out name, type, id, parent of this Component
        """
        print(f"\n {self.getClassName()} name: {self._name}, type: {self._type}, id: {self._id}, parent: {self._parent._name}, array_MM: \n{self._array_MM}")
        print(f" ______________________________________________________________")
    
    def __str__(self):
        return f"\n {self.getClassName()} name: {self._name}, type: {self._type}, id: {self._id}, parent: {self._parent._name}, array_MM: \n{self._array_MM}"

    def __iter__(self) ->CompNullIterator:
        """ A component does not have children to iterate, thus a NULL iterator
        """
        return CompNullIterator(self) 
    

class AnimationComponents(Component):

    def __init__(self, name=None, type=None, id=None, bones=None, MM=None, alpha=0, tempo=2, time_add=0, animation_start = True, anim_keys = 2, time = [0, 100, 200], flag = True, inter = 'SLERP'):
        super().__init__(name, type, id)
        self._parent = self

        self.alpha = alpha
        self.tempo = tempo
        self.time_add = time_add
        self.anition_start = animation_start
        self.animKeys = anim_keys
        self.inter = inter
        self.time = time
        self.flag = flag

        self.MM = []

        if not bones:
            self._bones = [] 
        else:
            self._bones = bones

    @property
    def bones(self):
        return self._bones
    
    @bones.setter
    def bones(self, value):
        self._bones = value 

    #Animation loop
    def animation_loop(self, key1, key2, key3=None):
        #Filling MM1 with 4x4 identity matrices
        self.MM = [np.eye(4) for _ in key1]

        if (self.time_add >= self.time[1] and key3 is None) or (self.time_add >= self.time[2]):
            self.flag = False
        elif self.time_add <= self.time[0]:
            self.flag = True


        if self.time_add >= self.time[0] and self.time_add <= self.time[1]:
            self.animation_for_loop(key1,key2, self.time[0], self.time[1])
        elif self.time_add > self.time[1] and self.time_add <= self.time[2] and key3 is not None:
            self.animation_for_loop(key2,key3, self.time[1], self.time[2])
        
        
        #So we can have repeating animation
        if self.flag == True:
            if self.anition_start == True:
                self.time_add += self.tempo
            else:
                self.time_add = self.time_add
        else:
            if self.anition_start == True:
                self.time_add -= self.tempo
            else:
                self.time_add = self.time_add

        # Flattening MM1 array to pass as uniform variable
        MM1Data =  np.array(self.MM, dtype=np.float32).reshape((len(self.MM), 16))

        return MM1Data
    
    def animation_for_loop(self, k_1, k_2, t0, t1):
        self.alpha = (self.time_add - t0) / abs(t1 - t0)

        keyframe1 = Keyframe(array_MM=[k_1])
        keyframe2 = Keyframe(array_MM=[k_2])

        for i in range(len(k_1)):
            if(self.inter == "LERP"):
                self.MM[i][:3, :3] = quat.Quaternion.to_rotation_matrix(quat.quaternion_lerp(keyframe1.rotate[i], keyframe2.rotate[i], self.alpha))
                self.MM[i][:3, 3] = self.lerp(keyframe1.translate[i], keyframe2.translate[i], self.alpha)
            else:
                #SLERP
                self.MM[i][:3, :3] = quat.Quaternion.to_rotation_matrix(quat.quaternion_slerp(keyframe1.rotate[i], keyframe2.rotate[i], self.alpha))
                #LERP
                self.MM[i][:3, 3] = self.lerp(keyframe1.translate[i], keyframe2.translate[i], self.alpha)

    def lerp(self,a, b, t):
        return (1 - t) * a + t * b
     
    def update(self):
        pass
   
    def accept(self, system: Elements.pyECSS.System, event = None):
        pass
    
    def init(self):
        pass