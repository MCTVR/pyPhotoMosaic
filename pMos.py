# -*- coding: utf-8 -*-
import os
import shutil
import sys
import cv2
from multiprocessing import Process
import numpy as np
from PIL import Image

TILE_SIZE = 80  # Mosaic Tile Size in Pixels
CACHE_DIR = ".CACHE"
TARGET_CACHE_DIR = ".TARGET_CACHE"
REUSE_CACHE = False
ENLARGE_FACTOR = 8


def findDominantColor(im):
    r_sum = g_sum = b_sum = 0
    pixel_count = TILE_SIZE * TILE_SIZE
    width, height = im.size
    for i in range(0, width):
        for j in range(0, height):
            r_count, g_count, b_count = im.getpixel((i, j))
            r_sum += r_count
            g_sum += g_count
            b_sum += b_count

    rgb = np.array([int(r_sum / pixel_count), int(g_sum /
                                                  pixel_count), int(b_sum / pixel_count)])
    pixels = im.getcolors(TILE_SIZE * TILE_SIZE)
    pixels = sorted(pixels, key=lambda t: t[0])
    dominant_color = np.asarray(pixels[-1][1])
    dominant_color = np.array2string(np.true_divide(np.add(rgb, dominant_color), 2).astype(
        int), separator=',').replace('[', '').replace(']', '').replace(' ', '')
    return dominant_color


def imgcrop(im, xPieces, yPieces):  # im in the format of numpy array
    im = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
    imgwidth, imgheight = im.size
    height = imgheight // yPieces
    width = imgwidth // xPieces
    for i in range(0, yPieces):
        for j in range(0, xPieces):
            box = (j * width, i * height, (j + 1) * width, (i + 1) * height)
            a = im.crop(box)
            try:
                a.save(os.path.join(TARGET_CACHE_DIR + "/" +
                                    str(i) + "," + str(j) + ".png"), "PNG")
            except:
                pass

# force remove CACHE_DIR


def removeCache():
    if os.path.exists(CACHE_DIR) == True:
        for f in os.listdir(CACHE_DIR):
            os.remove(CACHE_DIR+"/"+f)
        os.rmdir(CACHE_DIR)


def makeCache():
    if os.path.exists(CACHE_DIR) == False:   # if no cache, create one
        print("[!] Creating cache")
        os.mkdir(CACHE_DIR)
    elif os.path.exists(CACHE_DIR) == True:
        if REUSE_CACHE == True:    # if REUSE_CACHE is True
            if os.path.exists(CACHE_DIR):    # if .CAHCE exists, return 0
                print("[!] Reusing Cache")
                return 0
            else:       # if .CACHE doesn't exist, create it
                print("[!] Creating Cache")
                os.mkdir(CACHE_DIR)
                return 0
        # if    # if REUSE_CACHE is False, remove .CACHE
        elif REUSE_CACHE == False and os.path.exists(CACHE_DIR) == True:
            print("[!] Not Reusing Cache")
            removeCache()
            makeCache()
            return 0


