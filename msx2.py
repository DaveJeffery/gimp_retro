#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   MSX1 (Screen2) Image Filter - MSX plugin for The GIMP.
#   Copyright (C) 2008  Paulo Silva <nitrofurano@gmail.com>
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

#   sdlbasic version MsxScr02c8x1pictFilter0708101505.sdlbas
#   from firstbasic version: 010808
#   Speed enhancements based on blog post by Joao Bueno and Akkana Peck

from math import sqrt
from array import array

from gimpfu import *
gettext.install("gimp20-python", gimp.locale_directory, unicode=True)

def msx2(img, layer, halftone):

    # Store the GIMP's settings so they can be restored when we're finished
    gimp.context_push()

    # Make all the operations in this filter undo in one group
    img.undo_group_start()

    # Set up constants
    width = img.width
    height = img.height

    # Create a new black layer above the existing one
    position = pdb.gimp_image_get_layer_position(img, layer)
    gimp.set_background(0, 0, 0)
    black_layer = gimp.Layer(img, "Black Layer", width, height, 
                             RGB_IMAGE, 100, NORMAL_MODE)
    pdb.gimp_image_add_layer(img, black_layer, position)

    # Create a copy of the image as a new layer above the black one
    position = pdb.gimp_image_get_layer_position(img, black_layer)
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

    # Store for R,G,B in character square
    r0 = [[0] * 8 for i in range(8)]
    g0 = [[0] * 8 for i in range(8)]
    b0 = [[0] * 8 for i in range(8)]

    # Define two halftone clusters - tuples used for speed
    cluster = ((( 0,  6,  8, 14),
                ( 2, 12,  4, 10),
                ( 8, 14,  0,  6),
                ( 4, 10,  2, 12)),
               (( 0, 12,  3, 15),
                ( 8,  4, 11,  7),
                ( 2, 14,  1, 13),
                (10,  6,  9,  5)))

    # Defines greyscale values of MSX1 palette
    grpltlev = (   0,  237,  314,  395, 400, 
                 448,  504,  564,  600, 701,
                 714,  765,  778,  825, 1000)
    grpltlev = tuple([(grd * 255)/1000 for grd in grpltlev])

    # Colour palette
    npaletr = (0, 1, 5, 1, 7, 2, 6, 1, 7, 2, 5, 3, 6, 6, 7)
    npaletg = (0, 1, 1, 4, 1, 3, 2, 6, 3, 6, 5, 7, 6, 6, 7)
    npaletb = (0, 7, 1, 1, 1, 7, 5, 1, 3, 7, 5, 3, 1, 4, 7)

    npaletr = tuple([(rr * 255) / 7 for rr in npaletr])
    npaletg = tuple([(rg * 255) / 7 for rg in npaletg])
    npaletb = tuple([(rb * 255) / 7 for rb in npaletb])

    # Round screen extent to character blocks
    xmax, ymax = width, height
    xmaxo, ymaxo = xmax / 8, ymax / 8

    # Copy palette
    rfromat = npaletr[:]
    gfromat = npaletg[:]
    bfromat = npaletb[:]

    # Initialise progress bar
    gimp.progress_init("MSX1 (Screen2) Image Filter")

    # Process image one character row at a time
    for y1 in range(0, ymaxo):

        # Update progress bar
        gimp.progress_update(float(y1) / ymaxo)

        # Process image one character square at a time
        for x1 in range(0, xmaxo):

            # Store value of each pixel in character square
            for y2 in range(0, 8):
                for x2 in range (0, 8):
                    y = y1 * 8 + y2
                    x = x1 * 8 + x2

                    dst_pos = (x + width * y) * pxl_size
                    rgba = dst_pxl[dst_pos: dst_pos + pxl_size]
                    b0[y2][x2] = rgba[2]
                    g0[y2][x2] = rgba[1]
                    r0[y2][x2] = rgba[0]

            # Find colour attributes for each row of 8 pixels
            for y2 in range(0, 8):
                y = y1 * 8 + y2

                # Read each pixel in row
                bi, ri, gi = 0, 0, 0
                for x2 in range(0, 8):
                    x = (x1 * 8) + x2
                    iy = (ymax - 1) - y
                    bi = bi + b0[y2][x2]
                    gi = gi + g0[y2][x2]
                    ri = ri + r0[y2][x2]

                # Find average RGB values of row
                b, g, r = bi / 8, gi / 8, ri / 8

                # Work out MSX ink and paper values of row
                dbuf = 1000
                paattr = 0
                ikattr = 14
                pa = 0
                ik = 14   
                lumik = 0
                lumpa = 1

                # Cycle through all possible ink and paper combinations
                for pa in range(0, 14):
                    for ik in range (pa + 1, 15):
                        # Look-up ink and paper values as greys
                        graypa = grpltlev[pa]
                        grayik = grpltlev[ik]

                        # Convert current row's average RGB to grey
                        grayrgb = (((b * 11) + (r * 30) + (g * 59)) / 100)

                        # If the current row's average grey tone is lighter  
                        # than the paper's grey tone but darker than the ink's
                        # grey tone...
                        if (grayrgb >= graypa) and (grayrgb < grayik):
                            ikincid = ((grayrgb - graypa) 
                                       * 255) / (grayik - graypa)
                            rfikinc=((rfromat[ik] * ikincid) + 
                                     (rfromat[pa] * (255 - ikincid))) / 255
                            gfikinc=((gfromat[ik] * ikincid) + 
                                     (gfromat[pa] * (255 - ikincid))) / 255
                            bfikinc=((bfromat[ik] * ikincid) + 
                                     (bfromat[pa] * (255 - ikincid))) / 255
                            rdist = abs(rfikinc - r)
                            gdist = abs(gfikinc - g)
                            bdist = abs(bfikinc - b)                         
                            rgbdist = sqrt((rdist ** 2) + 
                                           (gdist ** 2) + 
                                           (bdist ** 2))
                            if rgbdist <= dbuf: 
                                dbuf = rgbdist
                                paattr = pa
                                ikattr = ik
                                lumik = grayik
                                lumpa = graypa

                # memory block 4 reading as grayscale for screen 2
                dflum = lumik - lumpa
                pkvar = 0
                for x2 in range(0, 8):
                    x = x1 * 8 + x2
                    b = b0[y2][x2]
                    g = g0[y2][x2]
                    r = r0[y2][x2]
                    vlue=(((b * 11) + (r * 30) + (g * 59)) / 100)
                    patgf1 = x2 % 4
                    patgf2 = y % 4
                    patgf = (((cluster[halftone][patgf2][patgf1] + 1) 
                              * 255) / 16)
                    varnd = ((patgf * dflum) / 255) + lumpa
                    ik = ikattr
                    if varnd > vlue:
                        ik = paattr
                    dst_pos = (x + width * y) * pxl_size
                    rgba = array("B", "\xff" * pxl_size)
                    rgba[0] = npaletr[ik]
                    rgba[1] = npaletg[ik]
                    rgba[2] = npaletb[ik]
                    dst_pxl[dst_pos : dst_pos + pxl_size] = rgba

    # Copy the byte array back into the pixel region
    dst_rgn[0:width, 0:height] = dst_pxl.tostring()

    # Update the processed layer
    new_layer.update(0, 0, width, height)
    new_layer.resize(xmaxo * 8, ymaxo * 8, 0, 0)

    # Merge processed layer into black layer
    black_layer = pdb.gimp_image_merge_down(img, new_layer, CLIP_TO_IMAGE)

    # Merge black layer into the original
    layer = pdb.gimp_image_merge_down(img, black_layer, CLIP_TO_IMAGE)

    img.undo_group_end()
    gimp.context_pop()

register("python-fu-msx1scr2",
         N_("MSX1 (Screen2) Image Filter"),
         "",
         "Nitrofurano",
         "Nitrofurano",
         "2008",
         N_("_MSX1 (Screen2)"),
         # "RGB*, GRAY*",
         "RGB*",
         [(PF_IMAGE, "image", _("Input image"), None),
          (PF_DRAWABLE, "drawable", _("Input drawable"), None),
          (PF_RADIO, "halftone", _("Halftone cluster"), 0,
           ((_("One"), 0),
            (_("Two"), 1)))
         ],
         [],
         msx2, 
         menu="<Image>/Filters/Retro Computing",
         domain=("gimp20-python", gimp.locale_directory))
main()
