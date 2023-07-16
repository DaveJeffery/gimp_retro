# gimp_retro

I documented my work on these plug-ins in a series of blog posts. I include these here, so they can be kept together with the code.

## Attribute Clash for The GIMP 

When I was browsing through [The GIMP plug-in registry](http://registry.gimp.org/), I came across a very interesting sounding filter called [zx spectrum filter](http://registry.gimp.org/node/7648) by [nitrofurano](http://nitrofurano.linuxkafe.com/) that promised it would imbue your images with all the glorious display limitations of the [Sinclair ZX Spectrum](http://en.wikipedia.org/wiki/ZX_Spectrum).

As it was written in [Python](http://www.python.org/) I thought I’d give it a go, but the plug-in refused to work. It took about an hour spuddling about to get the plug-in working. The main problem was incorrect indentation—Python is fussy about that. I also added some code to allow undoing and for the plug-in to appear in the Filters menu and then I could start playing!

_Before_

_After_

My fixed version of the plug-in can be downloaded from here, and adds the plug-in to `Filters -> Artistic -> ZX Spectrum`.

[GNU/Linux](http://www.gnu.org/) users need to set the Execute permission for the file `zxspectrum.py` before the [The GIMP](http://www.gimp.org/) will recognise it.

The plug-in is a very simple proof of concept and doesn’t work particularly well on small (as in ZX Spectrum sized) images as it just averages out the values in character squares, but it certainly creates some interesting effects on large images. 1024 x 768 seems to be the optimum size.

_Large images work best_

The next step would be to speed it up using the array library and to stop it from falling over nastily if you have an alpha channel on your image - if you do, you'll have to remove it to get the filter to work. 
