import os
from PIL import Image

from compressHMP import compressImage
from decompressHMP import decompressImage

extensionDict = Image.registered_extensions()
validExtensions = []
for key in extensionDict:
    validExtensions.append(key)
validExtensions = tuple(validExtensions)

for file in os.listdir("convert"):
    if file.lower().endswith(".hmp"):
        outname = os.path.splitext(os.path.basename(file))
        outname = "out\\" + outname[0] + ".bmp"
        decompressImage("convert\\" + file, outname)
    elif file.lower().endswith(validExtensions):
        outname = os.path.splitext(os.path.basename(file))
        outname = "out\\" + outname[0] + ".hmp"
        compressImage("convert\\" + file, outname)
    else:
        print("Invalid File Type")

input("Press Enter to close")