import os
import cv2 as cv
import time
from PIL import Image
from matplotlib import pyplot as plt
import statistics
import pytesseract
import numpy as np


practice_letters = ['L', 'F', 'E', 'H', 'T', 'I', 'D', 'B', 'P', 'U', 'J', 'C', 'O', 'G', 'Q', 'S', 'R', 'A', 'K', 'M', 'N', 'V', 'W', 'X', 'Y', 'Z', 'l', 't', 'i', 'c', 'k', 'o', 'p', 's', 'v', 'u', 'w', 'x', 'z', 'h', 'n', 'm', 'r', 'b', 'a', 'd', 'g', 'q', 'e', 'f', 'j', 'k', 'y']
practice_letters = ['A', 'L', 'F', 'E']
# L is bad at detection
# A has some feeedback on sizing
# F is bad at size
# E is bad at spacing
TK_SILENCE_DEPRECATION=1

# psm 10: Treat the image as a single character.
myconfig = r"--psm 10 --oem 3"

# this works okay, but only for A
#myconfig = r"--psm 6"

# 13
#psm --11
#letter_img ['e', 'p', ' ', 'o', 'e', '\n']

#r"--psm 8"
#letter_img ['a', '\n']

def get_letter_image(letter):
     
    i = 0
    filename = f"{letter}_{i+1}.jpg"
    print(f"Please upload an image of the letter '{letter}'",
        f"\nwritten five times in a row, like this: \n\n{letter} {letter} {letter} {letter} {letter}",
        f"\n\nTitle the image '{filename}'")
    
    print('Press enter once the image has been uploaded.')
    input()

    while not os.path.exists(filename):
        print("Image file does not exist. Retrying in 5 seconds...")
        time.sleep(5)

    try:
        # img = Image.open(filename)
        img = cv.imread(filename)
    except Exception as e:
        print(f"Error opening image file: {str(e)}")

    return img, filename 

def generate_size_feedback(written_letter_information):

    area_list = [sub_dict['Area'] for sub_dict in written_letter_information.values()]


    size_feedback_scores = []

    median = statistics.median(area_list)

    for index, number in enumerate(area_list):

        if number > median + (median/3):

            print(f"Letter {index+1} is too large compared to your other letters.",
                   "Try writing it smaller. ")
            size_feedback_scores.append(0)
            
        elif number < median - (median/3):

            print(f"Letter {index+1} is too small compared to your other letters.",
                   "Try writing it larger. ")
            size_feedback_scores.append(0)
            
        else: 
            size_feedback_scores.append(1)
    
    if sum(size_feedback_scores) == 5:
        print(f"Reasonable letter size for all letters.")

    return size_feedback_scores

def generate_spacing_feedback(written_letter_information):

    # print('written_letter_information: ', written_letter_information)

    spacing_feedback_scores = [0,0,0,0,0]
    spacings = []

    # spacing between:
    # 1 and 2
    # 2 and 3
    # 3 and 4
    # 4 and 5
    for i in range(4):

        firstLetterRight = written_letter_information[i]["Bounding Rectangle"][0] +\
                            written_letter_information[i]["Bounding Rectangle"][2]

        secondLetterLeft = written_letter_information[i+1]["Bounding Rectangle"][0]

        spacing = secondLetterLeft-firstLetterRight

        spacings.append(spacing)

    median = statistics.median(spacings)

    for index in range(4):
        spacing = spacings[index]

        # if not within 50 of median, flag spacing for both letters 
        if (median - 50 < spacing < median + 50):

            spacing_feedback_scores[index] = 1
            spacing_feedback_scores[index+1] = 1

        else:
            print('Letter ', index+1, ' and letter ', index+2, ' have incorrect relative spacing')
            spacing_feedback_scores[index] = 0
            spacing_feedback_scores[index+1] = 0

    if sum(spacing_feedback_scores) == 5:
        print('Reasonable letter spacing for all letters.')

    return spacing_feedback_scores

