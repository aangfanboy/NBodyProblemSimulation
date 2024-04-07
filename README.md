# N Body Problem Simulation With OpenGL & CUDA

This project aims to simulate the well known N Body problem in physics. Code skeleton will be written in Python. After successful simulation of 2 body problem, code will be migrated to C++, then calculations will be made with CUDA.

## Time Discretization Policy

For simulating purposes, we will generate **60 frames per second**. If user wants real time speed to match the simulation speed, s/he can set *config.TIME_DISCRETE* to reciprocal of *config.FPS*. This will not promise a perfect time alignment, but error range will be small enogh to ignore.

To increase the speed of simulation, *config.FPS* or/and *config.TIME_DISCRETE* can be increased. However, the latter is not recommended since it will disrupt the continuity illusion.

## Markov Policy

Markov rule **will be followed** at each step.

## Coordinate System

![coordinat system of opengl](https://learnopengl.com/img/getting-started/coordinate_systems_right_handed.png)

Coordinate system definitions above (1<sup>*</sup>) is valid.

Even though camera has settings for rotation and zoom, using the initial Camera coordinates for this task and sticking with them is recommended. Check the definition:

`self.camera.look(from_position=(10,10,10), to_position=(0, 0, 0))` @main.py init function of the class *App*

## To-Do

- [x] Create the 3D Environment
- [x] Add Newtonian Coordinate Map to the Main Screen
- [x] Finalize time discretization process
- [ ] Finalize the simulation for 2 body problem, share results with different initial momentum
- [ ] Solve the same 2 body calculations with CUDA (benchmark ?)
- [ ] Solve the N body problem with CUDA's parallel computing

## License

MIT-License Applies

## References

1. https://learnopengl.com/Getting-started/Coordinate-Systems