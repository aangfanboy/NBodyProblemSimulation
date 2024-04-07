#shader vertex
#version 330 core

in vec3 position;

void main()
{
    gl_Position = vec4(position, 1.0);
}

#shader fragment
#version 330 core

out vec4 color;
uniform vec4 objectColor;

void main()
{
    color = objectColor;
}


