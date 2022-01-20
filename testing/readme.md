# Testing Hardware

Current Hardware being used with a *Raspberry PI Zero WH*, *MPU9250 Module*.

MPU-9250 is a multi-chip module (MCM) consisting of two dies integrated into a single QFN package. One die the MPU-6500 houses the 3-Axis gyroscope, the 3-Axis accelerometer and temperature sensor. The other die houses the AK8963 3-Axis magnetometer. Hence, the MPU-9250 is a 9-axis MotionTracking device that combines a 3-axis gyroscope, 3-axis accelerometer, 3-axis magnetometer and a Digital Motion Processorâ„¢ (DMP). The hardware documentation for MPU-9250 can be found at (Product Specification)[https://github.com/Intelligent-Vehicle-Perception/MPU-9250-Sensors-Data-Collect/blob/master/doc/MPU-9250%20Product%20Specification%20Revision%201.1.pdf] and (Register Map and Descriptions)[https://github.com/Intelligent-Vehicle-Perception/MPU-9250-Sensors-Data-Collect/blob/master/doc/MPU-9250%20Register%20Map%20and%20Descriptions%20Revision%201.6.pdf].
- (Source)[https://pypi.org/project/mpu9250-jmdev/] 

  pip install mpu9250-jmdev 

Run *sudo raspi-config* and enable under interfaces REMOTE GPIO

Then to enable the hardware on your Raspberry PI you will need to do the following:

  sudo nano /etc/modules

Ensure both of these lines are listed.

  i2c-bcm2708 
  i2c-dev

Now run

  sudo apt-get install i2c-tools
  sudo i2cdetect -l

You should hopefully now see 2 IC2 Adapters listed.

  sudo i2cdetect -y 1 (or sudo i2cdetect -y 0)

Should now hopefully give you some results. Numbers will be in place of the "-" in some areas.

  sudo usermod -a -G i2c pi

Tip to David Grayson's documentation for his Raspberry C++ code for the MinIMU-9 sensor which is similar to the GY-80. And http://astrobeano.blogspot.com/2014/01/gy-80-orientation-sensor-on-raspberry-pi.html for figuring it all out!

Now to wire up the module to the Raspberry Pi, in most cases it is a female-to-female connector and you will need 4 wires.

Wiring: https://www.maxbotix.com/Setup-Raspberry-Pi-Zero-for-i2c-Sensor-151

Python test script file is from (mpu9250-jmdev 1.0.12)[https://pypi.org/project/mpu9250-jmdev/] 
