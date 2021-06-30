#### BEGINNING OF LICENSE TEXT ####

## Copyright (c) 2021 multiplealiases


## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:

## The above copyright notice and this permission notice shall be included in all
## copies or substantial portions of the Software.

## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
## EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
## MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
## IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
## DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
## OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
## OR OTHER DEALINGS IN THE SOFTWARE.

#### END OF LICENSE TEXT ####

## This script requires FFmpeg to be installed somewhere in PATH.
## If editing, you MUST encase all parameters in quotes, including the numbers.
## No error-correction done on variables; the whole script expects string type.
## You will need at least 3 times the size of the original image file free on disk. Be warned!

import subprocess
import sys
import os
import shutil
import numpy
from PIL import Image

# print(sys.argv)

#### Error condition checking ####

if shutil.which("ffmpeg") is None:
    print("FFmpeg is not installed on this system. Please install it to run this script.")
    sys.exit()

if len(sys.argv) == 1:
    print(f"Usage: {os.path.basename(__file__)} [resolution] [filename w/ extension] \
[audio codec] [bitrate] [internal pixel format] [offset in pixels, rightwards]")
    print("The internal pixel format should be \"rgb24\" for interleaved 24-bit RGB\
, and \"gbrp\" for planar 24-bit RGB.")
    print("However, no checking is done, so go wild!")
    print("This is the iterator version.")
    print("\"audio codec\", \"bitrate\" and \"internal pixel format\"\
can be given a list of arguments.")
    print("However, for most codecs, it is advisable to only give a list of bitrates, \
since the offset is fixed for each invocation.")
    print("Split the list with commas (without spaces!), surrounding it in single quotes\
 (\'\') on Unix-likes.")
    sys.exit()

if len(sys.argv) != 7:
    print(f"Invalid number of arguments given. Expected 6, got {len(sys.argv) - 1}. \n\
Run this script without arguments to see the help text.")
    sys.exit()

#### Variables ####

## Step 1 ##
in_filename  = os.path.splitext(sys.argv[2])[0]
in_extension = os.path.splitext(sys.argv[2])[1]

pixel_format = sys.argv[5]

## Step 2 ##
audio_codec         = sys.argv[3]
sample_rate         = "48000"
bitrate             = sys.argv[4]
step2_out_extension = ".mkv"
internal_channels   = "1"

audio_codec_list    = list(map(str, audio_codec.strip("(){}[]").split(",")))
bitrate_list        = list(map(str, bitrate.strip("()[]{}").split(",")))
pixel_format_list   = list(map(str, pixel_format.strip("()[]{}").split(",")))

print(list(audio_codec_list))
print(list(bitrate_list))
print(list(pixel_format_list))

## In theory, this could be changed, but it will likely lead to unlistenable results.
step2_format = "u8"

## Step 3 ##
# All variables recycled from previous steps.

## Step 4 ##
resolution          = sys.argv[1]
step4_out_extension = ".png"

## Step 5 ##
roll_amount = sys.argv[6]

## Combined variables ##


#### Code + Explanation ####

## Step 1: Convert input image file into a raw image in a pixel format of your choice.
## A pixel format of "gbrp" is planar 24-bit RGB.
## Setting "rgb24" yields interleaved 24-bit RGB.
for audio_codec_index in audio_codec_list:
    for bitrate_index in bitrate_list:
        for pixel_format_index in pixel_format_list:
            in_file   = sys.argv[2]
            step1_out = f"{in_filename}-step1-{pixel_format_index}"
            step2_out = f"{in_filename}-step2-\
{audio_codec_index}-{bitrate_index}-{pixel_format_index}"
            step3_out = f"{in_filename}-step3-\
{step2_format}-{audio_codec_index}-{bitrate_index}-{pixel_format_index}"
            step4_out = f"{in_filename}-step4-\
{audio_codec_index}-{bitrate_index}-{pixel_format_index}"
            step5_out = f"{in_filename}-end-\
{audio_codec_index}-{bitrate_index}-{pixel_format_index}-{roll_amount}"
            step1_list = ["ffmpeg","-y","-i",in_file,
                          "-f","rawvideo","-pix_fmt",pixel_format_index,f"{step1_out}.raw"]
            print(step1_list)
            subprocess.run(step1_list, check=True)

            ## Step 2: Interpret the raw image as if it were unsigned 8-bit PCM
            ## at 48000 Hz (by default), then encode it as audio in a codec
            ## defined in the script's arguments. This is where the magic is.
            step2_list = ["ffmpeg","-y","-f",step2_format,"-ar",sample_rate,"-ac",internal_channels,
                          "-i",f"{step1_out}.raw",
                          "-c:a", audio_codec_index,"-b:a",bitrate_index,
                          f"{step2_out}{step2_out_extension}"]
            print(step2_list)
            subprocess.run(step2_list, check=True)

            ## Step 3: Decode the audio produced in step 2 into unsigned 8-bit PCM.
            ## This allows Step 4 to proceed without erroring out and complaining that it's
            ## seeing audio instead of an image.
            step3_list = ["ffmpeg","-y","-i",f"{step2_out}{step2_out_extension}",
                         "-f",step2_format,"-ar",sample_rate, f"{step3_out}.raw"]
            print(step3_list)
            subprocess.run(step3_list, check=True)

            ## Step 4: Encode the decoded audio as image data in PNG format (changeable).
            step4_list = ["ffmpeg","-y",
                          "-f","rawvideo",
                          "-pix_fmt",pixel_format_index,
                          "-s",resolution,"-i",
                          f"{step3_out}.raw",
                          f"{step4_out}{step4_out_extension}"]
            print(step4_list)
            subprocess.run(step4_list, check=True)

            ## Step 5: Roll the Step 4 image by some amount of pixels as defined in roll_amount.

            print(f"\nOffsetting image by {roll_amount} pixels...")

            step5_image = Image.open(f"{step4_out}{step4_out_extension}")

            step5_data = numpy.asarray(step5_image)

            step5_int_data = step5_data.astype(numpy.uint8)

            ## Multiply by 3 here, since PNG uses 24-bit RGB
            ## and will cause hue-shifts if not shifted by a multiple of 3.
            step5_rolled_data = numpy.roll(step5_int_data,int(roll_amount) * 3)

            step5_rolled_image = Image.fromarray(step5_rolled_data)

            step5_rolled_image.save(f"{step5_out}.png")

            print("Done.\n")

            ## Technically Step 6: Clear up the intermediate files.

            print("Deleting intermediate files...")
            os.remove(f"{step1_out}.raw")
            os.remove(f"{step2_out}{step2_out_extension}")
            os.remove(f"{step3_out}.raw")
            os.remove(f"{step4_out}{step4_out_extension}")
            print("Done.")
