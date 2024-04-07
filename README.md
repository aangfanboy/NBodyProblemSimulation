# N Body Problem Simulation With OpenGL & CUDA

This project aims to simulate the well known N Body problem in physics. Code skeleton will be written in Python. After successful simulation of 2 body problem, code will be migrated to C++, then calculations will be made with CUDA.

## Time Discretization Policy

For simulating purposes, we will generate **60 frames per second**. If user wants real time speed to match the simulation speed, s/he can set *config.TIME_DISCRETE* to reciprocal of *config.FPS*. This will not promise a perfect time alignment, but error range will be small enogh to ignore.

To increase the speed of simulation, *config.FPS* can be increased or/and *config.TIME_DISCRETE* can be increased. However, latter is not recommended since it will disrupt the continuity illusion.

Please watch for the *Wait Time* log in the console while changing the *FPS* or *TIME_DISCRETE* values. If Wait Time is negative, this means your calculations are not fast enough to keep up with the desired frame rate. In this case, you can either decrease the *FPS* or increase the *config.TIME_DISCRETE* values. Former is recommended.

## Markov Policy

Markov Chain rules **will be followed** at each step.

## To-Do

- [x] Create the 3D Environment
- [ ] Add Newtonian Coordinate Map to the Main Screen
- [x] Finalize time discretization process
- [ ] Finalize the simulation for 2 body problem, share results with different initial momentum
- [ ] Migrate the Code to C++ and repeat the results
- [ ] Solve the same 2 body calculations with CUDA (benchmark ?)
- [ ] Solve the N body problem with CUDA's parallel computing

## License

MIT-License Applies

## References

None for now.