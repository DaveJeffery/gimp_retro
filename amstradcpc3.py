#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   Amstrad CPC (Mode 3) Image Filter - Amstrad CPC plugin for The GIMP.
#   Copyright (C) 2008, 2010  Paulo Silva 
#   Copyright (C) 2008  Daniel Carvalho
#   Copyright (C) 2010  Dave Jeffery <kecskebak.blog@gmail.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

#   Speed enhancements based on blog post by Joao Bueno and Akkana Peck

from array import array

from gimpfu import *
gettext.install("gimp20-python", gimp.locale_directory, unicode=True)

def no_dither(dst_pxl, colours, width, height, pxl_size,
              strength, serpent, dither):

    for y in range(0, height):

        # Update progress bar
        gimp.progress_update(float(y) / height)

        for x in range(0, width, 2):

            # find value of old_pixel 
            dst_pos = (x + width * y) * pxl_size
            rgbo = dst_pxl[dst_pos: dst_pos + pxl_size]
            r, g, b = rgbo[0], rgbo[1], rgbo[2]

            # find closest match in palette
            cd = []
            for c in colours:
                cd.append(((r - c[0]) ** 2 + 
                           (g - c[1]) ** 2 + 
                           (b - c[2]) ** 2) ** 0.5)
            rgbp = colours[cd.index(min(cd))]

            # ink(rgbn); dot(x, y); dot(x + 1, y)
            rgbn = array("B", "\xff" * pxl_size)
            rgbn[0] = rgbp[0]
            rgbn[1] = rgbp[1]
            rgbn[2] = rgbp[2]       

            try:
                # Write pixel pair to image
                dst_pos = (x + width * y) * pxl_size
                dst_pxl[dst_pos : dst_pos + pxl_size] = rgbn
                dst_pxl[dst_pos + pxl_size : dst_pos + (2 * pxl_size)] = rgbn
            
            except IndexError:
                # a pixel doesn't exist
                pass


