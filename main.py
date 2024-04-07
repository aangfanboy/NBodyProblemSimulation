import pygame as pg
import numpy as np
import random
from OpenGL.GL import *
from OpenGL.GLU import *

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QPushButton, QWidget, QSlider, QLabel, QGridLayout

class GlobalVariables:
    TITLE = "OpenGL with Pygame and PyQt5"
    CURRENT_ANGLE = 0
    ZOOM_RATE = 0.1

    G = 6.67430e-11 # m^3 kg^-1 s^-2

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

        self.run()

    def run(self):
        pressing_mouse = False
        while self.running:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False
                if event.type == pg.MOUSEBUTTONDOWN:
                    pressing_mouse = True

                if event.type == pg.MOUSEBUTTONUP:
                    pressing_mouse = False

                if event.type == pg.MOUSEMOTION:
                    if pressing_mouse:
                        glRotatef(event.rel[0], event.rel[1], 1, 0)
                        
                        GlobalVariables.CURRENT_ANGLE += event.rel[0]

                if event.type == pg.MOUSEWHEEL:
                    glScalef(1 + event.y * 0.1, 1 + event.y * 0.1, 1 + event.y * 0.1)

                    GlobalVariables.ZOOM_RATE += event.y * 0.5
                    

            glClear(GL_COLOR_BUFFER_BIT)
        
            self.cube.draw()
            pg.display.flip()
            self.clock.tick(60)

        pg.quit()

class PyQtController(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(GlobalVariables.TITLE)
        self.setGeometry(100, 100, 600, 800)

        self.layout = QGridLayout()
        
        self.text = QLabel("Current Angle: 0 degrees")
        self.text2 = QLabel("Zoom Rate: 0")
        self.layout.addWidget(self.text, 0, 0)
        self.layout.addWidget(self.text2, 1, 0)

        self.button = QPushButton("Click me")
        self.button.clicked.connect(self.button_clicked)
        self.layout.addWidget(self.button, 2, 0)

        self.setLayout(self.layout)

        self.initUI()

    def initUI(self):
        timer = QTimer(self)
        timer.timeout.connect(self.update_text)
        timer.start(100)

        self.show()

    def update_text(self):
        self.text.setText(f"Current Angle: {GlobalVariables.CURRENT_ANGLE} degrees")
        self.text2.setText(f"Zoom Rate: {GlobalVariables.ZOOM_RATE}")

    def button_clicked(self):
        print("Button clicked")

if __name__ == "__main__":
    # show both pyqt5 window and pygame window
    
    app = QApplication([])
    controller = PyQtController()

    App()

    app.exec_()
    