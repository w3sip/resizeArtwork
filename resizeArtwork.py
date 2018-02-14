import sys
import os
import traceback
from mutagen.id3 import ID3, TIT2
from PIL import Image
import cStringIO
from StringIO import StringIO


#===========================================================================
def _getopts(argv):
    opts = {}
    # skip the script name
    if argv:
        argv = argv[1:]
    while argv:
        if argv[0][0] == '-':
            # Found a "-name value" pair or "-option"
            nextIsValue = len(argv) > 1 and argv[1][0] != '-'
            shiftBy = 2 if nextIsValue else 1
            opts[argv[0]] = argv[1] if nextIsValue else "" # Add key and value to the dictionary.
            argv = argv[shiftBy:]
        else:
            print "Unexpected parameter: " + argv[0]
            exit()

    return opts

#=========================================================================================
def _thumbFromBuffer(buf):
    im = Image.open(cStringIO.StringIO(buf))
    return im

#=========================================================================================
def _bufferFromThumb(image):
    output = StringIO()
    image.save(output, format="JPEG")
    contents = output.getvalue()
    output.close()
    return contents

#=========================================================================================
def resizeArtwork(filename, maxSize, dryRun):
    changed = False
    audio = ID3(filename)
    if audio is None:
        print "Failed to open ID3 from " + filename
        return

    for k in audio.keys():
        index = 0
        if k.startswith('APIC'):
            artwork = audio[k].data
            if artwork is None:
                print "Failed to load artwork for " + k
                continue
            # index = index + 1
            image = _thumbFromBuffer(artwork)
            w, h = image.size
            if w > maxSize or h > maxSize:
                resizeRatio = min(maxSize/float(w), maxSize/float(h))
                newSize = (int(w*resizeRatio), int(h*resizeRatio))
                print k + ": Resizing " + str(image.size) + "->" + str(newSize)
                image.thumbnail(newSize, Image.ANTIALIAS)
                audio[k].data = _bufferFromThumb(image)
                if not dryRun:
                    changed = True
            else:
                print k + ": Keeping size " + str(image.size)
            # jpgName = filename+"-" + str(index) + ".jpg"
            # image.save(jpgName)
    if changed:
        audio.save()

#===========================================================================
def _printUsage():
    print "Usage python ./resizeArtwork.py -f folder [-s maxSize] [-dry]"


#===========================================================================
def main():
    args = _getopts(sys.argv)
    folder = args.get("-f", None)
    maxSize = args.get("-s", 400)
    dryRun = args.get("-dry", None) != None
    if folder is None:
        _printUsage()
        exit()

    if not os.path.isdir(folder):
        print "Folder " + folder + " does not exist"
        exit()

    for subdir, dirs, files in os.walk(folder):
        for file in files:
            _, ext = os.path.splitext(file)
            if ext.lower() == ".mp3":
                full = os.path.join(folder, subdir, file)
                print "Processing " + full
                try:
                    resizeArtwork(full, maxSize, dryRun)
                except:
                    print "Exception while processing " + full + ":\n" + traceback.format_exc()

    print "All done!"


#===========================================================================
if __name__ == "__main__":
    main()