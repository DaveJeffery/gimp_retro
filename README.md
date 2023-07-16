# gimp_retro

I documented my work on these plug-ins in a series of blog posts. I include these here, so they can be kept together with the code.

## Attribute Clash for The GIMP 

When I was browsing through [The GIMP plug-in registry](http://registry.gimp.org/), I came across a very interesting sounding filter called [zx spectrum filter](http://registry.gimp.org/node/7648) by [nitrofurano](http://nitrofurano.linuxkafe.com/) that promised it would imbue your images with all the glorious display limitations of the [Sinclair ZX Spectrum](http://en.wikipedia.org/wiki/ZX_Spectrum).

As it was written in [Python](http://www.python.org/) I thought I’d give it a go, but the plug-in refused to work. It took about an hour spuddling about to get the plug-in working. The main problem was incorrect indentation—Python is fussy about that. I also added some code to allow undoing and for the plug-in to appear in the `Filters` menu and then I could start playing!

![Replay Expo logo](/readme/r3play%20logo.png)

_Before_

![Replay Expo logo put through the Python ZX Spectrum filter](/readme/r3play_zx.png)

_After_

My fixed version of the plug-in can be downloaded from here, and adds the plug-in to `Filters -> Artistic -> ZX Spectrum`.

[GNU/Linux](http://www.gnu.org/) users need to set the Execute permission for the file `zxspectrum.py` before the [The GIMP](http://www.gimp.org/) will recognise it.

The plug-in is a very simple proof of concept and doesn’t work particularly well on small (as in ZX Spectrum sized) images as it just averages out the values in character squares, but it certainly creates some interesting effects on large images. 1024 x 768 seems to be the optimum size.

![Repton put through the Python ZX Spectrum filter](/readme/repton.png)

_Large images work best_

The next step would be to speed it up using the array library and to stop it from falling over nastily if you have an alpha channel on your image—if you do, you'll have to remove it to get the filter to work. 

## ZX Spectrum Filter Revisited
Well, a day is a long time in [Free Software](http://www.fsf.org/). Since I posted yesterday about the ZX Spectrum filter for The GIMP, I’ve had a lovely exchange of e-mails with the original author [nitrofurano](http://www.fsf.org/), I’ve improved the filter further and I’ve found out why it was written.


![A ZX Spectrum put through the Python ZX Spectrum filter](/readme/spectrum.jpg)

_Spectral Spectrum_

First things first, improving the filter. I had become rather rusty at working on filters for The GIMP but eventually everything came flooding back to me.

The first thing that helps when writing a Python filter in The GIMP is to run The GIMP from the command line in a terminal window. That way you get to see all the error messages the plug-in produces and are not working “blind”. You can also see the output of any print statements you add to help you debug.

The second thing I remembered was that you should use a symbolic link to the filter in The GIMP’s plug-in folder, so you can work somewhere more convenient than a hidden folder that’s several levels down.

![A ZX Spectrum +3 put through the Python ZX Spectrum filter](/readme/zxamstrad.jpg)

_Sugary Spectrum_

Once I’d got myself working sensibly I could have a look at improving the filter. The first thing I did was to speed the filter using [this technique](http://www.shallowsky.com/blog/gimp/pygimp-pixel-ops.html) described in [Akkana’s blog](http://shallowsky.com/blog/).  It cuts down on writing to the actual image, which is slow. Instead you copy the image to a byte array, work with that and then copy all the bytes back to the image when you have finished. Using Akkana’s technique had the added bonus of allowing the filter to be adapted easily work with either RGB or RGBA images.

However, the resulting changes didn’t seem to generate the desired increase in speed until I realised I had stupidly queried the image class’s size and width repeatedly instead of storing the values in variables. Once I did that the filter literally flew.

Nitrofurano (Paulo Silva) has been lovely and very encouraging as I’ve been hacking his lovely code to bits. He’s also as enthusiastic about free software as I am. I think it’s fantastic that people who have never met before can work on each other’s software, share ideas and get to know each other—the [GPL](http://www.gnu.org/licenses/gpl.html) really does work as advertised.

![A Sinclair pocket TV put through the Python ZX Spectrum filter](/readme/FTV1.jpg)

_Sinclair TV - thanks to Nitrofurano_

The reason the code was written originally was to be part of a very interesting project Paulo is working on to create "retro" vision web-cams. You can find out more about it [here](http://webcampictureson8bitcomputers.blogspot.com/).

## ZX Spectrum +3
Two days ago I blogged about getting nitrofurano's Python ZX Spectrum image filter for The GIMP working, and yesterday I blogged about speeding it up. However, Paulo e-mailed me just after I'd posted and said that the filter wasn't working as it should.

I had assumed that the filter just wasn't supposed to work on small images - such as ones at the ZX Spectrum resolution of 256 x 192. So if we took a 256 x 192 image like this:

Original image at 256 x 192

The best we could hope for would be this:

Put through The GIMP version of filter

However, Paulo pointed out that his sdlBasic version of the filter would produce this:

Put through sdlBasic version of filter

But having looked at the Python code for The GIMP filter he couldn't work out what was wrong. I was intrigued, and decided to have a look too.

Paulo thought that the problem probably lay in one of the loops that were processing the image, but I thought that was unlikely, particularly as he'd checked them so thoroughly against his sdlBasic original. The loops just contained maths, and maths tends to be pretty similar in any language.

Sure enough, the problem lay not in the maths but in the idiosyncratic weirdness of Python. I blame Eric Idle, personally.

The first problem was the way in which Paulo had dimensioned the lists (elderly gentlemen like me call them arrays) he used to work on character blocks. He'd done this:

```
r0 = [[0] * 8] * 8
g0 = [[0] * 8] * 8
b0 = [[0] * 8] * 8
```

Which is perfectly sensible, but the problem is in Python almost everything is copied by reference rather than by value. Numbers are copied by value, so [0] * 8 does create a list containing eight different zeros.

However lists are copied by reference so [[0] * 8] * 8 creates a list containing eight references to the same list. That means that any change made to one row of this multidimensional list affects all the other rows too - effectively cutting the resolution of the filter down to the character block level. This caused the blockiness.

To solve it we needed to do this:

```
r0 = [[None] * 8 for i in range(8)]
g0 = [[None] * 8 for i in range(8)]
b0 = [[None] * 8 for i in range(8)]`
```

What we are doing now is using a list comprehension to create a brand new list eight times, which is what we are after.

Another problem was that instead of referring to the nested lists using list[y][x] Paulo had used list[x][y]. So, for instance we had this:

```
b0[x2][y2] = str1[2]
g0[x2][y2] = str1[1]
r0[x2][y2] = str1[0]`
```

When we should have had this:

```
b0[y2][x2] = str1[2]
g0[y2][x2] = str1[1]
r0[y2][x2] = str1[0]`
```

It's very easy to do - in fact I've done it myself. Many times!

Regarding Python's weirdness, it more often works for you than against you and that's why I love the language. For instance, in Paulo's sdlBasic version of the filter he had to do this to swap two values:

```
if ikattr < paattr:
    tmpr = ikattr
    ikattr = paattr
    paattr = tmpr`
```

Whereas in Python you can use the far more "Pythonic":

```
if ikattr < paattr:
 ikattr, paattr = paattr, ikattr`
```
Anyway, now the filter was fixed and I could have some fun with some ZX Spectrum proportioned stupid rubbish. Here is Central News at 256 x 192:

It's 1982 again!

And here is a Tyne Tees/Channel 4 endcap - again at 256 x 192:

Unworthy of Half Man Half Biscuit

However, Paulo used it to produce something much grander:

by nitrofurano - Click to enlarge

This isn't the end of the story, unfortunately, as now I have to get the filter's Undo feature working - but tomorrow you'll be pleased to hear there will be something completely different.

The latest version of the ZX Spectrum image filter for The GIMP is available to download from here.
