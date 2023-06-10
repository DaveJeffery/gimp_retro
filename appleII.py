#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   AppleII (Colour) Image Filter - Apple II plugin for The GIMP.
#   Copyright (C) 2008, 2010  Paulo Silva <nitrofurano@gmail.com>
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

#   sdlbasic version Apple2hirespictFilterClust_1011061846.sdlbas
#   Speed enhancements based on blog post by Joao Bueno and Akkana Peck

from array import array

from gimpfu import *
gettext.install("gimp20-python", gimp.locale_directory, unicode=True)

def apple2(img, layer, halftone, pattern):

    gimp.context_push()
    img.undo_group_start()

    # Set up globals
    global width, height, height2 
    global dst_pxl, pxl_size

    # Width and height stored in variables for speed
    width = img.width 
    height = img.height

    # Create a new duplicate layer above the existing one
    position = pdb.gimp_image_get_layer_position(img, layer)
    new_layer = pdb.gimp_layer_copy(layer, False)
    pdb.gimp_image_add_layer(img, new_layer, position)

    # Resize the new layer to create two "buffer" scanlines
    height2 = height + 2
    pdb.gimp_layer_resize(new_layer, width, height2, 0, 0)

    # Create a copy of the image to write to
    dst_rgn = new_layer.get_pixel_rgn(0,            # x
                                      0,            # y
                                      width,        # w
                                      height2,      # h
                                      True,         # dirty
                                      False )       # shadow
    dst_pxl = array("B", dst_rgn[0:width, 0:height2])

    # Work out colour depth of image
    pxl_size = dst_rgn.bpp

    # Define two halftone clusters - tuples used for speed
    cluster = ((( 0,  6,  8, 14),
                ( 2, 12,  4, 10),
                ( 8, 14,  0,  6),
                ( 4, 10,  2, 12)),
               (( 0, 12,  3, 15),
                ( 8,  4, 11,  7),
                ( 2, 14,  1, 13),
                (10,  6,  9,  5)))

    # Define Apple II palette
    colours = ((0x00, 0x00, 0x00), (0x00, 0x00, 0xFF),
               (0xFF, 0x00, 0x00), (0xFF, 0x00, 0xFF),
               (0x00, 0xFF, 0x00), (0x00, 0xFF, 0xFF),
               (0xFF, 0xFF, 0x00), (0xFF, 0xFF, 0xFF))

    BLACK     = ink(0x00, 0x00, 0x00)
    BLUE      = ink(0x00, 0x00, 0xFF)
    RED       = ink(0xFF, 0x00, 0x00)
    MAGENTA   = ink(0xFF, 0x00, 0xFF)
    GREEN     = ink(0x00, 0xFF, 0x00)
    CYAN      = ink(0x00, 0xFF, 0xFF)
    YELLOW    = ink(0xFF, 0xFF, 0x00)
    WHITE     = ink(0xFF, 0xFF, 0xFF)

    # Define primary table
    prim_table = ((0, 1), (1, 2), (2, 2), (1, 0),
                  (2, 0), (1, 2), (2, 2), (3, 1))

    # Used on toolbar
    ipass = 1  

    if halftone:

        # Process images with halftones

        # Initialise progress bar
        gimp.progress_init("Apple II (Colour) Image Filter - Pass " + str(ipass))
        
        for y in range(0, height):

            # Update progress bar
            gimp.progress_init("Apple II (Colour) Image Filter - Pass " + str(ipass))
            gimp.progress_update(float(y) / height)

            for x in range(0, width):
                rgba = point(x, y)
                r, g, b = rgba[0], rgba[1], rgba[2]
         
                patgf = (((cluster[pattern][y % 4][x % 4] + 1) * 255) / 16)
                rpat = 1 if r > patgf else 0
                gpat = 1 if g > patgf else 0
                bpat = 1 if b > patgf else 0
                o4b = (bpat + (rpat * 2) + (gpat * 4)) % 8

                rgba = ink(colours[o4b][0], colours[o4b][1], colours[o4b][2])
                dot(x, y, rgba)          
        
        ipass += 1


    # Colour Correction

    # Set buffer line
    yed = height2 - 2

    # Initialise progress bar
    gimp.progress_init("Apple II Image Filter - Pass " + str(ipass))

    # Process image a scanline at a time
    for y in range(0, height):

        # Update progress bar
        gimp.progress_update(float(y) / height)

        # Use scanline to create proccessed buffer scanline (yed)

        for x1 in range(0, (width / 7) + 2):
            cflc = 0
            for x2 in range (0, 7):
                x = x2 + (x1 * 7)
                rgba = point(x, y)
                r, g, b = rgba[0], rgba[1], rgba[2]

                prim = (g / 128) * 4  + (r / 128) * 2 + (b / 128) 
                apv, cfl = prim_table[prim]
                if(x % 2) == 0: 
                    if apv in (0, 2):
                        dot(x, yed, BLACK)
                    if apv in (0, 1): 
                        dot(x + 1, yed, BLACK)

                cflc = cflc + cfl

            if cflc < 8:
                dot(x1, yed + 1, BLACK)

        # Clear scanline in actual image    
        blank_line(y, BLACK)

        for x in range(0, width, 2):
            rgba = point(x, yed)
            b = rgba[2]
            if b > 127:
                dot(x, y, MAGENTA)
        for x in range(1, width, 2):
            rgba = point(x, yed)
            b = rgba[2]
            if b > 127:
                dot(x, y, GREEN)
     
        for x in range(0, width - 2, 2):
            rgba1 = point(x, yed) 
            rgba2 = point(x + 2, yed)
            b1 = rgba1[2]
            b2 = rgba2[2]
            if (b1 > 127) and (b2 > 127):
                dot(x + 1, y, MAGENTA)

        for x in range(1, width - 2, 2):
            rgba1 = point(x, yed) 
            rgba2 = point(x + 2, yed)
            b1 = rgba1[2]
            b2 = rgba2[2]
            if (b1 > 127) and (b2 > 127):
                dot(x + 1, y, GREEN)

        for x in range(1, width - 1):
            rgba1 = point(x, yed) 
            rgba2 = point(x + 1, yed)
            b1 = rgba1[2]
            b2 = rgba2[2]
            if (b1 > 127) and (b2 > 127):
                dot(x, y, WHITE)
                dot(x + 1, y, WHITE)

        for x in range(1, width - 2):
            rgba1 = point(x, y) 
            rgba2 = point(x + 1, y)
            rgba3 = point(x + 2, y)
            white_pxl = array("B", "\xff" * pxl_size)
            if (rgba1 == white_pxl and 
                rgba3 == white_pxl and
                rgba2 != white_pxl):
                dot (x + 1, y, BLACK)

        for x1 in range(0, (width / 7) + 2):
            q = point(x1, yed + 1)
            q = q[2]
            for x2 in range(0, 7):
                n = point(x1 * 7 + x2, y)
                if(n == MAGENTA) and q > 128:
                    n = BLUE;
                if(n == GREEN) and q > 128:
                    n = ink(0xff,0x7f,0x00)
                dot(x1 * 7 + x2, y, n)

        blank_line(yed, WHITE)
        blank_line(yed + 1, WHITE)

    dst_rgn[0:width, 0:height2] = dst_pxl.tostring()

    new_layer.update(0, 0, width, height2)
    layer = pdb.gimp_image_merge_down(img, new_layer, CLIP_TO_IMAGE)

    img.undo_group_end()
    gimp.context_pop()