def error_diffusion(dst_pxl, colours, width, height, pxl_size,
                    strength, serpent, dither):

    # Define store for filter matrices
    matrix = []

    # False Floyd-Steinberg dithering filter matrix
    matrix.append([[0, 0, 3], 
                   [0, 3, 2]])

    # Floyd-Steinberg dithering filter matrix
    matrix.append([[0, 0, 7], 
                   [3, 5, 1]])

    # Stucki dithering filter matrix  
    matrix.append([[0, 0, 0, 8, 4], 
                   [2, 4, 8, 4, 2],
                   [1, 2, 4, 2, 1]])

    # Burkes dithering filter matrix  
    matrix.append([[0, 0, 0, 8, 4], 
                   [2, 4, 8, 4, 2]])

    # Jarvis, Judice & Ninke dithering filter matrix  
    matrix.append([[0, 0, 0, 7, 5], 
                   [3, 5, 7, 5, 3],
                   [1, 3, 5, 3, 1]])

    # Sierra3 dithering filter matrix  
    matrix.append([[0, 0, 0, 5, 3], 
                   [2, 4, 5, 4, 2],
                   [0, 2, 3, 2, 0]])

    # Sierra2 dithering filter matrix  
    matrix.append([[0, 0, 0, 4, 3], 
                   [1, 2, 3, 2, 1]])

    # Sierra-2-4A dithering filter matrix
    matrix.append([[0, 0, 2], 
                   [0, 1, 1]])

    # Fan dithering filter matrix
    matrix.append([[0, 0, 0, 7, 0], 
                   [1, 3, 5, 0, 0]])

    # Shiau-Fan dithering filter matrix  
    matrix.append([[0, 0, 0, 2, 0], 
                   [8, 8, 4, 0, 0]])

    # Filter to use
    img_filter = matrix[dither]
    
    # Work out filter matrix width and height
    fw, fh = len(img_filter[0]), len(img_filter)

    # Define matrix target
    tx, ty = fw / 2, 0

    # Work out divisor by summing matrix members
    fd = 0.0
    for row in img_filter: fd += sum(row)

    # For speed, do division in advance and convert matrix to tuple
    for dy in range(fh):
        for dx in range(fw):
            try:
                img_filter[dy][dx] = ((img_filter[dy][dx] / fd) 
                                      * (strength / 100))
            except ZeroDivisionError:
                 img_filter[dy][dx] = 0
        img_filter[dy] = tuple(img_filter[dy])
    img_filter = tuple(img_filter) 

    # Width of image rounded to nearest two pixels
    rw = width - (width % 2)

    for y in range(0, height):

        # Update progress bar
        gimp.progress_update(float(y) / height)

        for x in range(0, width, 2):

            # serpentine parsing
            sx = rw - (x + 2) if serpent and y % 2 else x

            # find value of old_pixel 
            dst_pos = (sx + width * y) * pxl_size
            rgbo = dst_pxl[dst_pos: dst_pos + pxl_size]

            # find closest palette colour
            r, g, b = rgbo[0], rgbo[1], rgbo[2]
            cd = []
            for c in colours:
                cd.append(((r - c[0]) ** 2 + 
                           (g - c[1]) ** 2 + 
                           (b - c[2]) ** 2) ** 0.5)
            rgbn = colours[cd.index(min(cd))]

            # find quantisation error
            qer = rgbo[0] - rgbn[0]
            qeg = rgbo[1] - rgbn[1]
            qeb = rgbo[2] - rgbn[2]

            # add quantisation error to surrounding pixels
            for qy in range(fh):

                # work out y of pixel to process
                py = y + (qy - ty)

                for qx in range(fw):

                    # serpentine parsing
                    sqx = (fw - qx) - 1 if serpent and y % 2 else qx

                    # work out x of pixel to process
                    px = sx + (qx - tx) * 2
                    
                    try:
                        # get rgb value of pixel
                        dst_pos = (px + width * py) * pxl_size
                        rgbq = dst_pxl[dst_pos: dst_pos + pxl_size]
                        r, g, b = rgbq[0], rgbq[1], rgbq[2]

                    except IndexError:
                        # pixel doesn't exist!
                        pass

                    else:                           
                        # add quantisation error
                        dc = img_filter[qy][sqx]
                        r += dc * qer
                        g += dc * qeg
                        b += dc * qeb

                        # clip numbers to range 0 <= n <= 255
                        r = r if r > 0 else 0
                        r = r if r < 255 else 255 
                        g = g if g > 0 else 0
                        g = g if g < 255 else 255
                        b = b if b > 0 else 0
                        b = b if b < 255 else 255

                        rgbq[0] = int(r)
                        rgbq[1] = int(g) 
                        rgbq[2] = int(b) 

                        dst_pxl[dst_pos : dst_pos + pxl_size] = rgbq

            # ink(rgbn); dot(x, y); dot(x + 1, y)
            rgba = array("B", "\xff" * pxl_size)
            rgba[0] = rgbn[0]
            rgba[1] = rgbn[1]
            rgba[2] = rgbn[2]            

            try:
                # Write pixel pair to image
                dst_pos = (sx + width * y) * pxl_size
                dst_pxl[dst_pos : dst_pos + pxl_size] = rgba
                dst_pxl[dst_pos + pxl_size : dst_pos + (2 * pxl_size)] = rgba
            
            except IndexError:
                # a pixel doesn't exist
                pass


