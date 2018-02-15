import sys
import os
import traceback
from mutagen.id3 import ID3, TIT2, APIC
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
def resizeArtwork(filename, maxSize, fileImgFilename, dryRun):
    changed = False
    filename = "\\\\?\\" + os.path.normpath(filename)
    audio = ID3(filename)
    if audio is None:
        print "Failed to open ID3 from " + filename
        return False

    # See if we need to apply an entirely new thumb
    newAPIC = None
    try:
        if fileImgFilename is not None:
            fileImgPath = os.path.join(os.path.dirname(filename), fileImgFilename)
            if os.path.isfile(fileImgPath):
                imagedata = open(fileImgPath, 'rb').read()
                image = _thumbFromBuffer(imagedata)
                w, h = image.size
                if w > maxSize or h > maxSize:
                    resizeRatio = min(maxSize/float(w), maxSize/float(h))
                    newSize = (int(w*resizeRatio), int(h*resizeRatio))
                    print "Resizing " + str(image.size) + "->" + str(newSize)
                    image.thumbnail(newSize, Image.ANTIALIAS)
                newAPIC = APIC(3, 'image/jpeg', 3, 'Front cover', _bufferFromThumb(image))
                print "Using image from " + fileImgPath
    except:
        print "Exception while trying to read new thumb: " + ":\n" + traceback.format_exc()
        pass

    for k in audio.keys():
        index = 0
        if k.startswith('APIC'):
            # If a substitution image is provided and exists, delete all other image tags
            if newAPIC is not None:
                del audio[k]
                changed = True
                continue

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
                changed = True
            else:
                print k + ": Keeping size " + str(image.size)
            # jpgName = filename+"-" + str(index) + ".jpg"
            # image.save(jpgName)

    if newAPIC is not None:
        audio['APIC'] = newAPIC
        changed = True


    if changed and not dryRun:
        audio.save()

    return True

#===========================================================================
def _printUsage():
    print "Usage python ./resizeArtwork.py -f folder [-s maxSize] [-cover coverFileName.jpg] [-dry]"


#===========================================================================
def main():
    args = _getopts(sys.argv)
    folder = args.get("-f", None)
    maxSize = int(args.get("-s", 400))
    fileImg = args.get("-cover", None)
    dryRun = args.get("-dry", None) != None
    if folder is None:
        _printUsage()
        exit()

    if not os.path.isdir(folder):
        print "Folder " + folder + " does not exist"
        exit()

    failed = []
    for subdir, dirs, files in os.walk(folder):
        for file in files:
            _, ext = os.path.splitext(file)
            if ext.lower() == ".mp3":
                full = os.path.join(folder, subdir, file)
                print "Processing " + full
                try:
                    if not resizeArtwork(full, maxSize, fileImg, dryRun):
                        failed.append(full)
                except:
                    print "Exception while processing " + full + ":\n" + traceback.format_exc()
                    failed.append(full)

    print "All done! Failed items:"
    for item in failed:
        print "    " + item


#===========================================================================
if __name__ == "__main__":
    main()