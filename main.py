import pygame as pg
import numpy as np
import time

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import config

class GlobalVariables:
    CURRENT_ANGLE = 0
    CURRENT_ZOOM = 0

    CALC_SPEED_PER_FRAME = 0

class Renderer:
    def clearError(self):
        while glGetError() != GL_NO_ERROR:
            pass

    def checkError(self):
        while (error := glGetError()) != GL_NO_ERROR:
            print(f"OpenGL Error: {error}")

    def openGLCommands(self, command, *args):
        self.clearError()
        result = command(*args)
        self.checkError()
        return result

    def parseShader(self, path):
        with open(path, "r") as file:
            data = file.read()

        vertexShader = ""
        fragmentShader = ""

        reading = 0
        for line in data.split("\n"):
            if "#shader vertex" in line:
                reading = 1
            elif "#shader fragment" in line:
                reading = 2
            else:
                if reading == 1:
                    vertexShader += line + "\n"
                elif reading == 2:
                    fragmentShader += line + "\n"

        return vertexShader, fragmentShader

    def compileShader(self, shaderType, source):
        shader_id = self.openGLCommands(glCreateShader, shaderType) 

        self.openGLCommands(glShaderSource, shader_id, source)

        self.openGLCommands(glCompileShader, shader_id)

        if glGetShaderiv(shader_id, GL_COMPILE_STATUS) != GL_TRUE:
            raise Exception("Shader compilation failed: %s" % glGetShaderInfoLog(shader_id))
        
        return shader_id
    
    def createShader(self, path, useVertex=False):
        vertexShader, fragmentShader = self.parseShader(path)

        program = self.openGLCommands(glCreateProgram)
        
        vertexShader = self.compileShader(GL_VERTEX_SHADER, vertexShader)
        fragmentShader = self.compileShader(GL_FRAGMENT_SHADER, fragmentShader)

        if useVertex:
            self.openGLCommands(glAttachShader, program, vertexShader)

        self.openGLCommands(glAttachShader, program, fragmentShader)

        self.openGLCommands(glLinkProgram, program)
        self.openGLCommands(glValidateProgram, program)

        self.openGLCommands(glDeleteShader, vertexShader)
        self.openGLCommands(glDeleteShader, fragmentShader)

        return program

