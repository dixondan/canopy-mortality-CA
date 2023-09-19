
require('lidR')
library('raster')
library(sf)
library("rgdal")
library("terra")

options(warn=-1)

args = commandArgs(trailingOnly=TRUE)
laz = args[1]
outcrowns = args[2]

segment <- function(laz) {
  # read in the laz file
  print('reading laz')
  las <- readLAS(laz)
  las <- classify_noise(las, sor(k = 10, m = 3, quantile = FALSE))
  las <- filter_poi(las, Classification != 18)

  print('normalize points')
  # get canopy height model
  las <- normalize_height(las, knnidw())

  print('smoothing')
  # smoothing 1
  chm_p2r_1 <- rasterize_canopy(las, 1, p2r(subcircle = 0.2), pkg = "terra")
  kernel <- matrix(1,3,3)
  chm_p2r_1_smoothed <- terra::focal(chm_p2r_1, w = kernel, fun = median, na.rm = TRUE)
  # tree tops
  ttops_chm_p2r_1_smoothed <- locate_trees(chm_p2r_1_smoothed, lmf(4))
  # segment point cloud
  algo <- dalponte2016(chm_p2r_1_smoothed, ttops_chm_p2r_1_smoothed)
  print('segmenting')
  las <- segment_trees(las, algo)
  # get crowns
  #m <- ~list(avgI = median(Z))
  #m <- ~list(median = median(Z), mean = mean(Z), max = max(Z), H90TH = H90TH(Z))
  #m func = 
  crowns <- crown_metrics(las, func = .stdmetrics, geom = "convex")
  print('write crowns')
  st_write(crowns, outcrowns)
}

segment(laz)