def ordered_dither(dst_pxl, colours, width, height, pxl_size,
                   strength, serpent, dither):

    # Define store for threshold maps
    threshold_map = []

    # 2 x 2
    threshold_map.append([[1, 3], 
                          [4, 2]])

    # 3 x 3
    threshold_map.append([[3, 7, 4],
                          [6, 1, 9], 
                          [2, 8, 5]])

    # 4 x 4
    threshold_map.append([[ 1,  9,  3, 11],
                          [13,  5, 15,  7],
                          [ 4, 12,  2, 10], 
                          [16,  8, 14,  6]])
    # 8 x 8
    threshold_map.append([[ 1, 49, 13, 61,  4, 52, 16, 64], 
                          [33, 17, 45, 29, 36, 20, 48, 32],
                          [ 9, 57,  5, 53, 12, 60,  8, 56],
                          [41, 25, 37, 21, 44, 28, 40, 24],
                          [ 3, 51, 15, 63,  2, 50, 14, 62],
                          [35, 19, 47, 31, 34, 18, 46, 30],
                          [11, 59,  7, 55, 10, 58,  6, 54],
                          [43, 27, 39, 23, 42, 26, 38, 22]])

    # Division threshold for each threshold map
    threshold_div = ( 5.0, 10.0, 17.0, 65.0)

     # Filter to use
    img_filter = threshold_map[dither]
    
    # Work out filter matrix width and height
    fw, fh = len(img_filter[0]), len(img_filter)

    # Work out divisor by summing matrix members
    fd = threshold_div[dither]

    # For speed, do division in advance and convert matrix to tuple
    for dy in range(fh):
        for dx in range(fw):
            try:
                img_filter[dy][dx] = ((img_filter[dy][dx] / fd) * 255) - 128
            except ZeroDivisionError:
                img_filter[dy][dx] = 0
        img_filter[dy] = tuple(img_filter[dy])
    img_filter = tuple(img_filter)

    for y in range(0, height):

        # Update progress bar
        gimp.progress_update(float(y) / height)

        for x in range(0, width, 2):

            # find value of old_pixel 
            dst_pos = (x + width * y) * pxl_size
            rgba = dst_pxl[dst_pos: dst_pos + pxl_size]

            # Add threshold map to pixel
            r, g, b = rgba[0], rgba[1], rgba[2]

            f = img_filter[y % fh][(x / 2) % fw] * (strength / 100)
            r, g, b = r + f, g + f, b + f

            cd = []
            for c in colours:
                cd.append(((r - c[0]) ** 2 + 
                           (g - c[1]) ** 2 + 
                           (b - c[2]) ** 2) ** 0.5)
            rgbo = colours[cd.index(min(cd))]

            # ink(rgbn); dot(x, y); dot(x + 1, y)
            rgbn = array("B", "\xff" * pxl_size)
            rgbn[0] = rgbo[0]
            rgbn[1] = rgbo[1]
            rgbn[2] = rgbo[2]       

            try:
                # Write pixel pair to image
                dst_pos = (x + width * y) * pxl_size
                dst_pxl[dst_pos : dst_pos + pxl_size] = rgbn
                dst_pxl[dst_pos + pxl_size : dst_pos + (2 * pxl_size)] = rgbn
            
            except IndexError:
                # a pixel doesn't exist
                pass

def calculate_palette(dst_pxl, width, height, pxl_size,
                      full_palette, plt_size):

    # Initialise progress bar
    gimp.progress_init("Calculating Palette")
    
    swatches = len(full_palette)
    counter = [0] * swatches
    colours = [] 

    for y in range(0, height):

        # Update progress bar
        gimp.progress_update(float(y) / height)

        for x in range(0, width, 2):

            # find value of old_pixel 
            dst_pos = (x + width * y) * pxl_size
            rgbo = dst_pxl[dst_pos: dst_pos + pxl_size]
            r, g, b = rgbo[0], rgbo[1], rgbo[2]

            # find closest match in full palette
            cd = []
            for c in full_palette:
                cd.append(((r - c[0]) ** 2 + 
                           (g - c[1]) ** 2 + 
                           (b - c[2]) ** 2) ** 0.5)

            # increment counter for that colour
            counter[cd.index(min(cd))] += 1

    # add most used colours to restricted palette
    for j in range(plt_size): 
        c = counter.index(max(counter))
        colours.append(full_palette[c])
        counter[c] = 0

    return tuple(colours)