class Drawer(Renderer):
    def __init__(self, vertices, indices, length, color=(1.0, 1.0, 1.0, 1.0)):
        self.vertices = vertices
        self.indices = indices
        self.length = length

        self.vertices = np.array(self.vertices, dtype=np.float32)
        self.indices = np.array(self.indices, dtype=np.uint32)

        self.buffer = self.openGLCommands(glGenBuffers, 1)
        self.indexBuffer = self.openGLCommands(glGenBuffers, 1)

        self.openGLCommands(glBindBuffer, GL_ARRAY_BUFFER, self.buffer)
        self.openGLCommands(glBindBuffer, GL_ELEMENT_ARRAY_BUFFER, self.indexBuffer)

        self.openGLCommands(glEnableVertexAttribArray, 0)
        self.openGLCommands(glVertexAttribPointer, 0, self.length, GL_FLOAT, False, self.vertices.itemsize * self.length, ctypes.c_void_p(0))

        self.shader = self.createShader("res/shaders/basic.shader")
        self.color = color
        self.colorUniformLoc = self.openGLCommands(glGetUniformLocation, self.shader, "objectColor")

    def lower_position(self):
        self.vertices[0] -= 0.01
        self.vertices[3] -= 0.01
        self.vertices[6] -= 0.01
        self.vertices[9] -= 0.01

    def raise_position(self):
        self.vertices[0] += 0.01
        self.vertices[3] += 0.01
        self.vertices[6] += 0.01
        self.vertices[9] += 0.01

    def draw(self):
        self.openGLCommands(glUseProgram, self.shader)
    
        self.openGLCommands(glBufferData, GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        self.openGLCommands(glBufferData, GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)
        
        self.openGLCommands(glUniform4f, self.colorUniformLoc, *self.color)

        self.openGLCommands(glDrawElements, GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)

class Sphere3d(Renderer):
    def __init__(self, radius, sectors, stacks, start_position=(0, 0, 0), velocity=(0, 0, 0), color=(1.0, 1.0, 1.0, 1.0)):
        self.radius = radius
        self.sectors = sectors
        self.stacks = stacks
        self.position = start_position

        self.vertices = []
        self.indices = []

        self.velocity = np.array(velocity, dtype=np.float32)

        self.create_sphere()

        self.drawer = Drawer(self.vertices, self.indices, 3, color=color)

    def create_sphere(self):
        for i in range(self.stacks + 1):
            stack_angle = np.pi / 2 - i * np.pi / self.stacks
            xy = self.radius * np.cos(stack_angle)
            z = self.radius * np.sin(stack_angle)

            for j in range(self.sectors + 1):
                sector_angle = j * 2 * np.pi / self.sectors
                x = xy * np.cos(sector_angle)
                y = xy * np.sin(sector_angle)

                self.vertices.append(x)
                self.vertices.append(y)
                self.vertices.append(z)

        for i in range(self.stacks):
            for j in range(self.sectors):
                self.indices.append(i * (self.sectors + 1) + j)
                self.indices.append((i + 1) * (self.sectors + 1) + j)
                self.indices.append((i + 1) * (self.sectors + 1) + j + 1)

                self.indices.append(i * (self.sectors + 1) + j)
                self.indices.append((i + 1) * (self.sectors + 1) + j + 1)
                self.indices.append(i * (self.sectors + 1) + j + 1)

        for i in range(len(self.vertices)):
            if i % 3 == 0:
                self.vertices[i] += self.position[0]
            elif i % 3 == 1:
                self.vertices[i] += self.position[1]
            elif i % 3 == 2:
                self.vertices[i] += self.position[2]

    def moveIncrement(self, change_in_position):
        for i in range(len(self.drawer.vertices)):
            if i % 3 == 0:
                self.drawer.vertices[i] += change_in_position[0]
            elif i % 3 == 1:
                self.drawer.vertices[i] += change_in_position[1]
            elif i % 3 == 2:
                self.drawer.vertices[i] += change_in_position[2]

        self.position = (self.position[0] + change_in_position[0], self.position[1] + change_in_position[1], self.position[2] + change_in_position[2])

    def draw(self):
        self.drawer.draw()

    def updateVelocity(self, acc):
        self.velocity += acc

    def moveAccToVelocity(self):
        self.moveIncrement(self.velocity)

class Camera(Renderer):
    def __init__(self):
        super().__init__()

        # assume camera is looking at the origin at all times
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (config.WIDTH/config.HEIGHT), .1, 50)
        """
        zNear and zFar are the near and far clipping planes of your camera. Basically, if something is closer to your camera than zNear or further away than zFar, it will be culled and not rendered. 
        Usually, you'll just want to set zNear to something really small like 0.01, and zFar basically represents your "view distance".
        """

        self.from_position = np.array([0, 0, 0], dtype=np.float32)
        self.to_position =  np.array([0, 0, 0], dtype=np.float32)

        self.buffer = self.openGLCommands(glGenBuffers, 1)
        self.indexBuffer = self.openGLCommands(glGenBuffers, 1)
        self.length = 3

        self.vertices = np.array([
            0, 0, 0,
            config.AXIS_PLANE_LENGTH, 0, 0,
            0, config.AXIS_PLANE_LENGTH, 0,
            0, 0, config.AXIS_PLANE_LENGTH
        ], dtype=np.float32)

        self.indices = np.array([
            0, 1,
            0, 2,
            0, 3
        ], dtype=np.uint32)
        
        self.openGLCommands(glBindBuffer, GL_ARRAY_BUFFER, self.buffer)
        self.openGLCommands(glBindBuffer, GL_ELEMENT_ARRAY_BUFFER, self.indexBuffer)

        self.openGLCommands(glEnableVertexAttribArray, 0)
        self.openGLCommands(glVertexAttribPointer, 0, self.length, GL_FLOAT, False, self.vertices.itemsize * self.length, ctypes.c_void_p(0))

        self.shader = self.createShader("res/shaders/axis.shader")

    def look(self, from_position, to_position):
        self.from_position = np.array(from_position, dtype=np.float32)
        self.to_position = np.array(to_position, dtype=np.float32)

        gluLookAt(*from_position, *to_position, 0, 1, 0)

    def zoom(self, zoom_rate):
        glScalef(1 + zoom_rate, 1 + zoom_rate, 1 + zoom_rate)

    def rotatexy(self, change_xy):
        x, y = change_xy
        x /= 1
        y /= 1

        if x != 0:
            glRotatef(x, 1, 0, 0)

        if y != 0:
            glRotatef(y, 0, 1, 0)
        
    def drawCurrentPlane(self):
        self.openGLCommands(glUseProgram, self.shader)

        self.openGLCommands(glBufferData, GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        self.openGLCommands(glBufferData, GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)
        
        self.openGLCommands(glDrawElements, GL_LINES, len(self.indices), GL_UNSIGNED_INT, None)

    def get_xyz_angle(self, degrees=True):
        x,y,z = np.arctan2(self.to_position[1] - self.from_position[1], self.to_position[2] - self.from_position[2]), np.arctan2(self.to_position[0] - self.from_position[0], self.to_position[2] - self.from_position[2]), np.arctan2(self.to_position[0] - self.from_position[0], self.to_position[1] - self.from_position[1])

        if degrees:
            return np.degrees(x), np.degrees(y), np.degrees(z)
        else:
            return x, y, z
        

class App:
    def initialize_pygame(self):
        pg.init()
        self.pygame_screen = pg.display.set_mode((2440, 1080), pg.OPENGL | pg.DOUBLEBUF)
        pg.display.set_caption(config.TITLE)
        pg.display.gl_set_attribute(pg.GL_MULTISAMPLEBUFFERS, 1)

        glClearColor(0.2, 0.2, 0.2, 1.0)

    def __init__(self):
        self.clock = pg.time.Clock()
        self.running = True
        self.pygame_screen = None

        self.initialize_pygame()

        self.camera = Camera()
        self.camera.look(from_position=(10,10,10), to_position=(0, 0, 0))

        self.sphere = Sphere3d(.1, 40, 40, start_position=(0, 0, 0), color=(1.0, 0.0, 0.0, 1.0))
        self.sphere2 = Sphere3d(.1, 40, 40, start_position=(10, 0, 0), color=(0.0, 1.0, 0.0, 1.0))

        self.lastCalculation = time.time()
        self.counter = 0
        self.start_time = time.time()

        self.run()

    def run(self):
        pressing_mouse = False
        last_mouse_pos = (0, 0)

        while self.running:
            self.lastCalculation = time.time()
            time_in_simulation = self.counter * config.TIME_DISCRETE

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False

                if event.type == pg.MOUSEWHEEL:
                    self.camera.zoom(event.y * config.ZOOM_RATE)
                    
                if event.type == pg.MOUSEBUTTONDOWN:
                    pressing_mouse = True
                    last_mouse_pos = pg.mouse.get_pos()

                if event.type == pg.MOUSEBUTTONUP:
                    pressing_mouse = False

            if pressing_mouse:
                current_mouse_pos = pg.mouse.get_pos()
                change_xy = np.array([current_mouse_pos[0] - last_mouse_pos[0], current_mouse_pos[1] - last_mouse_pos[1]], dtype=np.float32)
                
                if abs(change_xy[0]) > abs(change_xy[1]):
                    change_xy[1] = 0

                elif abs(change_xy[1]) > abs(change_xy[0]):
                    change_xy[0] = 0

                else:
                    change_xy[0] = 0
                    change_xy[1] = 0

                self.camera.rotatexy(change_xy)
                last_mouse_pos = current_mouse_pos


            glClear(GL_COLOR_BUFFER_BIT)

            # draw the camera
            self.camera.drawCurrentPlane()
        
            # draw the elements

            self.sphere.draw()
            self.sphere2.draw()

            # rest
            
            self.counter += 1
            GlobalVariables.CALC_SPEED_PER_FRAME = (time.time() - self.lastCalculation)

            pg.display.flip()
            self.clock.tick(config.FPS)
            # there will be an inconsistency in the frame rate, but it can be ignored for now

            if int(self.counter/config.FPS) == float(self.counter/config.FPS):
                for _ in range(5):
                    print ("\033[A                             \033[A")

                x_angle, y_angle, z_angle = self.camera.get_xyz_angle()

                print(f"Current Frame: {self.counter}\nTime In Simulation: {round(time_in_simulation/60, 2)} minutes\nTime Since Start: {round((time.time() - self.start_time)/60, 2)} minutes", 
                      f"\nCalculation Time Per Frame: {round(GlobalVariables.CALC_SPEED_PER_FRAME, 4)} seconds\nCurrent Axis Angles: {x_angle}, {y_angle}, {z_angle} degrees")
                
        pg.quit()


if __name__ == "__main__":
    App()
    