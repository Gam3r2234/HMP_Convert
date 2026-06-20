# HMP Convert
## Description: <br/>
HMP Convert is a program that compresses images from any PIL supported image format into the .hmp format used by OPTWORKS games (18+). It also decompresses .hmp images into bitmap files. 

This program was made with the help of gocha's spioptw susie plugin as a reference for decompression (with some minor fixes): <br/>
https://github.com/gocha/spioptw

No generative AI was used in any step the making of this program.

## Usage: <br/>
To use, put all images you would like to compress/decompress into the "convert" folder and run the run.bat file. The outputs will be in the "out" folder. <br/>

## Known Issues: <br/>
Sometimes has issues with PNG images that have fully transparent pixels.

## The HMP file format: <br/>
The HMP file format is an RLE compressed image format. <br/>
It uses 16 bit color (RGB555 with the most significant bit unused) and decompresses from the bottom left of the image to the top right. <br/>
It consists of 3 sections: the header, the flagmap, and the value map. <br/>
It also has a running list of the last 3 unique colors drawn, used when decompressing (will be referred to as the color list).

### The Header: <br/>
The header is composed of 5 sections: <br/>
The first two bytes are the file magic and read "HM". <br/>
The next 4 bytes are the width of the image in little endian. <br/>
The next 4 bytes are the height of the image in little endian. <br/>
The next 4 bytes are the length of the flagmap in little endian. <br/>
The last 4 bytes are the length of the value map in little endian.

### The Flagmap <br/>
The flagmap is composed of a series of bytes read from the most to least significant bit, starting from the first byte after the header and going to the last byte before the value map. <br/>
Each bit corresponds to an instruction for decompressing the file. <br/>
A 0 means the next 2 bytes in the value map will be interpereted as a color. <br/>
A 1 means the next 1 byte in the value map will be interpereted as an instruction for decompression. <br/>
After a whole byte is read, the next byte is looked at. No bits are ever looked at twice. <br/>
If the number of instructions is not a multiple of 8, the remaining bits in the last byte will be filled in with zeroes.

### The Value Map <br/>
The value map can be read two ways: as a color or as a draw instruction. <br/>
If it is read as a color, the next two bytes will be interpreted as a 16 bit color, and 1 pixel of that color will be drawn to the screen during decompression. <br/>
If it is read as a draw instruction, the next one byte will be split up into a draw method bit, a color choice bit, and 6 length bits.

Draw Method Bit: <br/>
If the draw method bit is 0, it draws the main color, the length amount of times. <br/>
If the draw method bit is 1, it draws the alt color, then the main color, the length amount of times.

Color Choice Bit: <br/>
If the color choice bit is 0, the main color will be set to the most recent color in the color list. The alt color will be set to the second most recent color in the color list. <br/>
If the color choice bit is 1, the main color will be set to the second most recent color in the color list. The alt color will be set to the third most recent color in the color list.

Length Bits: <br/>
The length bits can be either all zero, or nonzero. <br/>
If the length bits are nonzero, the length equals the value stored in the length bits. <br/>
If the length bits are zero, the length is set to the next byte in the value map, minus 64, and that byte is skipped over when reading the next instruction or color.

~Snow (she/her)
