import os
import shutil
import sys
from threading import Thread
import cv2
import numpy as np
from multiprocessing import Pool, cpu_count

TILE_SIZE = 80  # Mosaic Tile Size in Pixels
CACHE_DIR = ".CACHE1"
TARGET_CACHE_DIR = ".TARGET_CACHE1"
REUSE_CACHE = False
ENLARGE_FACTOR = 8
workers = cpu_count()

_bgrList = []

def buildMosaic(height, width, bgrList, OUTPUT):
    output_img = np.ones((height,width,3), np.uint8)*255

    for i in range(0, (height // TILE_SIZE)):
        for j in range(0, (width // TILE_SIZE)):
            bgr = cv2.imread(os.path.join(TARGET_CACHE_DIR,
                                          str(i) + "," + str(j) + ".png"))
            mean = np.mean(np.array(bgr))   # find mean color value of a bgr tile
            diff = np.abs(np.subtract(bgrList, mean))   # find the difference between two arrays
            index = np.where(diff == diff.min())[0][0]  # find the index of the diff in bgrList
            fileName = f"{CACHE_DIR}/{np.array2string(bgrList[index], separator = ',').replace(' ', '').replace('[', '').replace(']', '')}.jpg"

            fileName = cv2.imread(os.path.join(fileName))

            x, x2 = j * TILE_SIZE, (j + 1) * TILE_SIZE
            y, y2 = i * TILE_SIZE, (i + 1) * TILE_SIZE

            output_img[y:y2, x:x2] = fileName

    cv2.imwrite(os.path.join(OUTPUT), output_img)

    print("[+] Image created:", OUTPUT)


def analyseTiles():
    tilesBGR = [f.split(".")[0] for f in os.listdir(CACHE_DIR)]
    for bgr in tilesBGR:
        bgr = bgr.split(",")
        _bgrList.append(
            np.array([int(float(bgr[0])), int(float(bgr[1])), int(float(bgr[2]))]))


def findDominantColor(im):
    r_sum = g_sum = b_sum = 0
    pixel_count = TILE_SIZE * TILE_SIZE
    height, width = im.shape[:2]
    for i in range(0, width):
        for j in range(0, height):
            b_count, g_count, r_count = im[j,i][:3]
            r_sum += r_count
            g_sum += g_count
            b_sum += b_count
    bgr = np.array([int(b_sum / pixel_count), int(g_sum / pixel_count), int(r_sum / pixel_count)])
    
    avgColorPerRow = np.average(im, axis=0)
    avgColor = np.average(avgColorPerRow, axis=0)
    dominant_color = np.array2string(np.true_divide(np.add(bgr, avgColor), 2).astype(int), separator=',').replace('[', '').replace(']', '').replace(' ', '')

    return dominant_color


def imgcrop(im, xPieces, yPieces):  # im in the format of numpy array
    imgwidth, imgheight = im.shape[:2]
    height = imgheight // yPieces
    width = imgwidth // xPieces
    h, w = imgheight // (imgheight // TILE_SIZE), imgwidth // (imgwidth // TILE_SIZE)
    for i in range(0, yPieces):
        for j in range(0, xPieces):

            x, x2 = j * w, (j + 1) * w
            y, y2 = i * h, (i + 1) * h

            a = im[y:y2, x:x2]
            a = np.array(a)
            
            try:
                cv2.imwrite(os.path.join(TARGET_CACHE_DIR + "/" + str(i) + "," + str(j) + ".png"), a)
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

    index = 0
    # copy and rename all files into index numbers in dir to CACHE_DIR
    if REUSE_CACHE == False:
        # load all files in CACHE_DIR one by one and crop them into tiles
        for f in os.listdir(dir):
            cache_img = cv2.imread(os.path.join(dir, f), 1)

            if f.endswith("webp"):
                os.remove(os.path.join(dir, f))
            elif not f.endswith(".jpg") and not f.endswith(".DS_Store"):
                index += 1
                cv2.imwrite(f"{CACHE_DIR}/cached_{index}.jpg",
                            cache_img, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
            elif not f.endswith(".DS_Store") and f.endswith(".jpg"):
                index += 1
                shutil.copy(os.path.join(dir, f),
                            f"{CACHE_DIR}/cached_{index}.jpg")
        for fi in os.listdir(CACHE_DIR):
            try:
                f = cv2.imread(CACHE_DIR+"/"+fi)
                if fi.endswith(".jpg"):
                    height, width = f.shape[:2]
                    # crop largest square in center of image
                    if height == width:
                        f = cv2.resize(f, (TILE_SIZE, TILE_SIZE),
                                    interpolation=cv2.INTER_AREA)
                        dominantColor = findDominantColor(f)
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
                        dominantColor = findDominantColor(f)

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
                        dominantColor = findDominantColor(f)

                        os.remove(CACHE_DIR+"/"+fi)
                        cv2.imwrite(f"{CACHE_DIR}/{dominantColor}.jpg", f,
                                    [int(cv2.IMWRITE_JPEG_QUALITY), 100])
                    else:
                        pass
                else:
                    os.remove(CACHE_DIR+"/"+fi)
            except:
                pass

    elif REUSE_CACHE == True:
        pass


def processTargetImage(target_path, SOURCE_DIR, OUTPUT):
    # load target image
    _processTile = Pool(workers)
    _processTile.map_async(processTile, [SOURCE_DIR])
    _processTile.close()

    print("[+] Processing Main Image...")

    # read target image
    img = cv2.imread(target_path)
    height, width = img.shape[:2]

    # enlarge width and height of target image with ENLARGE_FACTOR
    img = cv2.resize(img, (int(width * ENLARGE_FACTOR),
                           int(height * ENLARGE_FACTOR)), interpolation=cv2.INTER_NEAREST)
    height, width = img.shape[:2]

    if (height % TILE_SIZE == 0) and (width % TILE_SIZE == 0):
        _imgcrop = Thread(target=imgcrop, args=(
            img, width // TILE_SIZE, height // TILE_SIZE))
        _imgcrop.start()
        print("[!] Cropping Target Image...")
    else:
        # trim target height and width evenly to make it divisible by TILE_SIZE
        pixelsToTrimHeightEach = (height % TILE_SIZE) // 2
        pixelsToTrimWidthEach = (width % TILE_SIZE) // 2
        img = img[pixelsToTrimHeightEach:height-pixelsToTrimHeightEach,
                  pixelsToTrimWidthEach:width-pixelsToTrimWidthEach]
        height, width = img.shape[:2]
        _imgcrop = Thread(target=imgcrop, args=(
            img, width // TILE_SIZE, height // TILE_SIZE))
        _imgcrop.start()
        print("[!] Cropping Target Image...")

    if os.path.exists(os.path.join(TARGET_CACHE_DIR)):
        for f in os.listdir(os.path.join(TARGET_CACHE_DIR)):
            os.remove(os.path.join(TARGET_CACHE_DIR, f))
    else:
        os.mkdir(os.path.join(TARGET_CACHE_DIR))

    _imgcrop.join()
    _processTile.join()

    _mainimgcrop = Pool(workers)
    _mainimgcrop.starmap(imgcrop, [(img, width // TILE_SIZE, height // TILE_SIZE)])
    _mainimgcrop.close()

    analyseTiles()

    print("[!] Tiles Processed")

    _mainimgcrop.join()
    print("[!] Target Image Processed")

    print("[+] Building Output Image...")
    _buildMosaic = Pool(workers)
    _buildMosaic.starmap(buildMosaic, [(height, width, _bgrList, OUTPUT)])
    _buildMosaic.close()

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