def generate_bounding_rectangles(contours, img):

     # get the main 5 letters written on the user page
    areas = []

    for contour in contours:
        areas.append(cv.contourArea(contour))

    # Sort the list in descending order
    sorted_areas = sorted(areas, reverse=True)

    # Get the top 5 contours
    top_5 = sorted_areas[1:6]

    # print("top 5: ", top_5)

    # get the bounding rectangles

    bounding_rectangles = []

    i = 0
    for contour in contours:

        if cv.contourArea(contour) in top_5:

            # Get the bounding rectangle
            x, y, w, h = cv.boundingRect(contour)

            bounding_rectangles.append([x,y,w,h])

            i += 1

    # print('bounding rectangles: ', bounding_rectangles)

    return sorted(bounding_rectangles, key=lambda rect: rect[0])

def generate_letter_labels(written_letter_information, img, total_feedback_scores, green_threshold):

    labels = ["Letter 1", "Letter 2", "Letter 3", "Letter 4", "Letter 5"]

    i = 0
    for letter in written_letter_information:
            
        x = written_letter_information[letter]["Bounding Rectangle"][0]
        y = written_letter_information[letter]["Bounding Rectangle"][1]
        w = written_letter_information[letter]["Bounding Rectangle"][2]
        h = written_letter_information[letter]["Bounding Rectangle"][3]

        # TODO: change text and rectangle color based on feedback - orange, green, or red
        if total_feedback_scores[i] >= green_threshold:
            color = (0, 255, 0) # green
        elif total_feedback_scores[i] == 0:
            color = (255, 0, 0) # red
        else:
            color = (255, 165, 0) # orange

        # Draw the rectangle on the original image
        cv.rectangle(img, (x, y), (x+w, y+h), color, 2)

        # Add the label to the rectangle
        label = labels[i]

        cv.putText(img, label, (x, y-10), cv.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
        
        i += 1

def generate_letter_information(sorted_bounding_rectangles):

    written_letter_information = {}

    # put the written letters into a dictionary by order left to right
    # with bounding rectangles and areas

    i = 0
    for bounding_rectangle in sorted_bounding_rectangles:
        written_letter_information[i] = {"Bounding Rectangle":bounding_rectangle,
                                         "Area":bounding_rectangle[2]*bounding_rectangle[3]}
        i += 1

    # for item in written_letter_information:
    #   print(item, written_letter_information[item])

    return written_letter_information

def generate_image_zoom(img, sorted_bounding_rectangles):

    # x, y, w, h
    # x is the furthest left x (min x) - 100
    # y is the furthest up y (min y) - 100
    # w is the furthest right x (max x) - (min x) + 100
    # h is the max y - min y + 100 

    new_list = []
    for i in range(2):
        column = []
        for j in range(len(sorted_bounding_rectangles)):
            column.append(sorted_bounding_rectangles[j][i])
        new_list.append(column)

    x_vals = new_list[0]
    y_vals = new_list[1]

    new_x = max(min(x_vals)-100,0)
    new_y = max(min(y_vals)-100,0)
    new_w = max(x_vals) - new_x + 500
    new_h = max(y_vals) - new_y + 500

    roi = img[new_y:new_y+new_h, new_x:new_x+new_w]

    # Resize the ROI
    zoom_level = 2
    zoomed_roi = cv.resize(roi, (new_w*zoom_level, new_h*zoom_level))

    return zoomed_roi

def generate_size_spacing_feedback(img, written_letter_information, sorted_bounding_rectangles):

    # 1 point possible per letter
    size_feedback_scores = generate_size_feedback(written_letter_information)

    # 1 point possible per letter
    spacing_feedback_scores = generate_spacing_feedback(written_letter_information)

    # print('size_feedback_scores: ', size_feedback_scores)
    # print('spacing_feedback_scores: ', spacing_feedback_scores)

    # total feedback score 
    total_feedback_scores = [size_feedback_scores[i] + spacing_feedback_scores[i] for i in range(len(size_feedback_scores))]

    # add labels to each letter, in sorted order.
    # change color based on feedback scores
    generate_letter_labels(written_letter_information, img, total_feedback_scores, 2)

    # zoom in on image so user can see better
    zoomed_roi = generate_image_zoom(img, sorted_bounding_rectangles)

    # commenting out during testing but add back later
    plt.imshow(zoomed_roi)
    plt.title("Size and Spacing Feedback - Visualized")
    plt.show()

def generate_readability_feedback(filename, written_letter_information, goal_letter):
    
    # game plan
    # print('written_letter_information')
    # print(written_letter_information)

    detection_feedback_scores = [0,0,0,0,0]

    # iterate through letters
    for letter in written_letter_information:

        letter_img = generate_letter_image(letter, written_letter_information, filename)

        scale_percent = 60 # percent of original size
        width = int(letter_img.shape[1] * scale_percent / 100)
        height = int(letter_img.shape[0] * scale_percent / 100)
        dim = (width, height)
        
        # resize image - this part was key
        letter_img = cv.resize(letter_img, dim, interpolation = cv.INTER_AREA)

        #gry = cv.cvtColor(letter_img, cv.COLOR_BGR2GRAY)

        thr = cv.threshold(letter_img, 120, 255, cv.THRESH_OTSU)[1]

        #ret,thresh1 = cv.threshold(letter_img,127,255,cv.THRESH_BINARY)
        thr = cv.blur(thr,(4,4))
        # letter_img = letter_img.crop((left-10, top-10, right+10, bottom+10))
        
        # for testing purposes
        # plt.imshow(thr)
        # plt.title("Tester")
        # plt.show()

        detected_letter = list(pytesseract.image_to_string(thr, config=myconfig))
        
        # gets string or nothing - remove \n from the end
        if len(detected_letter) > 1:
            detected_letter = detected_letter[0]
        else:
            detected_letter = ''

        #print('detected letter:  ', detected_letter)
        #print('goal letterr: ', goal_letter)
        
        if detected_letter == goal_letter:
            detection_feedback_scores[letter] = 1
        else:
            print("Letter ", letter+1, " did not match on identification.")

    if sum(detection_feedback_scores) == 5:
        print('All letters were able to be identified.')

    return detection_feedback_scores

def generate_letter_image(letter, written_letter_information, filename):

        bounding_rectangle = written_letter_information[letter]['Bounding Rectangle']

        left = bounding_rectangle[0]
        top = bounding_rectangle[1]
        right = bounding_rectangle[0] + bounding_rectangle[2]
        bottom = bounding_rectangle[1] + bounding_rectangle[3]

        letter_img = Image.open(filename)

        # crop to the letter's bounding rectangle so you have 
        # a per-letter image
        letter_img = cv.imread(filename, cv.IMREAD_GRAYSCALE)

        # crop the image down
        letter_img = letter_img[top-50:bottom+50, left-50:right+50]

        return letter_img

def generate_thickness_feedback(filename, written_letter_information):

    # general idea: use the concept of erosion to detect problems
    # with line thickness.
    letter_percents = []

    # do this on a per-letter basis 

    # can get up to 2 for each value
    thickness_feedback_scores = [0,0,0,0,0]

    # iterate through letters
    for letter in written_letter_information:

        letter_img = generate_letter_image(letter, written_letter_information, filename)

        # get the inverse
        letter_img = cv.bitwise_not(letter_img)

        # Creating kernel
        kernel = np.ones((6, 6), np.uint8)

        letter_img = cv.threshold(letter_img, 120, 255, cv.THRESH_BINARY)[1]

        # Using cv2.erode() method 
        letter_img = cv.erode(letter_img, kernel, iterations=4) 

        #plt.imshow(letter_img)
        #plt.title("Testing Thickness")
        #plt.show()

        # check if it's thick enough (should survive at least 4 iterations)
        #print(letter_img)

        # get the unique values (0 and 255) and the counts for each
        uniques, counts = np.unique(letter_img, return_counts=True)
        #print('uniques: ', uniques)
        #print('counts: ', counts)

        # get percentage
        percent_letter = counts[1]/counts[0]

        # print('Percent letter left: ', percent_letter)

        # percent letter should be around 2 - 30%
        if percent_letter > .3:
            print('Letter ', letter+1, ' is too thick in general')

        elif percent_letter < .02:
            print('Letter ', letter+1, ' is too thin in general')
        
        else:
             thickness_feedback_scores[letter] += 1

        letter_percents.append(percent_letter)


    # check for inconsistent thickness across the letters
    # i.e. one is much thicker than the others

    median = statistics.median(letter_percents)
    #print('Median: ', median)

    for index, number in enumerate(letter_percents):

        #print('Letter: ', index+1, ' had a letter percent of ', number)

        if number > median + (median/3):

            print(f"Letter {index+1} is too thick compared to your other letters. ")
            
            
        elif number < median - (median/3):

            print(f"Letter {index+1} is too thin compared to your other letters.")
            
        else:
            thickness_feedback_scores[index] += 1

    if sum(thickness_feedback_scores) == 10:
        print('All letters had good thickness.')

    return thickness_feedback_scores

def generate_similarity_feedback(img, sorted_bounding_rectangles, filename, written_letter_information, goal_letter):

    # generate letter detection scores with tesseract
    readability_feedback_scores = generate_readability_feedback(filename, written_letter_information, goal_letter)

    # augment with personalized functions for symmetry 
    # maybe this is "symmetry" feedback - will depend on letter

    # augment with function for line thickness
    # maybe this is "thickness" feedback
    thickness_feedback_scores = generate_thickness_feedback(filename, written_letter_information)

    # print('readability_feedback_scores: ', readability_feedback_scores)
    # print('thickness_feedback_scores: ', thickness_feedback_scores)

    # total feedback score 
    total_feedback_scores = [readability_feedback_scores[i] + thickness_feedback_scores[i] for i in range(len(thickness_feedback_scores))]

    # add labels to each letter, in sorted order.
    # change color based on feedback scores
    generate_letter_labels(written_letter_information, img, total_feedback_scores, 3)

    # zoom in on image so user can see better
    zoomed_roi = generate_image_zoom(img, sorted_bounding_rectangles)

    # commenting out during testing but add back later
    plt.imshow(zoomed_roi)
    plt.title("Similarity Feedback - Visualized")
    plt.show()

def generate_letter_feedback(img, filename, goal_letter):
     
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    ret, th1 = cv.threshold(gray, 127, 255, cv.THRESH_BINARY)

    # get the contours, narrow down
    contours, hierarchy = cv.findContours(th1, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)

    sorted_bounding_rectangles = generate_bounding_rectangles(contours, img)
    written_letter_information = generate_letter_information(sorted_bounding_rectangles)

    # SIZE AND SPACING SCORES #
    print('\n\n --- Size and Spacing Feedback ---')
    generate_size_spacing_feedback(img, written_letter_information, sorted_bounding_rectangles)

    # SIMILARITY SCORES: letter detection, symmetry, and thickness #
    print('\n\n --- Similarity Feedback ---')
    generate_similarity_feedback(img, sorted_bounding_rectangles, filename, written_letter_information, goal_letter)

    return 1

def letter_analysis(letter):

        print(f"\n-----------{letter}-----------\n")
        
        img, filename = get_letter_image(letter)
        print('Thanks for uploading your image!'\
        '\nGenerating feedback.....\n')
        generate_letter_feedback(img, filename, letter)

        # automating a decimal for now
        return .5

def main():

    print('What would you like the acceptance threshold to be?'\
          '\nEnter a decimal between 0 and 1.')
    
    threshold = float(input())

    for letter in practice_letters:

        while 1: 
            result = letter_analysis(letter)

            if result < threshold:
                 print('\n\nYour result ', result, ' was less than your threshold ', threshold,\
                       "\nLet's get more practice!")
                 time.sleep(5)
            else:
                print('\n\nYour result ', result, ' was greater than your threshold! Congrats.')
                break

        print('Do you want to continue onto the next letter? Y/N')
        response = input()
        if response != 'Y':
             exit()

main()