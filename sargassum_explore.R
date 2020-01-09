# ---
# title: "Sargassum Data Exploration"
# author: "Allison Bailey"
# date: "8/19/2019"
# output: html_document
# ---

# Setup
### Load Packages..
library(raster)
library(rgdal)

datadir <- "/Users/allison/projects/natcap/mar2019/sargassum/0190272/1.1/data/0-data/Sargassum_areal_coverage/Sargassum_areal_coverage"
tiff <- "Year-2018-07.S_coverage.tiff"
sarg_raster <- raster(file.path(datadir, tiff))
plot(sarg_raster)
hist(sarg_raster, col="springgreen")
cellStats(sarg_raster, 'mean')
freq(sarg_raster)

