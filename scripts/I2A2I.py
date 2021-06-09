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

# print(sys.argv)

#### Error condition checking ####

if shutil.which("ffmpeg") is None:
    print("FFmpeg is not installed on this system. Please install it to run this script.")
    sys.exit()

if len(sys.argv) == 1:
    print(f"Usage: {os.path.basename(__file__)} [resolution] [filename w/ extension] \
[audio codec] [bitrate] [internal pixel format]\n\
The internal pixel format should be \"rgb24\" for interleaved 24-bit RGB, and \"gbrp\" for planar 24-bit RGB.\n\
However, no checking is done, so go wild!")
    sys.exit()
    
if len(sys.argv) != 6:
    print(f"Invalid number of arguments given. Expected 5, got {len(sys.argv) - 1}. \n\
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

## In theory, this could be changed, but it will likely lead to unlistenable results.
step2_format = "u8"

## Step 3 ##
# All variables recycled from previous steps.

## Step 4 ##
resolution          = sys.argv[1]
step4_out_extension = ".png"

## Combined variables ##
in_file   = sys.argv[2]
step1_out = f"{in_filename}-step1-{pixel_format}"
step2_out = f"{in_filename}-step2-{audio_codec}-{bitrate}-{pixel_format}"
step3_out = f"{in_filename}-step3-{step2_format}-{audio_codec}-{bitrate}-{pixel_format}"
step4_out = f"{in_filename}-end-{audio_codec}-{bitrate}-{pixel_format}"

#### Code + Explanation ####

## Step 1: Convert input image file into a raw image in a pixel format of your choice. 
## A pixel format of "gbrp" is planar 24-bit RGB.
## Setting "rgb24" yields interleaved 24-bit RGB. 

step1_list = ["ffmpeg","-y","-i",in_file,
              "-f","rawvideo","-pix_fmt",pixel_format,f"{step1_out}.raw"]
print(step1_list)
subprocess.run(step1_list, check=True)

## Step 2: Interpret the raw image as if it were unsigned 8-bit PCM
## at 48000 KHz (by default), then encode it as audio in a codec
## defined in the script's arguments. This is where the magic is.

step2_list = ["ffmpeg","-y","-f",step2_format,"-ar",sample_rate,"-ac",internal_channels,"-i",
              f"{step1_out}.raw",
              "-c:a", audio_codec,"-b:a",bitrate,f"{step2_out}{step2_out_extension}"]
print(step2_list)
subprocess.run(step2_list, check=True)

## Step 3: Decode the audio produced in step 2 into unsigned 8-bit PCM.
## This allows Step 4 to proceed without erroring out and complaining that it's
## seeing audio instead of an image.

step3_list = ["ffmpeg","-y","-i",f"{step2_out}{step2_out_extension}",
              "-f",step2_format, f"{step3_out}.raw"]
print(step3_list)
subprocess.run(step3_list, check=True)

## Step 4: Encode the decoded audio as image data in PNG format (changeable).

step4_list = ["ffmpeg","-y","-f","rawvideo","-pix_fmt",pixel_format,"-s",resolution,"-i",
              f"{step3_out}.raw",
              f"{step4_out}{step4_out_extension}"]
print(step4_list)
subprocess.run(step4_list, check=True)