import os
import numpy
from PIL import Image

def compressImage(inputFileName, hmpFileName):
        
    #get image info
    image = Image.open(inputFileName).convert("RGB")
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    width = image.width
    height = image.height

    #get pixel data and convert to 16 bit color
    pixelList = []
    i = 0
    for y in range(height):
        for x in range(width):
            r, g, b = image.getpixel((x,y))
            r = (r*249 +1014) >> 11
            g = (g*249 +1014) >> 11
            b = (b*249 +1014) >> 11
            pixelList.append((r<<10) + (g<<5) + (b))
            i+=1

    #compress px array
    flagMapBits = []
    colList = ["","",""]
    hmpValList = []
    lengthList = []

    i=0
    while i < len(pixelList) - 2:
        
        #check if its in the color list or color 2 and if not, add it to the top, shifting other colors down
        #also append 0 to flagmap
        if pixelList[i] not in colList:
            colList[2] = colList[1]
            colList[1] = colList[0]
            colList[0] = pixelList[i]

            flagMapBits.append(0)
            hmpValList.append(pixelList[i].to_bytes(2, "little")[:1])
            hmpValList.append(pixelList[i].to_bytes(2, "little")[1:2])
            i += 1

        else:
            
            #I HATE EVERYTHING ABOUT THIS STUPID FUCKING COMPRESSION ALGORITHM
            #if its the first color in the color list we can only draw that color repeating
            if pixelList[i] == colList[0]:
                colChoiceBit = 1
                drawMethodBit = 0
            #if its second we can either repeat the first color then it, or we just repeat it by itself
            elif pixelList[i] == colList[1]:
                if pixelList[i+1] == colList[0]:
                    colChoiceBit = 1
                    drawMethodBit = 1
                    maincol = pixelList[i+1]
                    altcol = pixelList[i]
                else:
                    colChoiceBit = 0
                    drawMethodBit = 0
            #if its third we can either repeat the second color then it, or we remove it from our color list and start over without incrementing
            #this essentially moves it to the top of the color list and shifts other things down
            else:
                if pixelList[i+1] == colList[1]:
                    colChoiceBit = 0
                    drawMethodBit = 1
                    maincol = pixelList[i+1]
                    altcol = pixelList[i]
                else:
                    colList[2] = ""
                    continue

            #count length
            length = 1
            if drawMethodBit == 0:
                checkPos = i+1
                while  checkPos <= len(pixelList) - 1 and pixelList[checkPos] == pixelList[i] and length < 319:
                    length += 1
                    checkPos += 1
                i += length
            else:
                checkPos = i+2
                while checkPos <= len(pixelList) - 2 and pixelList[checkPos+1] == maincol and pixelList[checkPos] == altcol and length < 319:
                    length += 1
                    checkPos += 2
                i += 2*length
            
            #handle large length and append values to valmap and append 1 to flagmap
            if length < 64:
                lengthbits = length
            else:
                lengthbits = 0
                lengthbyte = length - 64

            flagMapBits.append(1)
            drawInstrByte = (drawMethodBit << 7) + (colChoiceBit << 6) + (lengthbits)
            hmpValList.append(drawInstrByte.to_bytes())

            if length >= 64:
                hmpValList.append(lengthbyte.to_bytes())

    #handle edge cases
    if i == len(pixelList) - 2:
        appendNew = False
        #do our normal checks and set length to 1 unless its colList[2]
        if pixelList[i] == colList[0]:
            colChoiceBit = 1
            drawMethodBit = 0
            lengthbits = 1
        elif pixelList[i] == colList[1]:
            if pixelList[i+1] == colList[0]:
                colChoiceBit = 1
                drawMethodBit = 1
                lengthbits = 1
                i += 1
            else:
                colChoiceBit = 0
                drawMethodBit = 0
                lengthbits = 1
        else:
            if pixelList[i+1] == colList[1]:
                colChoiceBit = 0
                drawMethodBit = 1
                lengthbits = 1
                i += 1
            else:
                colList[2] = ""
                colList[2] = colList[1]
                colList[1] = colList[0]
                colList[0] = pixelList[i]
                appendNew = True
                flagMapBits.append(0)
                hmpValList.append(pixelList[i].to_bytes(2, "little")[:1])
                hmpValList.append(pixelList[i].to_bytes(2, "little")[1:2])
        if not appendNew:
            flagMapBits.append(1)
            drawInstrByte = (drawMethodBit << 7) + (colChoiceBit << 6) + (lengthbits)
            hmpValList.append(drawInstrByte.to_bytes())
        i += 1

    if i == len(pixelList) - 1:
        appendNew = False
        #do our checks without checking next pixel
        if pixelList[i] == colList[0]:
            colChoiceBit = 1
            drawMethodBit = 0
            lengthbits = 1
        elif pixelList[i] == colList[1]:
            colChoiceBit = 0
            drawMethodBit = 0
            lengthbits = 1
        else:
            appendNew = True
            flagMapBits.append(0)
            hmpValList.append(pixelList[i].to_bytes(2, "little")[:1])
            hmpValList.append(pixelList[i].to_bytes(2, "little")[1:2])
        if not appendNew:
            flagMapBits.append(1)
            drawInstrByte = (drawMethodBit << 7) + (colChoiceBit << 6) + (lengthbits)
            hmpValList.append(drawInstrByte.to_bytes())
            


    #write hmp
    #make length of flagmapbits a multiple of 8
    while len(flagMapBits) % 8 != 0:
        flagMapBits.append(0)

    trueFlagMap = []

    i = 0
    while i < len(flagMapBits):
        currentByte = []
        currentByte.extend(flagMapBits[i:i+8])
        currentNum = 0
        for bit in currentByte:
            currentNum = 2* currentNum + bit
        trueFlagMap.append(currentNum.to_bytes())
        i+=8
    
    #make hmp file
    hmpFileHeader = b"HM"
    hmpFileHeader += int(width).to_bytes(4, "little")
    hmpFileHeader += int(height).to_bytes(4,"little")
    hmpFileHeader += int(len(trueFlagMap)).to_bytes(4,"little")
    hmpFileHeader += int(len(hmpValList)).to_bytes(4,"little")

    with open(hmpFileName, "wb") as hmpFile:
        hmpFile.write(hmpFileHeader)
        for val in trueFlagMap:
            hmpFile.write(val)
        for val in hmpValList:
            hmpFile.write(val)
        hmpFile.close()
    
    print(os.path.basename(inputFileName) + " converted to " + os.path.basename(hmpFileName))