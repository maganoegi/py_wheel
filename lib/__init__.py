

import cv2
import numpy as np
import math


def create_triplet_array(parameters, side_modifier, minmax_modifier):
    """ 
    Creates the numpy array that holds the relevant HSV values from the parameters
    * PARAM: parameters: HSV values defined by the slider values : dictionary
    * PARAM: side_modifier: 1 for left and 2 for right - for code reusage : int
    * PARAM: minmax_modifier: whether we are looking for maximum of the HSV range or the minumum: string
    * RETURN: numpy array containing the HSV values we require
    """
    hue = f"hue {minmax_modifier} {side_modifier}" 
    sat = f"sat {minmax_modifier} {side_modifier}"
    val = f"val {minmax_modifier} {side_modifier}"

    return np.array([parameters[hue], parameters[sat], parameters[val]])
    

def get_minmax_HSV(parameters, left):
    """ 
    Creates 2 numpy arrays that hold the range triplets for the HSV parameters set by the user. This is used for the cv2.inRange() function.
    * PARAM: parameters, dictionary
    * PARAM: left, boolean
    * RETURN: min, max
    """
    side_modifier = "1" if left else "2"

    min_triplet = create_triplet_array(parameters, side_modifier, minmax_modifier = "min")
    max_triplet = create_triplet_array(parameters, side_modifier, minmax_modifier = "max")

    return min_triplet, max_triplet

def hsv_transform(is_left, img, hsv_img, parameters):
    """ 
    Applies the HSV triplets taken from the parameters and applies them to the image
    * PARAM: is_left: whether we are dealing with the small image on the left : bool
    * PARAM: img: original image
    * PARAM: hsv_img: original image in hsv
    * PARAM: parameters, dictionary
    * RETURN: min, max
    """
    
    min_triplet, max_triplet = get_minmax_HSV(parameters, is_left)
    mask = cv2.inRange(hsv_img, min_triplet, max_triplet)

    return cv2.bitwise_and(img, img, mask=mask)


def get_angle(lx, ly, rx, ry):
    """ 
    Takes the x,y coordinates of the centers of the two objects, and returns the angle they make with respect with the horizontal. 
    """
    rel_x = rx - lx
    rel_y = ry - ly

    center_x = rx - (rel_x//2) 
    center_y = ry - (rel_y//2)

    try:
        theta = math.degrees(math.atan2(rel_y, rel_x))
    except ZeroDivisionError:
        theta = 0.0

    return center_x, center_y, theta


def get_shape_coord(rgb_img):
    """
    Extracts the centroids of the 2 main objects. 
    * PARAM: rgb: original image in RGB
    * LOGIC: after the HSV transform, analyses how many "separate objects" are present. If their number is between 1 and THRESH, we start tracking angles. This is an attempt to make the logic behind the question "when should we start tracking" a bit more objective. This is NOT a perfect solution, but it works for now.
    * RETURN: center_x , center_y if LOGIC is respected, else None, None
    """
    THRESH = 5
    grayscale = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2GRAY)
    strel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3,3))
    opened = cv2.morphologyEx(grayscale, cv2.MORPH_OPEN, strel, iterations=2)

    num_labels, _, stats, centroids = cv2.connectedComponentsWithStats(opened, 4, cv2.CV_32S)
    if 1 < num_labels < THRESH:

        areas = stats[:,4]
        sorted_coordinates = sorted(zip(areas, centroids), key = lambda x: x[0])

        main_centroid = sorted_coordinates[-2][1]
        
        if not any([math.isnan(main_centroid[0]), math.isnan(main_centroid[1])]):

            center_x = int(main_centroid[0])
            center_y = int(main_centroid[1])

            return center_x, center_y
    
    return None, None

def analyze_detection(left, right, is_started):
    """
    Takes the left and right HSV Range images, analyses their content, modifying it if needed, and merges the two to create the final output.
    * PARAM: left: HSV range image on the left
    * PARAM: right: HSV range image on the right
    * PARAM: is_started: a simple logical control variable that is toggled when we first touch a slider, saying that "tracking" is "possible".
    * LOGIC: calculates the centers of the found objects, and checks whether they form the 2 objects we are trying to detect. 
        If all is good, it modifies the left image, writing "locked", drawing lines and calculating the angle. If not, the two images are just merged without any modifications
    * RETURN: Merged image and the angle (0.0 if no valid angle)
    """

    lx, ly = get_shape_coord(left)
    rx, ry = get_shape_coord(right)

    is_left_locked = lx != None and ly != None
    is_right_locked = rx != None and ry != None
    valid_4_tracking = is_left_locked and is_right_locked

        
    if valid_4_tracking and is_started:
        line_thickness = 2
        cx, cy, theta = get_angle(lx, ly, rx, ry)

        cv2.line(left, (lx, ly), (rx, ry), (0,0,255), line_thickness)

        cv2.circle(left, (cx, cy), 5, (0,0,255), line_thickness)

        cv2.putText(left, "locked", (50, 70), cv2.FONT_HERSHEY_PLAIN, 4, (0,255,0), 2)

    else: 
        theta = 0.0

    combined = cv2.bitwise_or(left, right)

    return combined, theta