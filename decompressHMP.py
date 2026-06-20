import os
import numpy

def decompressImage(hmpFileName, bmpFileName):
    with open(hmpFileName, "rb") as hmpFile:

        #read magic
        hmpfilemagic = hmpFile.read(2)

        if hmpfilemagic == b"HM":
            
            #read header
            width = int.from_bytes(hmpFile.read(4), "little")
            height =  int.from_bytes(hmpFile.read(4), "little")
            flagmapSize =  int.from_bytes(hmpFile.read(4), "little")
            valmapSize = int.from_bytes(hmpFile.read(4), "little")
            hmpFileSize = os.path.getsize(hmpFileName)
            headersize = 18

            #get offsets
            flagmapOfs = headersize
            valmapOfs = flagmapOfs + flagmapSize
            valmapStartPos = valmapOfs

            #dummy colors for list
            color1 = ""
            color2 = ""
            color3 = ""

            #setup pixel array
            pixelArr = numpy.empty((height,width), dtype=numpy.uint16)

            (x,y)=(0,0)

            while flagmapOfs < valmapStartPos:
                #move to new flag offset and get next byte
                hmpFile.seek(flagmapOfs)
                flagByte = int.from_bytes(hmpFile.read(1))
                flagmapOfs += 1

                #get next bit in byte
                n = 7
                while n >= 0 and valmapOfs < hmpFileSize: 
                    flagBit = flagByte & (1 << n) > 0
                    n -= 1

                    #if next bit is 0, next 2 bytes are the next color added to list, and one pixel of that color is added to bitmap
                    writeToPxArr = []
                    if not flagBit:
                        hmpFile.seek(valmapOfs)
                        readBytes = int.from_bytes(hmpFile.read(2), "little")
                        valmapOfs += 2

                        #add to list and shift down
                        color3 = color2
                        color2 = color1
                        color1 = readBytes

                        writeToPxArr.append(readBytes)

                    #if next bit is 1
                    else:
                        hmpFile.seek(valmapOfs)
                        readByte = int.from_bytes(hmpFile.read(1))
                        valmapOfs += 1

                        #check second bit of next byte in valmap
                        colorChoiceBit = readByte & 0x40 > 0
                        #if the bit is 1 set maincolor to color 1 and altcolor to color 2
                        if colorChoiceBit:
                            maincolor = color1
                            altcolor = color2
                        #if the bit is 0 set maincolor to color 2 and altcolor to color 3
                        else:
                            maincolor = color2
                            altcolor = color3

                        #check last 6 bits of byte
                        length = readByte & 0x3f
                        #check if length is 0 and if it is add the next byte to 0x40 and set that to length
                        if length == 0:
                            hmpFile.seek(valmapOfs)
                            lengthByte = int.from_bytes(hmpFile.read(1))
                            valmapOfs += 1
                            length = lengthByte + 0x40

                        #check first bit of byte
                        colorMethodBit = readByte & 0x80 > 0
                        #if the bit is 1 alternate alt then main length times
                        if colorMethodBit:
                            for i in range(length):
                                writeToPxArr.append(altcolor)
                                writeToPxArr.append(maincolor)
                        #if the bit is 0 write main length times
                        else:
                            for i in range(length):
                                writeToPxArr.append(maincolor)    

                    #write to pixel array
                    for pixel in writeToPxArr:
                        if y < height:
                            pixelArr[y,x] = pixel
                            if x < width-1:
                                x += 1
                            else:
                                x = 0
                                y += 1

                        
            #make image the fucked up way
            #start of bitmap header
            bmpHeader = b"BM" #2 bytes
            bmpHeader += int(54+(width*height*2)).to_bytes(4, "little") #bmp file size
            bmpHeader += len([]).to_bytes(2) #doesnt matter
            bmpHeader += len([]).to_bytes(2) #doesnt matter
            bmpHeader += int(54).to_bytes(4, "little") #pixel start ofs
            #start of bitmapinfoheader
            bmpHeader += int(40).to_bytes(4, "little") #size of this header
            bmpHeader += width.to_bytes(4, "little") #width
            bmpHeader += height.to_bytes(4, "little") #height
            bmpHeader += int(1).to_bytes(2, "little") #color plane
            bmpHeader += int(16).to_bytes(2, "little") #bitsperpixel
            bmpHeader += int(0).to_bytes(4, "little") #no compression
            bmpHeader += int((width*height*2)).to_bytes(4, "little") #image size (default 0)
            bmpHeader += int(1).to_bytes(4, "little") #horiz res
            bmpHeader += int(1).to_bytes(4, "little") #vert res
            bmpHeader += int(0).to_bytes(4, "little") #colors in color palette (default 0)
            bmpHeader += int(0).to_bytes(4, "little") #important colors

            #write
            with open(bmpFileName, "wb") as outputFile:
                outputFile.write(bmpHeader)
                outputFile.write(pixelArr.tobytes())
                outputFile.close()

            print(os.path.basename(hmpFileName) + " converted to " + os.path.basename(bmpFileName))

        else:
            print("THIS IS NOT AN HMP FILE")