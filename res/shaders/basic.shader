#shader vertex

#shader fragment
#version 330 core

out vec4 color;
uniform vec4 objectColor;

void main()
{
    color = objectColor;
}


