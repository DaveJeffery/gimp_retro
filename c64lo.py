#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   Commodore 64 (Low Res) Image Filter - Commodore 64 plugin for The GIMP.
#   Copyright (C) 2002, 2010  Paulo Silva <nitrofurano@gmail.com>
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

#   sdlbasic version c64_MpicDithWebcam_1006111020.sdlbas
#   Speed enhancements based on blog post by Joao Bueno and Akkana Peck

from array import array
from math import sqrt

from gimpfu import *
gettext.install("gimp20-python", gimp.locale_directory, unicode=True)


class ColourMap(object):
    def __init__(self, width=40, height=32, colours=16):
        self.width = width
        self.height = height        
        self.colours = colours
        self.pixmap = array("B", "\x00" * (width * height * colours))

    def add_pixel(self, x, y, c):
        self.pixmap[((x + self.width * y) * self.colours) + c] += 1

    def set_pixel(self, x, y, c, v):
        self.pixmap[((x + self.width * y) * self.colours) + c] = v

    def get_pixel(self, x, y, c):
        return self.pixmap[((x + self.width * y) * self.colours) + c]


def c64lo(img, layer):

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

    # Work out width and height on image in 8x8 characters and 4x8 cells
    w_chars = width / 8
    h_chars = height / 8
  
    # No pixels of each colour in each character
    cr = ColourMap(w_chars, h_chars, 16)

    # No of colours in each attribute
    mt = [[0] * w_chars for i in range(h_chars)]
    cmu = [0] * 16

    # Attribute map
    ag = ColourMap(w_chars, h_chars, 4)

    # Set up Commodore 64 palette
    colourid = (0x000, 0xFFF, 0x931, 0x5BD, 
                0x93C, 0x4A1, 0x32C, 0xBD3, 
                0x950, 0x440, 0xC64, 0x444, 
                0x777, 0x8E5, 0x75F, 0x999)

    iklv, colourid2 = [], []
    for u in colourid:
        rlv = u / 256    
        glv = (u / 16) & 15
        blv = u & 15
        iklv.append(((blv * 11) + (glv * 59) + (rlv * 30)) / 15)
        colourid2.append( ( int((rlv / 15.0) * 255),
                            int((glv / 15.0) * 255),
                            int((blv / 15.0) * 255) ) )
    iklv = tuple(iklv)
    colourid2 = tuple(colourid2)

    # Step 1 - Count number of pixels of each colour in each character square

    # Initialise progress bar
    gimp.progress_init("Commodore 64 (Low Res) - Step 1/8")

    for y1 in range(h_chars):

        # Update progress bar
        gimp.progress_update(y1 / float(h_chars))

        for x1 in range(w_chars):
            for y2 in range(8):
                for x2 in range(4):
                    x = x2 + (x1 * 4)
                    y = y2 + (y1 * 8)
                    dst_pos = ((x * 2) + width * y) * pxl_size
                    rgba = dst_pxl[dst_pos: dst_pos + pxl_size]
                    u = 0
                    dis = 1000
                    for i, c in enumerate(colourid):
                        rlv,  glv,  blv = c / 256, (c / 16) & 15, c & 15  
                        rlv2, glv2, blv2 = [j / 16 % 16 for j in rgba[0:3]]

                        rdist = abs(rlv - rlv2)
                        gdist = abs(glv - glv2)
                        bdist = abs(blv - blv2)

                        rgbdist = sqrt((rdist**2)+(gdist**2)+(bdist**2))

                        if rgbdist < dis:
                            dis = rgbdist
                            u = i
            
                    cr.add_pixel(x1, y1, u)

    # Step 2 - Count number of colours used in each character square

    # Initialise progress bar
    gimp.progress_init("Commodore 64 (Low Res) - Step 2/8")

    for y1 in range(h_chars):

        # Update progress bar
        gimp.progress_update(y1 / float(h_chars))

        for x1 in range(w_chars):
            es = 0
            for e in range(16):
                if cr.get_pixel(x1, y1, e) != 0: es += 1
            mt[y1][x1] = es

    # Step 3 - Work out most used colours in squares with more than 4 colours

    # Initialise progress bar
    gimp.progress_init("Commodore 64 (Low Res) - Step 3/8")

    for y1 in range(h_chars):

        # Update progress bar
        gimp.progress_update(y1 / float(h_chars))

        for x1 in range(w_chars):
            if mt[y1][x1] >= 4:
                for e in range(16):
                    if cr.get_pixel(x1, y1, e) > 0:
                        cmu[e] += 1

    # Step 4 - Determine most used colour in squares with more than 4 colours

    # Initialise progress bar
    gimp.progress_init("Commodore 64 (Low Res) - Step 4/8")

    curc, cnt = 15, 0
    for e in range(15, -1, -1):

        # Update progress bar
        gimp.progress_update(abs(e - 15) / 15.0)

        if cmu[e] > cnt:
            cnt = cmu[e]
            curc = e

    # Step 5 - Sets index 0 from each attribute with most used colour in 
    #          attribute with 4 colours or more

    # Initialise progress bar
    gimp.progress_init("Commodore 64 (Low Res) - Step 5/8")

    for y1 in range(h_chars):

        # Update progress bar
        gimp.progress_update(y1 / float(h_chars))

        for x1 in range(w_chars):
            for g in range(4):
                ag.set_pixel(x1, y1, g, 16)
            ag.set_pixel(x1, y1, 0, curc)
            cr.set_pixel(x1, y1, curc, 0)

    # Step 6 - Sets index from 1 to 3 from each attribute with remaining colours

    # Initialise progress bar
    gimp.progress_init("Commodore 64 (Low Res) - Step 6/8")

    for y1 in range(h_chars):

        # Update progress bar
        gimp.progress_update(y1 / float(h_chars))

        for x1 in range(w_chars):
            for g in range(1, 4):
                mx, ct = 0, 0
                for e in range(16):
                    if cr.get_pixel(x1, y1, e) > mx:
                        ct = e
                        mx = cr.get_pixel(x1, y1, e)
                cr.set_pixel(x1, y1, ct, 0)
                ag.set_pixel(x1, y1, g, ct)

    # Step 7 - Cleans value 16 generated from Step 5 (becomes background 0)

    # Initialise progress bar
    gimp.progress_init("Commodore 64 (Low Res) - Step 7/8")

    for y1 in range(h_chars):

        # Update progress bar
        gimp.progress_update(y1 / float(h_chars))

        for x1 in range(w_chars):
            for g in range(1, 4):
                if ag.get_pixel(x1, y1, g) > 15:
                    ag.set_pixel(x1, y1, g, ag.get_pixel(0, 0, 0)) 
            
    # Step 8 - Create final image

    # Initialise progress bar
    gimp.progress_init("Commodore 64 (Low Res) - Step 8/8")

    for y1 in range(h_chars):

        # Update progress bar
        gimp.progress_update(y1 / float(h_chars))

        for x1 in range(w_chars):
            kv = [iklv[ag.get_pixel(x1, y1, e)] for e in range(4)]
            for y2 in range(8):
                vac = 0
                for x2 in range(4):
                    x = (x1 * 4) + x2
                    y = (y1 * 8) + y2
                    dst_pos = ((x * 2) + width * y) * pxl_size
                    rgba = dst_pxl[dst_pos: dst_pos + pxl_size]
                    u, dis = 0, 1000
                    for i, c in enumerate(colourid):
                        rlv,  glv,  blv = c / 256, (c / 16) & 15, c & 15  
                        rlv2, glv2, blv2 = [j / 16 % 16 for j in rgba[0:3]]

                        rdist = abs(rlv - rlv2)
                        gdist = abs(glv - glv2)
                        bdist = abs(blv - blv2)

                        rgbdist = sqrt((rdist**2)+(gdist**2)+(bdist**2))

                        if rgbdist < dis:
                            dis = rgbdist
                            u = i
                    kvv = iklv[u]

                    diff, vap = 1000, 0
                    for e in range(4):
                        if diff > abs(kvv - kv[e]):
                            vap = e
                            diff = abs(kvv - kv[e])

                    rgba = array("B", "\xff" * pxl_size)
                    c = colourid2[ag.get_pixel(x1, y1, vap)]
                    rgba[0] = c[0]
                    rgba[1] = c[1]
                    rgba[2] = c[2]

                    dst_pos = ((x * 2) + width * y) * pxl_size
                    dst_pxl[dst_pos : dst_pos + pxl_size] = rgba                     

                    dst_pos = (((x * 2) + 1) + width * y) * pxl_size
                    dst_pxl[dst_pos : dst_pos + pxl_size] = rgba

                    vac = vac + (vap * (4 ** (3 - x2)))
                
                #pke[adrp] = vac

    # Copy the byte array back into the pixel region
    dst_rgn[0:width, 0:height] = dst_pxl.tostring()

    # Update the processed layer
    new_layer.update(0, 0, width, height)
    new_layer.resize((width / 8) * 8, (height / 8) * 8, 0, 0)

    # Merge processed layer into black layer
    black_layer = pdb.gimp_image_merge_down(img, new_layer, CLIP_TO_IMAGE)

    # Merge black layer into the original
    layer = pdb.gimp_image_merge_down(img, black_layer, CLIP_TO_IMAGE)

    img.undo_group_end()
    gimp.context_pop()

register("python-fu-c64lo",
         N_("Commodore 64 (Low Res) Image Filter"),
         "",
         "Nitrofurano",
         "Nitrofurano",
         "2008",
         N_("_Commodore 64 (Low Res)"),
         "RGB*",
         [(PF_IMAGE, "image", _("Input image"), None),
          (PF_DRAWABLE, "drawable", _("Input drawable"), None)
          ],
         [],
         c64lo, 
         menu="<Image>/Filters/Retro Computing",
         domain=("gimp20-python", gimp.locale_directory))
main()
