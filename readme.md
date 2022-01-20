# Original Project

In 2014 or there abouts [Peter Cook](https://github.com/peterjc) put together an amzing little project.

[Blog Posts](http://astrobeano.blogspot.com/2014/01/instrumented-telescope-with-raspberry.html)

The idea was to use a Raspberry Pi and Gyro sensors to create a "Push To" style mount for his telescope.

>Instrumented Telescope with Raspberry Pi and orientation sensor
>A "Push To" telescope mount is like a fully automated "Go To" telescope mount, but without the motors. You must manually move the telescope, but because the >telescope knows where it is pointed, you get live tracking telling you where it needs to go.

Fast forward to 2022, 
- the GY-80 module originally used is out of date.
- astropysics - a Python module used is no longer maintained
- SkySafari has a whole lot of new versions

This project is now an attempt to perseve the original hard work and begin to refactor the code. The needs I have are limited to the "Push To", image capturing and camera connection are not something I am focused on.
