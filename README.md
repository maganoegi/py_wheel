# Computer Vision - Wheel
### Author: Sergey Platonov
### Class of: Adrien Lescourt,  Valérie Duay
### HEPIA ITI sem.4 June 2020
___
## Description:
This goal of this project was to implement a concrete application that uses OpenCV and Python for object tracking using HSV color space. This allows us to focus our algorithm's attention to 2 objects of a specific color, and use them as a "steering wheel" input. PyQt5 is used create a GUI.

## Inputs
2 options are available, and are controlled with the use of a CLI flag:
* Webcam feed, enabled when the flag __-l__ or __--live__ is used.
* Video feed, that reads the video that comes with this project. The project is graded on the performance of the algorithm on this video, thus it is hardcoded around it. The video file name is __wheel_racing.avi__.

## Outputs
* Visual output on different screens, allowing to see all the transformations an individual frame goes through.
* In the case of the __video__ input, a file __angles.txt__ is created __in the end__ of the video, containing the angles recorded during the video. 

## Usage
Launch the Python script with or without flags, depending on use case:
```bash
python3 . --live # for webcam feed
```
or
```bash
python3 . # for video feed
```

Next, you will see an application that hosts 5 displays, along with 2 areas with sliders. These sliders allow you to control the individual HSV range filters applied to your image. For every respective HSV value component, you will see a __min__ and a __max__ slider. Play with these to isolate a bright colored object and follow it!

Once 2 objects (left and right) have been detected, you will see a "locked" message appear in the central window. This means that the algorith is actively calculating the angle created by a line drawn between the center of those 2 objects and the horizontal, drawing it in the top right window. These angles constitute our output. These angles can be used for controlling a racing game, as our professor Adrien Lescourt demonstrates in the following demo: https://www.youtube.com/watch?v=glspLFKnuy8. 

## Stuff I'm not happy with
* I would like to make my algorithm smarter and give more thought to the triggers that allow us to detect the angles. Simply put: when does our program understand that the objets we have manually "isolated" constitute the "actual" objects we want to track? I think this cannot be achieved fully in a manual manner (without using ML), but an approximation can be made by implementing a set of "conditions" for the program to respect, before it starts detecting stuff. In my opinion, an individual condition is weak, but a big number of concrete, coherent and atomic conditions could reduce the risk of false positive reading.