
import sys
import io
import os
from os.path import dirname, abspath, isfile

from django.shortcuts import render,render_to_response
from django import forms
from django.http import HttpResponse,HttpResponseRedirect
from django.template import RequestContext
from .models import User,Uploaded_img

from PIL import Image

from django.shortcuts import redirect
from .forms import  RegisterForm, ImgForm
from django.contrib import auth
import scipy 
from scipy import fftpack
from scipy import interpolate
from .Analysis_algorithm import *
import numpy as np
import scipy.ndimage
import sys
from scipy.signal import find_peaks_cwt
import gdal

import math
import itertools
from random import randint
import operator
import time

import shutil
import json
import cv2

from .Analysis_algorithm.run import find_gap

# define abspath 
# for example /Users/shenghaoisyummy/comp5615_p19c/replant_map in my macbook
replant_map_path = abspath('.')


def demo(request):

    if request.method == 'POST':
        form = ImgForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('/emergence/demo')
    
    else:
        form = ImgForm()
    # print(find_gap('photo/0.png',7))
    return render(request, 'emergence_map.html', {
        'form': form
    })

def analysis(request):
    # get last uploaded png image name
    uploaded_img_name= str(Uploaded_img.objects.all().order_by('-id')[0].img)

    # get minimum_gap and sensitive value
    minimum_gap = int(request.POST['minimum_gap'])
    sensitive = float(request.POST['sensitive'])

    # get uploaded png image path
    last_uploaded_img_path = replant_map_path + '/'+ uploaded_img_name
    print(last_uploaded_img_path)

    # convert tif to png by using Imagemagick
    png_out_path = replant_map_path + "/emergence_map/static/png/convert.png"
    os.system('magick convert {} {}'.format(last_uploaded_img_path, png_out_path))

    #get length and width of tif image 
    length_width = getXY(last_uploaded_img_path)
    tif_length = length_width[0]
    tif_width = length_width[1]
    print(tif_length)
    print(tif_width)

    # cut image
    rows_cols = cut_pic(png_out_path)
    rows_cnt = rows_cols[0]
    cols_cnt = rows_cols[1]

    #analysis picture
    cut_img_src = replant_map_path + "/emergence_map/static/cutimg/*.png"
    result = find_gap(cut_img_src, minimum_gap, sensitive)
    gap_miss_length = result[0]
    miss_percentage = result[1]
    
    #merge picture
    merge_pic(replant_map_path, minimum_gap, sensitive, rows_cnt, cols_cnt)

    #cal yield loss
    yield_loss_result = yield_loss(gap_miss_length, miss_percentage, tif_length, tif_width)

    return HttpResponse(json.dumps({"gap_miss_length":gap_miss_length, "miss_percentage":miss_percentage, "yield_loss_result":yield_loss_result}), content_type="application/json")




def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/emergence/demo')
    else:
        form = RegisterForm()
    return render(request, 'register.html', context={'form': form})


def login(request):
    context = {}
    if request.method == "POST":
        user_name = request.POST.get("username","")
        pass_word = request.POST.get("password","")
        user = auth.authenticate(username=user_name, password=pass_word)
        if user is not None:
            auth.login(request, user)
            request.session['user_id'] = user.id
            return render(request, "emergence_map.html")
            context = {'login_err': 'Username or Password is wrong!'}
            return render(request, "login.html", context)
    elif request.method == "GET":
        return render(request, "login.html",{})

def cut_pic(path):
    k = 1 # picture count
    image = cv2.imread(path, -1)
    print(image)
    print(image.shape)
    rows, cols, = image.shape[0:2] # get row & col
    r1, r2 =  [0, 511]
    while r2 <= rows:
        c1, c2 = [0, 511]
        while c2 <= cols:
            # crop the picture
            img = image[r1 : r2 + 1, c1 : c2 + 1]
            # save the picture
            cv2.imwrite(replant_map_path + '/emergence_map/static/cutimg/' + str(k) + '.png', img)
            k, c1, c2 = [k + 1, c1 + 511, c2 + 511]# update the value
        r1, r2 = [r1 + 511, r2 + 511] # update the value
    print('finish')
    rows_cnt = int(rows/511)
    cols_cnt = int(cols/511)
    return rows_cnt, cols_cnt


def merge_pic(path,min_gap, sensitive,rows, cols):

    arr = ['' for i in range(36)]

    analysisPath= path + '/emergence_map/static/analysis/'

    for i in range(1,37):
        arr[i-1]= analysisPath +str(i)+'.png'

    toImage = Image.new('RGBA',(4272,4272))
    for i in range(rows * cols):
        fromImge = Image.open(arr[i])
        # loc = ((i % 2) * 200, (int(i/2) * 200))
        #loc = ((int(i/6) * 712), (i % 6) * 712)
        loc =((i%rows)*712, (int(i/cols)*712))
        print(loc)
        toImage.paste(fromImge, loc)

    toImage.save( path + '/emergence_map/static/merged/merged({})({}).png'.format(min_gap, sensitive))


def yield_loss(length_gap, missing_plants, length, width):
    total_length = length_gap / missing_plants

    rows = total_length / width
    row_spacing = length / rows
    print('row spacing '+str(row_spacing))

    row_spacing_lookup = [30 * 2.54*0.01, 36 * 2.54*0.01, 38 * 2.54*0.01, 40 * 2.54*0.01] 

    plants_per_acre_lookup = [34838, 29040, 27512, 26136]

    if row_spacing <= row_spacing_lookup[0]:
        plants_per_acre = plants_per_acre_lookup[0]
    elif row_spacing >= row_spacing_lookup[0]:
        plants_per_acre = plants_per_acre_lookup[len(plants_per_acre_lookup) - 1]
    else:
        for i in range(1, len(row_spacing_lookup)):
            if row_spacing > row_spacing_lookup[i]:
                next(i)
            else:
                plants_per_acre = plants_per_acre_lookup[i - 1] + (
                            plants_per_acre_lookup[i] - plants_per_acre_lookup[i - 1]) * (
                                              row_spacing - row_spacing_lookup[i - 1]) / (
                                              row_spacing_lookup[i] - row_spacing_lookup[i - 1])

    print('plants per acre'+str(plants_per_acre))

    # Assuming avg yield of 11.5ba/ha
    plants_per_acre_loss = plants_per_acre / plants_per_acre_lookup[0] * 11.5 * missing_plants

    return plants_per_acre_loss

def getXY(path):
    dataset = gdal.Open(path)

    adfGeoTransform =dataset.GetGeoTransform()

    # this is the point of top left corner

    x_left = adfGeoTransform[0]

    y_left = adfGeoTransform[3]

    nXSize = dataset.RasterXSize
    nYSize = dataset.RasterYSize

    # this is the point of bottom right corner
    x_right = adfGeoTransform[0] + nYSize* adfGeoTransform[1] + nXSize * adfGeoTransform[2]
    y_right = adfGeoTransform[3] + nYSize * adfGeoTransform[4] + nXSize * adfGeoTransform[5]

    # distance is roughly converted to meters by using scale at equator(1 degree =111319.49 meters)
    l_x = abs((x_left- x_right)*111319.49)
    l_y = abs((y_left- y_right)*111319.49)
    return l_x, l_y