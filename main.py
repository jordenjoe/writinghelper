import os
import cv2 as cv
import time
from PIL import Image
from matplotlib import pyplot as plt
import statistics


practice_letters = ['L', 'F', 'E', 'H', 'T', 'I', 'D', 'B', 'P', 'U', 'J', 'C', 'O', 'G', 'Q', 'S', 'R', 'A', 'K', 'M', 'N', 'V', 'W', 'X', 'Y', 'Z', 'l', 't', 'i', 'c', 'k', 'o', 'p', 's', 'v', 'u', 'w', 'x', 'z', 'h', 'n', 'm', 'r', 'b', 'a', 'd', 'g', 'q', 'e', 'f', 'j', 'k', 'y']
practice_letters = ['L', 'F']
TK_SILENCE_DEPRECATION=1

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

    return img   

def generate_size_feedback(top_5):

    size_feedback_score = 0

    average = statistics.mean(top_5)

    for index, number in enumerate(top_5):

        if number > average + (average/3):

            print(f"Letter {index+1} is too large compared to your other letters.",
                   "Try writing it smaller. ")
            
        elif number < average - (average/3):

            print(f"Letter {index+1} is too small compared to your other letters.",
                   "Try writing it larger. ")
            
        else: 
            size_feedback_score += 1
    
    if size_feedback_score == 5:
        print(f"Good letter size for all letters.")

def generate_spacing_feedback(bounding_rectangles):

    print('bounding_rectangles: ', bounding_rectangles)

    spacing_feedback_score = 0
    spacings = []

    # spacing between:
    # 1 and 2
    # 2 and 3
    # 3 and 4
    # 4 and 5
    for i in range(4):

        firstLetterRight = bounding_rectangles[i][0]+bounding_rectangles[i][2]
        secondLetterLeft = bounding_rectangles[i+1][0]
        print(bounding_rectangles[i][0]+bounding_rectangles[i][2])
        print(bounding_rectangles[i+1][0])
        spacing = secondLetterLeft-firstLetterRight

        spacings.append(spacing)


    print(spacings)

def generate_bounding_rectangles(contours, img):

     # get the main 5 letters written on the user page
    areas = []

    for contour in contours:
        areas.append(cv.contourArea(contour))

    # Sort the list in descending order
    sorted_areas = sorted(areas, reverse=True)

    # Get the top 5 contours
    top_5 = sorted_areas[1:6]

    print("top 5: ", top_5)

    # get the bounding rectangles

    bounding_rectangles = []

    i = 0
    for contour in contours:

        if cv.contourArea(contour) in top_5:

            # Get the bounding rectangle
            x, y, w, h = cv.boundingRect(contour)

            bounding_rectangles.append([x,y,w,h])

            i += 1

    print('bounding rectangles: ', bounding_rectangles)

    return sorted(bounding_rectangles, key=lambda rect: rect[0])

def generate_letter_labels(written_letter_information, img):

    labels = ["Letter 1", "Letter 2", "Letter 3", "Letter 4", "Letter 5"]

    i = 0
    for letter in written_letter_information:
            
        x = written_letter_information[letter]["Bounding Rectangle"][0]
        y = written_letter_information[letter]["Bounding Rectangle"][1]
        w = written_letter_information[letter]["Bounding Rectangle"][2]
        h = written_letter_information[letter]["Bounding Rectangle"][3]

        # TODO: change text and rectangle color based on feedback - orange, green, or red

        # Draw the rectangle on the original image
        cv.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)

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

    for item in written_letter_information:
        print(item, written_letter_information[item])

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
    new_w = max(x_vals) - new_x + 300
    new_h = max(y_vals) - new_y + 300

    roi = img[new_y:new_y+new_h, new_x:new_x+new_w]

    # Resize the ROI
    zoom_level = 2
    zoomed_roi = cv.resize(roi, (new_w*zoom_level, new_h*zoom_level))

    return zoomed_roi

def generate_letter_feedback(img):
     
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    ret, th1 = cv.threshold(gray, 127, 255, cv.THRESH_BINARY)

    # get the contours, narrow down
    contours, hierarchy = cv.findContours(th1, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)

    sorted_bounding_rectangles = generate_bounding_rectangles(contours, img)
    written_letter_information = generate_letter_information(sorted_bounding_rectangles)

    #generate_size_feedback(top_5)
    #time.sleep(3)
    #generate_spacing_feedback(sorted_bounding_rectangles)
    #time.sleep(3)

    # add labels to each letter, in sorted order.
    # change color based on feedback scores
    generate_letter_labels(written_letter_information, img)

    # zoom in on image so user can see better
    zoomed_roi = generate_image_zoom(img, sorted_bounding_rectangles)

    plt.imshow(zoomed_roi)
    plt.title("Contours")
    plt.show()
     
    return 1

def letter_analysis(letter):

        print(f"\n-----------{letter}-----------\n")
        
        img = get_letter_image(letter)
        print('Thanks for uploading your image!'\
        '\nGenerating feedback.....')
        generate_letter_feedback(img)

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
                 print('Your result ', result, ' was less than your threshold ', threshold,\
                       "\nLet's get more practice!")
                 time.sleep(5)
            else:
                print('Your result ', result, ' was greater than your threshold! Congrats.')
                break

        print('Do you want to continue onto the next letter? Y/N')
        response = input()
        if response != 'Y':
             exit()

main()