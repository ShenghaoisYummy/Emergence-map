import matplotlib  
matplotlib.use('Agg')  
from matplotlib import pyplot as plt  

import numpy as np
from os.path import dirname, abspath, isfile
from emergence_map.Analysis_algorithm import find_gradient, find_lines
import scipy
import sys
import glob
from PIL import Image
import cv2

replant_map_path = abspath('.')
cut_img_src_1= replant_map_path + "/emergence_map/static/cutimg/1.png"

def find_gap(img_path, minimum_gap, pixel_value_cutoff):
    image_paths = []
    count = 0

    plot_fourier = False  # Set to True for 2d fourier transform plot to shown
    plot_line_find = False  # Set to True for found lines plot to be shown
    # This is the avg pixel value of the lines, below which lines will not be detected.

    image_paths.append(cut_img_src_1)
    #image_paths.append('png_pict/22.png')

    #image_paths.append('png_pict/29.png')

    #image_paths.append('png_pict/79.png')
    #image_paths.append('png_pict/0.png')
    #image_paths.append('png_pict/1.png')
    # image_paths.append('../Media/0pos.png')
    # image_paths.append('../Media/0.png')
    #image_paths.append('png_pict/116.png')
    #image_paths.append('png_pict/131.png')
    #image_paths.append('png_pict/78.png')

    halfway = round(len(image_paths) / 2)

    # find good estimation of gradient from the middle images
    for i in range(halfway, halfway + 10):
        # print(image_paths[i])
        img = plt.imread(image_paths[i]).astype(float)
        row_distance, source_angle = find_gradient.run_everything(img, plot_fourier)
        if round(source_angle) == 0 or round(source_angle) == -90 or round(source_angle) == 90 or round(
                source_angle) == 45 or round(source_angle) == -45:
            print('Bad angle:')
            print(source_angle)
        else:
            source_gradient = np.tan(np.deg2rad(source_angle))
            source_gradient, detected_lines = find_lines.run_everything(img, source_gradient, row_distance, plot_line_find, pixel_value_cutoff)
            break

    print('selected gradient:')
    print(source_gradient)

    # sys.exit()
    number_gap=[]

    for image in glob.glob(img_path):  # Loop through images provided in image_paths
        print('**--**')
        print(image)
        
        img = plt.imread(image).astype(float)

        row_distance, row_angle = find_gradient.run_everything(img, plot_fourier)

        # checking if the detected row_angle is ok
        if round(row_angle) == 0 or round(row_angle) == -90 or round(row_angle) == 90 or round(
                row_angle) == 45 or round(
                row_angle) == -45:
            print('detected bad angle, using source_angle')
            gradient = source_gradient
        else:
            gradient = np.tan(np.deg2rad(row_angle))

        if count > 0 and improved_gradient and abs(improved_gradient - gradient) < 0.5:

            print('running with improved_gradient:')
            print(improved_gradient)
            improved_gradient, detected_lines = find_lines.run_everything(img, improved_gradient, row_distance,
                                                                          plot_line_find, pixel_value_cutoff)
        else:
            improved_gradient, detected_lines = find_lines.run_everything(img, gradient, row_distance, plot_line_find,
                                                                          pixel_value_cutoff)
        count += 1

        x1_value = []
        y1_value = []
        x2_value = []
        y2_value = []
        for line in detected_lines:
            start_index = line[0]
            end_index = line[1]
            x1_value.append(start_index[1])
            y1_value.append(start_index[0])
            x2_value.append(end_index[1])
            y2_value.append(end_index[0])

        #number_gap = []

        fig, axes = plt.subplots()
        axes.imshow(img)

        # cv2.imshow('img',img)

        for x, y, z, w in zip(x1_value, x2_value, y1_value, y2_value):
            x1, y1 = x, z
            x2, y2 = y, w
            num = int(np.hypot(x2 - x1, y2 - y1))
            if num > 10:
                x, y = np.linspace(x1, x2, num - 10), np.linspace(y1, y2, num - 10)
                # Extract the values alone the line using cubic interpolation
                zi = scipy.ndimage.map_coordinates(np.transpose(img), np.vstack((x, y)))

                # find local minimal index & value
                local_minimal_index = np.argwhere((zi < 0.2) & (zi != 0))
                gap = []
                if minimum_gap == 0:  # when minumum gap is 0
                    gap = local_minimal_index
                else:
                    for i in range(len(local_minimal_index)):
                        if i + minimum_gap <= len(local_minimal_index) - 1:
                            while (local_minimal_index[i + minimum_gap] - local_minimal_index[i] == minimum_gap):
                                for j in range(minimum_gap + 1):
                                    gap.append(local_minimal_index[i + j])
                                    number_gap.append(gap)
                                break
                print(np.array(gap))
                # number_gap.append(gap)
                gap = np.array(gap).astype('int64')
                # find local minimal value
                local_minimal_value = zi[gap]
                if abs(y1 - y2) <= abs(x1 - x2):
                    # get the y axis value on the picture,'gap' parameter is x axis value
                    y_value1 = ((y1 - y2) / (x1 - x2)) * (gap + x1) + ((y2 * x1 - y1 * x2) / (x1 - x2))
                    print(y_value1)

                    # Plot..
                    # axes[0].plot([x1,x2],[y1,y2],'r-')
                    #axes.axis('image')
                    axes.plot(x1 + gap, y_value1, 'r.')

                    # axes[1].plot(gap, local_minimal_value, 'r.')
                    # axes[1].plot(zi)

                elif abs(y1 - y2) > abs(x1 - x2):
                    # get the y axis value on the picture,'gap' parameter is x axis value
                    y_value = ((x2 - x1) / (y2 - y1)) * (y1 + gap) - ((y1 * x2 - y2 * x1) / (y2 - y1))
                    print(y_value)

                    # Plot..
                    # axes[0].plot([x1,x2],[y1,y2],'r-')
                    #axes.axis('image')
                    axes.plot(y_value, y1 + gap, 'r.')

                    # axes[1].plot(gap, local_minimal_value, 'r.')
                    # axes[1].plot(zi)
        axes.axis('off')
        #axes.img
        fig = plt.gcf()

        fig.set_size_inches(5.12/0.72,5.12/0.72) 
        plt.gca().xaxis.set_major_locator(plt.NullLocator())
        plt.gca().yaxis.set_major_locator(plt.NullLocator())
        plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
        plt.margins(0, 0)

        mpath=image.replace(replant_map_path + '/emergence_map/static/cutimg' ,replant_map_path + '/emergence_map/static/analysis')
        fig.savefig(mpath, transparent=True, pad_inches=0)

        # fig.savefig(replant_map_path + '/emergence_map/static/analysis/%d.png' % count, transparent=True, pad_inches=0)
        #fig.savefig('saved/%d.png' % count, bbox_inches='tight')
    gap_length = ((186.7 / img.shape[0] + 221.5 / img.shape[1]) / 32) * len(number_gap)
    print(len(number_gap))

    total_pixel = img.shape[0] * img.shape[1]
    proportion_gap = len(number_gap) / total_pixel

    return gap_length, proportion_gap

# find_gap(r'png_pict/*.png',7)
# print(find_gap(r'png_pict/*.png',7))