def amstradcpc3(img, layer, strength, serpent, dither):

    # Store the GIMP's settings so they can be restored when we're finished
    gimp.context_push()

    # Make all the operations in this filter undo in one group
    img.undo_group_start()

    # Width and height stored in variables for speed
    width = img.width 
    height = img.height

    # Create a new duplicate layer above the existing one
    position = pdb.gimp_image_get_layer_position(img, layer)
    new_layer = pdb.gimp_layer_copy(layer, False)
    pdb.gimp_image_add_layer(img, new_layer, position)

    # Specify the new layer as the pixel region we'll work with
    dst_rgn = new_layer.get_pixel_rgn(0,            # x
                                      0,            # y
                                      width,        # w
                                      height,       # h
                                      True,         # dirty
                                      False )       # shadow
    
    # Store the copy of the pixel region in a byte array for speed
    dst_pxl = array("B", dst_rgn[0:width, 0:height])

    # Work out colour depth of image
    pxl_size = dst_rgn.bpp
           
    # Define full palette
    full_palette = ((0x00, 0x00, 0x00), (0x00, 0x00, 0x7F),
                    (0x00, 0x00, 0xFF), (0x7F, 0x00, 0x00),
                    (0x7F, 0x00, 0x7F), (0x7F, 0x00, 0xFF),
                    (0xFF, 0x00, 0x00), (0xFF, 0x00, 0x7F),
                    (0xFF, 0x00, 0xFF), (0x00, 0x7F, 0x00),
                    (0x00, 0x7F, 0x7F), (0x00, 0x7F, 0xFF),
                    (0x00, 0x7F, 0xFF), (0x7F, 0x7F, 0x00),
                    (0x7F, 0x7F, 0x7F), (0x7F, 0x7F, 0xFF),
                    (0xFF, 0x7F, 0x00), (0xFF, 0x7F, 0x7F),
                    (0xFF, 0x7F, 0xFF), (0x00, 0xFF, 0x00),
                    (0x00, 0xFF, 0x7F), (0x00, 0xFF, 0xFF),
                    (0x7F, 0xFF, 0x00), (0x7F, 0xFF, 0x7F),
                    (0x7F, 0xFF, 0xFF), (0xFF, 0xFF, 0x00),
                    (0xFF, 0xFF, 0x7F), (0xFF, 0xFF, 0xFF))

    # Calculate restricted palette
    colours = calculate_palette(dst_pxl, width, height, pxl_size,
                                full_palette, 4)

    # Initialise progress bar
    gimp.progress_init("Amstrad CPC (Mode 3) Image Filter")

    # Choose dithering technique
    if dither in range(1, 5):
        ordered_dither(dst_pxl, colours, width, height, pxl_size,
                       strength, serpent, dither - 1)
    elif dither in range(5, 15):
        error_diffusion(dst_pxl, colours, width, height, pxl_size,
                        strength, serpent, dither - 5)        
    else:
        no_dither(dst_pxl, colours, width, height, pxl_size,
                  strength, serpent, dither)

    # Copy the byte array back into the pixel region
    dst_rgn[0:width, 0:height] = dst_pxl.tostring()

    # Update the layer and merge it down into the original
    new_layer.update(0, 0, width, height)
    layer = pdb.gimp_image_merge_down(img, new_layer, CLIP_TO_IMAGE)

    img.undo_group_end()
    gimp.context_pop()

register("python-fu-amstradcpc3",
         N_("Amstrad CPC (Mode 3) Image Filter"),
         "",
         "Nitrofurano",
         "Nitrofurano",
         "2008",
         N_("_Amstrad CPC (Mode 3)"),
         "RGB*",
         [(PF_IMAGE, "image", _("Input image"), None),
          (PF_DRAWABLE, "drawable", _("Input drawable"), None),
          (PF_SLIDER, "strength", _("Filter Strength"), 100, (0, 100, 1)),
          (PF_TOGGLE, "serpent", _("Serpentine parsing?"), True),
          (PF_RADIO, "dither", _("Image Dither Filter"), 0,
           ((_("None"), 0),
            (_("Ordered 2x2"), 1),
            (_("Ordered 3x3"), 2),
            (_("Ordered 4x4"), 3),
            (_("Ordered 8x8"), 4),
            (_("False Floyd-Steinberg"), 5),
            (_("Floyd-Steinberg"), 6),
            (_("Stucki"), 7),
            (_("Burkes"), 8),
            (_("Jarvis, Judice & Ninke"), 9),
            (_("Sierra3"), 10),
            (_("Sierra2"), 11),
            (_("Sierra-2-4A"), 12),
            (_("Fan"), 13),
            (_("Shiau-Fan"), 14)))
         ],
         [],
         amstradcpc3, 
         menu="<Image>/Filters/Retro Computing",
         domain=("gimp20-python", gimp.locale_directory))
main()
