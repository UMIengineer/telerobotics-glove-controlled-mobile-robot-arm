# telerobotics-glove-controlled-mobile-robot-arm
Wearable IMU/flex-sensor glove controller, gesture CNN &amp; 3-DOF mobile robotic arm
# Wearable Glove Teleoperation & Vision-Guided 3-DOF Mobile Manipulator

A dual-microcontroller telerobotics system combining a **Raspberry Pi Pico W** sensor glove with a **Raspberry Pi 4B** tracked mobile manipulator. The system fuses real-time IMU tilt, finger flex/potentiometer joint tracking, forward-kinematics collision safety interlocks, and an **FP16 TensorFlow Lite CNN (98.75% test accuracy)** for hybrid gesture and wearable control.

## System Architecture

```mermaid
flowchart LR
    subgraph Glove [Wearable Control Glove - Pi Pico W]
        IMU[MPU-9250 IMU<br/>Accel + AK8963 Mag]
        POT[2x Index Potentiometers<br/>3D-Printed Joint Mounts]
        FLEX[Middle-Finger Flex Sensor<br/>25 kOhm Baseline]
        IMU & POT & FLEX --> PICO[Pico W JSON Server<br/>Persistent TCP Stream]
    end

    subgraph Robot [Mobile Manipulator - Raspberry Pi 4B]
        CAM[Robot-Eye USB Camera] --> MP[MediaPipe Hands ROI<br/>50x50 Grayscale Crop]
        MP --> TFL[FP16 TFLite CNN<br/>8 Gesture Classes]
        PICO -->|Low-Latency TCP Socket| THREAD[Multi-Threaded Controller<br/>50 Hz Servo + Chassis Loop]
        TFL -->|Speed 25-100% & Turn Overrides| THREAD
        US[HC-SR04 Ultrasonic<br/>15 cm Safety Stop] --> THREAD
        THREAD --> ARM[3-DOF Arm + Gripper<br/>FK Safety Limit y_e >= -4 cm]
        THREAD --> BASE[Tracked Chassis Motors<br/>PWM ENA/ENB Drive]
    end
