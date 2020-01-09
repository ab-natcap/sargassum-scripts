""" sema_sargassum.py

Author: Allison Bailey
Date: 2019-10-11

Pull data about sargassum cleanup from website:
http://sargazo2018.semaqroo.gob.mx/
http://sema.qroo.gob.mx/sistemas/inira.semaqroo.gob.mx/mapa_dig.php?id=39
http://sema.qroo.gob.mx/sistemas/inira.semaqroo.gob.mx/tramite_sl.php?id="+ficha;

This works:
curl -X POST -F 'AJAX=4' -F 'fecha=2018-10-10' http://sema.qroo.gob.mx/sistemas/inira.semaqroo.gob.mx/mapa_dig.php
"""

import json
import requests
import os
import csv
import pandas as pd
import geopandas as gpd
import shapely
import fiona

def get_dates(file):
    dates = [line.rstrip('\n') for line in open(file)]
    return dates

work_dir = "/Users/arbailey/natcap/mar/sargassum/data/sema"

# Get clean up dates from a file (originally pulled from the website
date_file = os.path.join(work_dir,"cleanup_dates2018.txt")
dates = get_dates(date_file)
# date2query = '2018-10-10'   # date format example

# output data and file
out_data = []
out_file = os.path.join(work_dir, "cleanup_data2018.csv")

for date2query in dates:
    # parameters for post request
    files = {
        'AJAX': (None, '4'),
        'fecha': (None, date2query),
    }
    # Post Request to SEMA sargassum site
    response = requests.post('http://sema.qroo.gob.mx/sistemas/inira.semaqroo.gob.mx/mapa_dig.php', files=files)
    # Convert response json to python list of list
    cleanup_data = json.loads(response.text)["datos"]
    print(cleanup_data)

    # Get elements for each cleanup record
    for beach in cleanup_data:
        record_id = beach[7]
        qa_flag = 0 # Set flag to 1 if there is an issue with the record
        clean_date = beach[0]
        beach_name = beach[1]
        # Volume and Length error checking
        # sometimes have unit strings, so remove them
        # If it's not a float, set the value to 0 and flag in qa_flag
        try:
            cubic_meters = float(beach[2].split()[0])
        except ValueError:
            cubic_meters = 0
            qa_flag = 1
        try:
            lineal_meters = beach[3].split()[0]
        except IndexError:
            lineal_meters = beach[3]
        try:
            float(lineal_meters)
        except ValueError:
            lineal_meters = 0
            qa_flag = 1
        # -- Coordinates -- need lots of error checking
        # - Start coordinates
        start_end_coords = beach[5]
        start_coords = start_end_coords[0]
        y_start = start_coords[0]
        x_start = start_coords[1]
        # skip records that can't be converted to float, i.e. 2070456,000
        try:
            y_start = float(y_start)
            x_start = float(x_start)
        except ValueError:
            continue
        # If the start coordinates are out bounds, skip this record
        # if abs(float(y_start)) > 180.0 or abs(float(x_start)) > 90.0:
        # if not(85 <= abs(x_start) <= 90 or 15 <= abs(y_start) <= 23):
        if abs(x_start) < 85 or abs(x_start) > 90 or abs(y_start) < 15 or abs(y_start) > 23:
            continue
        # Longitude should be negative
        if x_start > 0:
            x_start = -1 * x_start
            qa_flag = 1
        # - End coordinates
        try:
            end_coords = start_end_coords[1]
            y_end = end_coords[0]
            x_end = end_coords[1]
        except IndexError:
            # if end coordinate missing, set it to same as start coordinate
            end_coords = start_coords
            y_end = y_start
            x_end = x_start
            qa_flag = 1
        # skip records that can't be converted to float, i.e. 2070456,000
        try:
            y_end = float(y_end)
            x_end = float(x_end)
        except ValueError:
            continue
        # If the end coordinates are out bounds, skip this record
        # if abs(float(y_end)) > 180.0 or abs(float(x_end)) > 90.0 or float(y_end) == 0 or float(x_end) == 0:
        if abs(x_end) < 85 or abs(x_end) > 90 or abs(y_end) < 15 or abs(y_end) > 23:
            continue
        # Longitude should be negative
        if x_end > 0:
            x_end = -1 * x_end
            qa_flag = 1

        # Add record to out_data list
        out_data.append([record_id, clean_date, beach_name, cubic_meters, lineal_meters, x_start, y_start, x_end, y_end, qa_flag])

# write out_data list to csv file
with open(out_file, mode='w') as cleanup_file:
    cleanup_writer = csv.writer(cleanup_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    for record in out_data:
        cleanup_writer.writerow(record)

# Write out_data to pandas data frame
columns = [
    'record_id',
    'clean_date',
    'beach_name',
    'cubic_meters',
    'lineal_meters',
    'x_start',
    'y_start',
    'x_end',
    'y_end',
    'qa_flag'
]
# sargassum_df = pd.DataFrame(out_data, columns = columns)
# Or read it from the created csv
sargassum_df = pd.read_csv(out_file, names=columns)
sargassum_df[['clean_date']] = sargassum_df[['clean_date']].astype('datetime64[ns]')
print(sargassum_df.head())
print(sargassum_df.info())

# # Option 1 - create Shapely points
# start_points = gpd.points_from_xy(sargassum_df.x_start, sargassum_df.y_start)
# # Same as above
# start_points = [shapely.geometry.Point(x, y) for x, y in zip(sargassum_df.x_start, sargassum_df.y_start)]
# end_points = gpd.points_from_xy(sargassum_df.x_end, sargassum_df.y_end)

# Option 2 - Create tuples of x/y coordinates
start_coords = [(x,y) for x,y in zip(sargassum_df.x_start, sargassum_df.y_start)]
end_coords = [(x,y) for x,y in zip(sargassum_df.x_end, sargassum_df.y_end)]
# beach_lines = [shapely.geometry.LineString([start, end]) for start,end in zip(start_coords, end_coords)]

# Create Geodataframe with the dataframe and 2-point line created from start and end coordinates
sargassum_gdf = gpd.GeoDataFrame(
    sargassum_df, geometry=[shapely.geometry.LineString([start, end]) for start, end in zip(start_coords, end_coords)]
)

# Set the GeoDataFrame's coordinate system to WGS84 (i.e. epsg code 4326)
sargassum_gdf.crs = fiona.crs.from_epsg(4326)

print(sargassum_gdf.head(20))
print(sargassum_gdf.info())
print(sargassum_gdf.dtypes)

# WRite to Geopackage
gpkg_file = os.path.join(work_dir,"sargassum_sema.gpkg")
layer = "sargassum_sema2018"
sargassum_gdf.to_file(gpkg_file, layer=layer, driver="GPKG")

