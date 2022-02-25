# pyPhotoMosaic
 pyPhotoMosaic lets you create photomosaics.

## Example:
### Original & Output
<p float="left">
<img src="target.png" height="400px" /><img src="output.jpg" height="400px" />
</p>
Artist: 
<a href="https://www.pixiv.net/artworks/96381546">https://www.pixiv.net/artworks/96381546</a>

## Prerequisites

- numpy
- cv2
- PIL

## Usage

Windows:
```console
python pMos.py <target_image> <image tiles folder> <output_filename>
```

Linux & macOS:
```console
python3 pMos.py <target_image> <image tiles folder> <output_filename>
```

It might take a while to create a the Photo Mosaics.

## Parameters
- `TILE_SIZE` (Mosaic Tiles' sizes in pixels)
- `CACHE_DIR` (Mosaic Tiles' cache directory)
- `TARGET_CACHE_DIR` (Target Image's cache directory)
- `REUSE_CACHE` (`True` to reuse the cache, `False` to regenerate cache)
- `ENLARGE_FACTOR` (Factor to enlarge the image)

