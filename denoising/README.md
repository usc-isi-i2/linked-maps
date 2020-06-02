# Denoising
- Denoising is the task of removing false positives from map vector data using clustering analysis.
- Because of the usage of clustering techniques in determining the noise, this method is unsupervised.
- It is (as of yet) intended to work for linear continuous features such as railroads, roads, waterlines.

<hr>

## Usage:
- Input: a shapefile
- Output: denoised shapefile
- Command: *python3 denoiser.py /path/to/shapefile/\*.shp*
- Default: python3 denoiser.py --clustering agglomerative --basis health --plot True --decimals 6 SHAPEFILE (see Notes)
# 
    python3 denoiser.py [-h] [--clustering [C]] [--basis [B]] [--explain [%]]
                        [--plot [P]] [--decimals [D]]
                        SHAPEFILE [SHAPEFILE ...]
                        
#### positional arguments:
    SHAPEFILE         input map shapefile

#### optional arguments:
    -h, --help        show this help message and exit
    --clustering [C]  agglomerative (default) or dbscan
    --basis [B]       sorting basis: health (default) or density
    --explain [%]     percetage data to explain [0,1]
    --plot [P]        Plot? Default: True
    --decimals [D]    Round D(6) places                   

### Denoising Example
![Example](https://github.com/usc-isi-i2/linked-maps/blob/denoising/denoising/examples/example.png)
- **Black**: Noise (False Positive) identified
- Note: The axes range wasn't controlled for plotting and hence the discerning distortions in the denoised plots.

<hr>

# About Denoiser:
* The goal of the denoiser is to produce a richer map vector data that has greater overlap with the ground truth map.
* The removal of false positives leads to higher precision and thus better F1 score.
* Denoising although is not perfect and comes at a cost: some true positives also get removed.
* _assumptions:_
  - _feature of interest is dense and continuous_
  - _noise is scatterd and scanty_
* _intuition: by eyeballing we can determine that the scattered, scanty points are noise (refer to example below)_
<hr>

# How does it work:

1) The inputted map (shapefile) is preprocessed and the coordinates are rounded off to D decimal places.
2) According to the clustering C (agglomerative | dbscan)
  - Initial clusters of the geocoordinates are formed
  - Depending on the basis B:
    - health: clusters are sorted based on a health score (see below) calculated for their neighborhood
    - density: clusters are sorted based on the number of points they contain
  - Using a ![Knee Detection Algorithm](https://github.com/arvkevi/kneed) , a knee is determined and the noisy clusters are discarded.
  - The discarding is done based on estimating noise in an unsupervised manner, either:
    - pass as an argument P% to be explained/retained i.e. atmost (100-P)% noise will be removed
    - or estimation algorithm estimates noise based on the scatter plot of data (below)
3) The data points (geocoordinates) of the remaining clusters are outputted to a shapefile.

##### Estimating Noise
- Save scatter plot of data as an image
- Binarize the image
- Determine the components (using 8-adj) in the pixel grid *n_components*
- Estimate:
  1) Agglomerative:
    - form *n_components* clusters and find the knee
  2) DBSCAN:
    - form *n_components* clusters
    - using matplotlib, re-map the data to pixel to determine the density of the `components (in pixel grid)`
    - find the knee as per the basis (density / health scores)
    - % noise = (discarded components) / (total data)
    - explain (100-%noise) in the data clusters to get denoised data



<hr>

# Where does it fit in the pipeline:
1. A semantic segmentation neural network is trained to recognize geographical features (eg. railroads)
2. The extracted pixel mask is converted to vector data (raster -> vector). (output: a shapefile .shp)
3. The shapefile is passed as an argument to the denoiser to remove the unnecessary false positives recognized by the semantic segmentation model.
4. The output of the denoiser is a cleaned shapefile that has fewer noise.

<hr>

![Health Formula](https://github.com/usc-isi-i2/linked-maps/blob/denoising/denoising/examples/health2.png)
![Health](https://github.com/usc-isi-i2/linked-maps/blob/denoising/denoising/examples/health1.png)

### Notes
- Agglomerative is faster than DBSCAN (in this algorithm)
- Use default settings for most robust performance.
- **Tweaking**: The kneedle hyperparameters used might need to tweaked accordingly.
- **Caution**: The algorithm would still detect `noise` in a perfect data having 0% noise.


#### Author: Pratulya Bubna (https://github.com/pratulyab)
