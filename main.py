import pygame as pg
import numpy as np
import random
import time
from OpenGL.GL import *
from OpenGL.GLU import *

import config

class GlobalVariables:
    CURRENT_ANGLE = 0
    ZOOM_RATE = 0.1

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
    
    def createShader(self, path):
        vertexShader, fragmentShader = self.parseShader(path)

        program = self.openGLCommands(glCreateProgram)
        
        vertexShader = self.compileShader(GL_VERTEX_SHADER, vertexShader)
        fragmentShader = self.compileShader(GL_FRAGMENT_SHADER, fragmentShader)

        # self.openGLCommands(glAttachShader, program, vertexShader)
        self.openGLCommands(glAttachShader, program, fragmentShader)

        self.openGLCommands(glLinkProgram, program)
        self.openGLCommands(glValidateProgram, program)

        self.openGLCommands(glDeleteShader, vertexShader)
        self.openGLCommands(glDeleteShader, fragmentShader)

        return program

class Triangle(Renderer):
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
        self.openGLCommands(glUseProgram, self.shader)

        self.colorUniformLoc = self.openGLCommands(glGetUniformLocation, self.shader, "objectColor")
        self.color = color

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

        self.triangle = Triangle(self.vertices, self.indices, 3, color=color)

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
        for i in range(len(self.triangle.vertices)):
            if i % 3 == 0:
                self.triangle.vertices[i] += change_in_position[0]
            elif i % 3 == 1:
                self.triangle.vertices[i] += change_in_position[1]
            elif i % 3 == 2:
                self.triangle.vertices[i] += change_in_position[2]

        self.position = (self.position[0] + change_in_position[0], self.position[1] + change_in_position[1], self.position[2] + change_in_position[2])

    def draw(self):
        self.triangle.draw()

    def updateVelocity(self, acc):
        self.velocity += acc

    def moveAccToVelocity(self):
        self.moveIncrement(self.velocity)


class App:
    def initialize_pygame(self):
        pg.init()
        pg.display.set_mode((2440, 1080), pg.OPENGL | pg.DOUBLEBUF)
        pg.display.set_caption(config.TITLE)
        pg.display.gl_set_attribute(pg.GL_MULTISAMPLEBUFFERS, 1)

        glClearColor(0.2, 0.2, 0.2, 1.0)

    def __init__(self):
        self.clock = pg.time.Clock()
        self.running = True
        self.elements = []

        self.initialize_pygame()

        self.cube = Sphere3d(1, 50, 50, start_position=(-20, 10, 0), color=(1.0, 0.0, 0.0, 1.0))

        self.elements.append(self.cube)

        gluPerspective(45, (2440/1080), 0.4, 50.0)
        glTranslatef(0.0, 0.0, -50)

        self.lastCalculation = time.time()
        self.counter = 0
        self.start_time = time.time()

        self.run()

    def run(self):
        while self.running:
            self.lastCalculation = time.time()
            time_in_simulation = self.counter * config.TIME_DISCRETE

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False

            glClear(GL_COLOR_BUFFER_BIT)
        
            self.cube.draw()
            
            self.counter += 1
            GlobalVariables.CALC_SPEED_PER_FRAME = (time.time() - self.lastCalculation)

            pg.display.flip()
            self.clock.tick(config.FPS)
            # there will be an inconsistency in the frame rate, but it can be ignored for now

            if int(self.counter/config.FPS) == float(self.counter/config.FPS):
                for _ in range(6):
                    print ("\033[A                             \033[A")

                print(f"Current Frame: {self.counter}\nTime In Simulation: {round(time_in_simulation/60, 2)} minutes\nTime Since Start: {round((time.time() - self.start_time)/60, 2)} minutes", 
                      f"\nCalculation Time Per Frame: {round(GlobalVariables.CALC_SPEED_PER_FRAME, 4)} seconds")
                
        pg.quit()


if __name__ == "__main__":


    App()
    