def processTile(dir):

    makeCache()

    # copy and rename all files into index numbers in dir to CACHE_DIR
    index = 0
    if REUSE_CACHE == False:
        # load all files in CACHE_DIR one by one and crop them into tiles
        for f in os.listdir(dir):
            cache_img = cv2.imread(os.path.join(dir, f), 1)
            if not f.endswith(".jpg"):
                index += 1
                cv2.imwrite(f"{CACHE_DIR}/cached_{index}.jpg",
                            cache_img, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
            else:
                index += 1
                shutil.copy(os.path.join(dir, f),
                            f"{CACHE_DIR}/cached_{index}.jpg")

        for fi in os.listdir(CACHE_DIR):
            f = cv2.imread(CACHE_DIR+"/"+fi)
            height, width = f.shape[0], f.shape[1]
            # crop largest square in center of image
            if height == width:
                f = cv2.resize(f, (TILE_SIZE, TILE_SIZE),
                               interpolation=cv2.INTER_AREA)
                _f = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
                dominantColor = findDominantColor(Image.fromarray(_f))
                os.remove(CACHE_DIR+"/"+fi)
                cv2.imwrite(f"{CACHE_DIR}/{dominantColor}.jpg", f,
                            [int(cv2.IMWRITE_JPEG_QUALITY), 100])

            elif width > height:
                x = int((width - height) / 2)
                y = 0
                w = height
                h = height
                f = cv2.resize(f[y:y+h, x:x+w], (TILE_SIZE,
                                                 TILE_SIZE), interpolation=cv2.INTER_AREA)
                _f = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
                dominantColor = findDominantColor(Image.fromarray(_f))

                os.remove(CACHE_DIR+"/"+fi)
                cv2.imwrite(f"{CACHE_DIR}/{dominantColor}.jpg", f,
                            [int(cv2.IMWRITE_JPEG_QUALITY), 100])
            elif height > width:
                x = 0
                y = int((height - width) / 2)
                w = width
                h = width
                f = cv2.resize(f[y:y+h, x:x+w], (TILE_SIZE,
                                                 TILE_SIZE), interpolation=cv2.INTER_AREA)

                _f = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
                dominantColor = findDominantColor(Image.fromarray(_f))

                os.remove(CACHE_DIR+"/"+fi)
                cv2.imwrite(f"{CACHE_DIR}/{dominantColor}.jpg", f,
                            [int(cv2.IMWRITE_JPEG_QUALITY), 100])
            else:
                pass

    elif REUSE_CACHE == True:
        pass


def processTargetImage(target_path, SOURCE_DIR, OUTPUT):
    # process source into tiles
    _processTile = Process(target=processTile, args=(SOURCE_DIR,))
    _processTile.start()

    print("[+] Processing Main Image...")

    # read target image
    img = cv2.imread(target_path)
    height, width = img.shape[0], img.shape[1]

    # enlarge width and height of target image with ENLARGE_FACTOR
    img = cv2.resize(img, (int(width * ENLARGE_FACTOR),
                           int(height * ENLARGE_FACTOR)), interpolation=cv2.INTER_NEAREST)
    height, width = img.shape[0], img.shape[1]

    if (height % TILE_SIZE == 0) and (width % TILE_SIZE == 0):
        pass
    else:
        # trim target height and width evenly to make it divisible by TILE_SIZE
        pixelsToTrimHeightEach = (height % TILE_SIZE) // 2
        pixelsToTrimWidthEach = (width % TILE_SIZE) // 2
        img = img[pixelsToTrimHeightEach:height-pixelsToTrimHeightEach,
                  pixelsToTrimWidthEach:width-pixelsToTrimWidthEach]
        height, width = img.shape[0], img.shape[1]

    if os.path.exists(os.path.join(TARGET_CACHE_DIR)):
        for f in os.listdir(os.path.join(TARGET_CACHE_DIR)):
            os.remove(os.path.join(TARGET_CACHE_DIR, f))
    else:
        os.mkdir(os.path.join(TARGET_CACHE_DIR))

    output_img = Image.new('RGB', size=(width, height))

    _processTile.join()

    tilesRGB = [f.split(".")[0] for f in os.listdir(CACHE_DIR)]

    rgbList = []

    for rgb in tilesRGB:
        rgb = rgb.split(",")
        rgbList.append(
            np.array([int(float(rgb[0])), int(float(rgb[1])), int(float(rgb[2]))]))
    print("[!] Tiles Processed")

    imgcrop(img, width // TILE_SIZE, height // TILE_SIZE)

    print("[!] Target Image Processed")

    print("[+] Building Output Image...")
    for i in range(0, (height // TILE_SIZE)):
        for j in range(0, (width // TILE_SIZE)):
            rgb = Image.open(os.path.join(TARGET_CACHE_DIR,
                                          str(i) + "," + str(j) + ".png"))
            # find mean color value of a rgb tile
            mean = np.mean(np.array(rgb))
            # find the difference between two arrays
            diff = np.abs(np.subtract(rgbList, mean))
            # find the index of the diff in rgbList
            index = np.where(diff == diff.min())[0][0]
            fileName = f"{CACHE_DIR}/{np.array2string(rgbList[index], separator = ',').replace(' ', '').replace('[', '').replace(']', '')}.jpg"
            fileName = Image.open(os.path.join(fileName))
            output_img.paste(fileName, (j * TILE_SIZE, i * TILE_SIZE))

    output_img.save(os.path.join(OUTPUT))

    print("[+] Image created:", OUTPUT)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "[-] Usage: python mos.py <target_image> <image tiles folder> <output_filename>")
    else:
        target_image = sys.argv[1]
        SOURCE_DIR = sys.argv[2]
        OUTPUT = sys.argv[3]
        if not os.path.isfile(target_image):
            print("[-] Target image not found")
        elif not os.path.isdir(SOURCE_DIR):
            print("[-] Source image tiles folder not found")
        else:
            processTargetImage(target_image, SOURCE_DIR, OUTPUT)
