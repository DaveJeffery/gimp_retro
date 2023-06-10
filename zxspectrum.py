#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   ZX Spectrum Image Filter - ZX Spectrum plugin for The GIMP.
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

#   sdlbasic version 0708072157 - from firstbasic version: 0201310133
#   Speed enhancements based on blog post by Joao Bueno and Akkana Peck

from array import array

from gimpfu import *
gettext.install("gimp20-python", gimp.locale_directory, unicode=True)

def zxspectrum(img, layer, hbedge, rgbsat, halftone):

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


    r0 = [[None] * 8 for i in range(8)]
    g0 = [[None] * 8 for i in range(8)]
    b0 = [[None] * 8 for i in range(8)]

    plte = (0x000000, 0xB40000, 0x0000B4, 0xB400B4,
            0x00B400, 0xB4B400, 0x00B4B4, 0xB4B4B4,
            0x000000, 0xFF0000, 0x0000FF, 0xFF00FF,
            0x00FF00, 0xFFFF00, 0x00FFFF, 0xFFFFFF)

    # Define two halftone clusters - tuples used for speed
    cluster = ((( 0,  6,  8, 14),
                ( 2, 12,  4, 10),
                ( 8, 14,  0,  6),
                ( 4, 10,  2, 12)),
               (( 0, 12,  3, 15),
                ( 8,  4, 11,  7),
                ( 2, 14,  1, 13),
                (10,  6,  9,  5)))

    #- halfbright attr edge -zx32=218, zx32fs=153 , realthing=180?
    hbedge = 180 

    # r, g and b saturation levels    
    rgrsp = rgbsat
    ggrsp = rgbsat
    bgrsp = rgbsat 

    # Initialise progress bar
    gimp.progress_init("ZX Spectrum Image Filter")

    # Process image one character row at a time
    for y1 in range(0, height / 8):

        # Update progress bar
        gimp.progress_update(float(y1) / (height / 8))

        # Process image one character square at a time
        for x1 in range(0, width / 8):
            
            # Find the value of each pixel of character square
            for y2 in range(0, 8):
                for x2 in range(0, 8):
                    y = y1 * 8 + y2
                    x = x1 * 8 + x2
		    
                    dst_pos = (x + width * y) * pxl_size
                    str1 = dst_pxl[dst_pos: dst_pos + pxl_size]
                    b0[y2][x2] = str1[2]
                    g0[y2][x2] = str1[1]
                    r0[y2][x2] = str1[0]

            # Find the mean r, g and b value of character square
            bi, ri, gi = 0, 0, 0
            for y2 in range(0, 8):
                for x2 in range(0, 8):
                    x = (x1 * 8) + x2
                    y = (y1 * 8) + y2
                    bi = bi + b0[y2][x2]
                    gi = gi + g0[y2][x2]
                    ri = ri + r0[y2][x2]

            b = bi / 64
            g = gi / 64
            r = ri / 64

	    # Work out if character square is "half bright"
            xrreg = 0
            hbrite = 0
            if (r < hbedge) and (g < hbedge) and (b < hbedge):
                hbrite = 1
            hbampl = 255 - (hbrite * (255 - hbedge))

            if b > hbampl / 2:
                b = hbampl - b
                xrreg = xrreg | 1

            if r > hbampl / 2:
                r = hbampl - r
                xrreg=xrreg | 2

            if g > hbampl / 2:
                g = hbampl - g
                xrreg = xrreg | 4

            halbr = (r * rgrsp) / 100
            halbg = (g * ggrsp) / 100
            halbb = (b * bgrsp) / 100

            vlik = 7
            if((r > halbb) and (g <= halbb)) or ((b <= halbr) and (g <= halbr)):
                vlik = 3
            if((g > halbb) and (r<=halbb)) or ((b <= halbg) and(r <= halbg)):
                vlik = 5
            if((g > halbr) and (b<=halbr)) or ((r<=halbg) and (b <= halbg)):
                vlik = 6
            if((r <= halbb) and(g<=halbb)):
                vlik = 1
            if((b <= halbr) and (g<=halbr)):
                vlik = 2
            if((b <= halbg) and (r <= halbg)):
                vlik = 4

            # Set ink, paper and bright attributes for character square
            brattr = 1 - hbrite
            ikattr = (vlik ^ xrreg) # ^ is used for xor
            paattr = xrreg

            if ikattr < paattr:
		ikattr, paattr = paattr, ikattr

            ikval = ikattr + ((ikattr & 6) / 2)
            paval = paattr + ((paattr & 6) / 2)

            lumik = (ikval * 255) / 10
            lumpa = (paval * 255) / 10

            if brattr < 1:
                lumik = (lumik * hbedge) / 255
                lumpa = (lumpa * hbedge) / 255

            dflum = lumik - lumpa

            for y2 in range (0, 8):
                for x2 in range (0, 8):
                    y = y1 * 8 + y2
                    x = x1 * 8 + x2
                    b = b0[y2][x2]
                    g = g0[y2][x2]
                    r = r0[y2][x2]
                    vlue = (b + (r * 3) + (g * 6)) / 10
                    patgf = ((cluster[halftone][y2 & 3][x2 & 3] 
                              + 1) * 255) / 16
                    varnd = ((patgf * dflum) / 255) + lumpa
                    ik = ikattr + (8 * brattr)
                    if varnd > vlue:
                        ik = paattr + (8 * brattr)

                    dst_pos = (x + width * y) * pxl_size
                    str2 = array("B", "\xff" * pxl_size)
                    str2[0] = plte[ik] & 0x0000FF
                    str2[1] = (plte[ik] & 0x00FF00) / 256
                    str2[2] = (plte[ik] & 0xFF0000) / 65536
                    dst_pxl[dst_pos : dst_pos + pxl_size] = str2
                
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

register("python-fu-zxspectrum",
         N_("ZX Spectrum Image Filter"),
         "",
         "Nitrofurano",
         "Nitrofurano",
         "2008",
         N_("_ZX Spectrum"),
         # "RGB*, GRAY*",
         "RGB*",
         [(PF_IMAGE, "image", _("Input image"), None),
          (PF_DRAWABLE, "drawable", _("Input drawable"), None),
          (PF_SLIDER, "hbedge", _("Bright attribute at"), 180, (0, 255, 1)),
          (PF_SLIDER, "rgbsat", _("RGB saturation point"), 30, (0, 255, 1)),
          (PF_RADIO, "halftone", _("Halftone cluster"), 0,
           ((_("One"), 0),
            (_("Two"), 1)))
         ],
         [],
         zxspectrum, 
         menu="<Image>/Filters/Retro Computing",
         domain=("gimp20-python", gimp.locale_directory))
main()