def ink(r, g, b):
    rgba = array("B", "\xff" * pxl_size)
    rgba[0], rgba[1], rgba[2] = r, g, b
    return rgba

def dot(x, y, rgba):
    global dst_pxl
    if x in range(width):
        dst_pos = (x + width * y) * pxl_size
        dst_pxl[dst_pos : dst_pos + pxl_size] = rgba


def point(x, y):
    if x in range(width):
        dst_pos = (x + width * y) * pxl_size
        return dst_pxl[dst_pos: dst_pos + pxl_size]
    else:
        return [0] * pxl_size

def blank_line(y, rgba):
    global dst_pxl
    line = array("B", rgba * width)
    dst_pos = (width * y) * pxl_size
    dst_pxl[dst_pos : dst_pos + (pxl_size * width)] = line

register("python-fu-apple2",
         N_("AppleII (Colour) Image Filter"),
         "",
         "Nitrofurano",
         "Nitrofurano",
         "2008",
         N_("_AppleII (Colour)"),
         # "RGB*, GRAY*",
         "RGB*",
         [(PF_IMAGE, "image", _("Input image"), None),
          (PF_DRAWABLE, "drawable", _("Input drawable"), None),
          (PF_TOGGLE, "halftone", _("Use halftones?"), True),
          (PF_RADIO, "pattern", _("Halftone cluster"), 0,
           ((_("One"), 0),
            (_("Two"), 1)))
          ],
         [],
         apple2, 
         menu="<Image>/Filters/Retro Computing",
         domain=("gimp20-python", gimp.locale_directory))
main()
