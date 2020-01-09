# ---
# convert_sargassum_kml.R
# title: "Extract Sargassum Data from OceanCleaner KMLs"
# author: "Allison Bailey"
# date: "9/17/2019"
# ---

# This script is used to extract Sargassum data downloaded from Ocean Cleaner's website
# 2018: http://sargassummonitoring.com/2018-sargassum-sargasses-sargazo/
# current (2019): http://sargassummonitoring.com/
# Data were downloaded as KML files from the website
# Data are stored as points.  
# One file per year for presence and one for absence observations
# 
# Process data to create additional columns
# Convert to GeoPackage layers - one for each year

### Load Packages
library(here)
library(sf)
library(tidyverse)
library(lubridate)

# Read data from KML
data_dir <- "data/oceancleaner"
presence_2018_kml <- st_read(here::here(data_dir,"2018 Beaches with sargassum seaweeds - Plages avec algues sargasses.kml"), quiet = TRUE)
absence_2018_kml <- st_read(here::here(data_dir,"2018 - Beaches without sargassum - Plages sans sargasses - Playas sin sargazo.kml"), quiet = TRUE)
presence_2019_kml <- st_read(here::here(data_dir,"2019 Beaches with sargassum - Plages avec sargasses - Playa con sargazo.kml"), quiet = TRUE)
absence_2019_kml <- st_read(here::here(data_dir,"2019 - Beaches without sargassum - Plages sans sargasses - Playas sin sargazo.kml"), quiet = TRUE)


# Pattern for dates in the format of DD/MM/YYYY or MM/DD/YYYY or MM/YYYY
#  Does not check to confirm that they are valid dates, just the right format
date_dmy <- "[0-3][0-9]/[0-1][0-9]/[0-9]{4}"  # DD/MM/YYYY (or MM/DD/YY for some dates)
date_my <- "[0-1][0-9]/[0-9]{4}"  # MM/YYYY

# Preprocessing function for KML dataframe to modify/add a few columns and filter
process_kml <- function(kml_df, occur_type){
  # Calculate source_date column based on type of date format found
  processed_df <- kml_df %>%
    transmute(
      # rename KML default column names
      name_kml = Name,
      desc_kml = Description
    ) %>%
    mutate(
      # Extract any date values from the Name column
      source_date = case_when(
        str_detect(name_kml, date_dmy) ~ dmy(str_extract(name_kml, date_dmy)),
        str_detect(name_kml, date_my) ~ myd(str_extract(name_kml, date_my), truncated = 1)
      )
    ) %>%
    mutate(
      # Create new column to capture the date type
      date_type = case_when(
        str_detect(name_kml, date_dmy) ~ "DMY",
        str_detect(name_kml, date_my) ~ "MY"   
      )
    ) %>%
    mutate(
      # Column for sargassum occurrence (present/absent)
      occur = occur_type
    ) %>%
    filter(
      # remove record referencing other data set
      str_detect(name_kml, "FOR 2019", negate = TRUE)
    )
  return(processed_df)
}

# Preprocess the individual KMLs
presence_2018 <- process_kml(presence_2018_kml, "present")
absence_2018 <- process_kml(absence_2018_kml, "absent")
presence_2019 <- process_kml(presence_2019_kml, "present")
absence_2019 <- process_kml(absence_2019_kml, "absent")

# Combine all data frames together
sargassum_oc_2018_2019 <- rbind(presence_2018, absence_2018, presence_2019, absence_2019)

# Output to Geopackage
gpkg_filename = "sargassum_oceancleaner.gpkg"
lyr_name = "sargassum_oc_2018_20190919"
gpkg_file = here::here(data_dir,gpkg_filename)
# overwrites exist layer, but not geopackage
# st_write(sargassum_oc_2018_2019, dsn=gpkg_file, layer=lyr_name, layer_options="OVERWRITE=YES") 
# Overwrites Geopackage
st_write(sargassum_oc_2018_2019, dsn=gpkg_file, layer=lyr_name, delete_dsn=TRUE)


