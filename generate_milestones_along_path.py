# -*- coding: utf-8 -*-
"""
Created on Wed Aug 23 17:38:50 2023

@author: jack

pip install geographiclib numpy pandas geopandas haversine vincenty geopy shapely
"""
from geographiclib.geodesic import Geodesic
# import gpxpy
import numpy as np
import pandas as pd
import geopandas as gp
# import matplotlib.pyplot as plt
import haversine as hs
from vincenty import vincenty
from geopy.distance import geodesic, great_circle
from math import sin, cos, sqrt, atan2, radians, degrees
from geopandas import GeoDataFrame
from shapely.geometry import Point
import haversine as hs
import os

# A = (44.27364400, -121.17116400)  # Point A (lat, lon)
# B = (44.27357900, -121.17006800)  # Point B (lat, lon)
# s = 10  # Distance (m)

# # Define the ellipsoid
geod = Geodesic.WGS84
g_circle = great_circle()
geo_desic = geodesic()
# # Solve the Inverse problem
# inv = geod.Inverse(A[0], A[1], B[0], B[1], Geodesic.AZIMUTH)
# azi1 = inv['azi1']
# print('Initial Azimuth from A to B = ' + str(azi1))

# # Solve the Direct problem
# dir = geod.Direct(A[0], A[1], azi1, s)
# C = (dir['lat2'], dir['lon2'])
# print('C = ' + str(C))


# great circle
# bearing = atan2(sin(long2 - long1)*cos(lat2), cos(lat1)*sin(lat2) - sin(lat1)*cos(lat2)*cos(long2 - long1))
# bearing = degrees(bearing)
# bearing = (bearing + 360) % 360

# Approximate radius of earth in km
# R = 6373.0
R = 6378137
#file_url = "D:/geo/dongjiang/dongjiang_river_osm_sorted_dissolved.shp"
file_url = r"c:\Users\jack\Desktop\test\xiangjiang_river_osm_sorted_dissolved.shp"


def cal_great_circle_distance(lat1, lon1, lat2, lon2) -> float:
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance


# def gpx2df(gpx):
#     data = gpx.tracks[0].segments[0].points

#     # Start Position
#     start = data[0]
#     # End Position
#     finish = data[-1]

#     df = pd.DataFrame(columns=["lon", "lat", "alt", "time"])
#     for point in data:
#         df = df.append(
#             {
#                 "lon": point.longitude,
#                 "lat": point.latitude,
#                 "alt": point.elevation,
#                 "time": point.time,
#             },
#             ignore_index=True,
#         )
#     df["time"] = df["time"].astype(str).str[:-6]
#     df["time"] = pd.to_datetime(df["time"], dayfirst=True)
#     return data, df


def cal_great_circle_bearing2(pointA, pointB):
    if (type(pointA) != tuple) or (type(pointB) != tuple):
        raise TypeError("Only tuples are supported as arguments")

    lat1 = radians(pointA[0])
    lat2 = radians(pointB[0])

    diffLong = radians(pointB[1] - pointA[1])

    x = sin(diffLong) * cos(lat2)
    y = cos(lat1) * sin(lat2) - (sin(lat1) * cos(lat2) * cos(diffLong))

    initial_bearing = atan2(x, y)

    # Now we have the initial bearing but math.atan2 return values
    # from -180° to + 180° which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below
    initial_bearing = degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing


# 有问题 弃用 deprecated
def cal_great_circle_bearing(lat1, lon1, lat2, lon2) -> float:
    bearing = atan2(
        sin(lon2 - lon1) * cos(lat2),
        cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(lon2 - lon1),
    )
    bearing = degrees(bearing)
    bearing = (bearing + 360) % 360
    return bearing


def cal_bearing(lat1, lon1, lat2, lon2) -> float:
    # geodesic
    # return geod.Inverse(lat1, lon1, lat2, lon2, Geodesic.AZIMUTH)['azi1']
    # return cal_great_circle_bearing(lat1, lon1, lat2, lon2)  # great circle
    return cal_great_circle_bearing2((lat1, lon1), (lat2, lon2))


def cal_direction(lat1, lon1, bearing, distance):
    # geodesic
    # return geo_desic.destination((lat1, lon1), bearing, distance/1000)
    # great circle
    return g_circle.destination((lat1, lon1), bearing, distance / 1000)


def haversine_distance(lat1, lon1, lat2, lon2) -> float:
    distance = hs.haversine(
        point1=(lat1, lon1), point2=(lat2, lon2), unit=hs.Unit.METERS
    )
    return distance


def geopy_distance(lat1, lon1, lat2, lon2) -> float:
    # distance = geodesic((lat1, lon1), (lat2, lon2)).meters  # geodesic
    # distance = gd.measure((lat1, lon1), (lat2, lon2))
    # distance = great_circle((lat1, lon1), (lat2, lon2)).meters #great circle R = 6371.009
    # distance = haversine_distance(lat1, lon1, lat2, lon2)
    distance = cal_great_circle_distance(
        lat1, lon1, lat2, lon2
    )  # great circle R = 6378137
    return distance


gdf = gp.read_file(file_url)

points = gdf.apply(lambda x: [y for y in x["geometry"].coords], axis=1)[0]

route_df = pd.DataFrame(points, columns=["lon", "lat"])
distances = [np.nan]

for i in range(len(route_df)):
    if i == 0:
        continue
    else:
        distances.append(
            geopy_distance(
                lat1=route_df.iloc[i - 1]["lat"],
                lon1=route_df.iloc[i - 1]["lon"],
                lat2=route_df.iloc[i]["lat"],
                lon2=route_df.iloc[i]["lon"],
            )
        )

route_df["distance"] = distances

mile_stones_df = pd.DataFrame(
    columns=["lon", "lat", "name", "seg_no", "bearing", "seg_distance"]
)
new_dict = {
    "lon": route_df.iloc[0]["lon"],
    "lat": route_df.iloc[0]["lat"],
    "name": "0",
    "seg_no": 0,
    "bearing": 0,
    "seg_distance": route_df.iloc[0]["distance"],
}
# mile_stones_df = mile_stones_df.append(new_dict, ignore_index=True)
mile_stones_df = pd.concat(
    [mile_stones_df, pd.DataFrame([new_dict])], ignore_index=True
)

interval_distance = 1000.0
a_distance = 0
bearing = None
mile_stones_i = int(1)
for i in range(len(route_df)):
    if i == 0:
        continue
    pre_distance = a_distance
    a_distance += distances[i]
    lat1 = route_df.iloc[i - 1]["lat"]
    lon1 = route_df.iloc[i - 1]["lon"]
    lat2 = route_df.iloc[i]["lat"]
    lon2 = route_df.iloc[i]["lon"]

    while a_distance >= interval_distance:
        if a_distance == interval_distance:
            new_dict = {
                "lon": route_df.iloc[i]["lon"],
                "lat": route_df.iloc[i]["lat"],
                "name": str(mile_stones_i),
                "seg_no": i,
                "bearing": bearing,
                "seg_distance": interval_distance * mile_stones_i,
            }
            # mile_stones_df = mile_stones_df.append(new_dict, ignore_index=True)
            mile_stones_df = pd.concat(
                [mile_stones_df, pd.DataFrame([new_dict])], ignore_index=True
            )
            a_distance = 0
            bearing = None
        else:
            # 只要不是正好落在track point上（概率极低），就是需要连接好几个点，从这一段上拱出一点点，所以绝大多数需要截取（减去）
            # 少数大长段，只有第二次以上进while才不用减去，直接用interval_distance
            distance = interval_distance - pre_distance
            if bearing != None:
                # not first time in while loop
                lat1 = mile_stones_df.iloc[mile_stones_i - 1]["lat"]
                lon1 = mile_stones_df.iloc[mile_stones_i - 1]["lon"]
                distance = interval_distance
            if bearing == None:
                bearing = cal_bearing(lat1, lon1, lat2, lon2)

            point = cal_direction(lat1, lon1, bearing, distance)
            a_distance -= interval_distance
            new_dict = {
                "lon": point.longitude,
                "lat": point.latitude,
                "name": str(mile_stones_i),
                "seg_no": i,
                "bearing": bearing,
                "seg_distance": interval_distance * mile_stones_i + a_distance,
            }
            # mile_stones_df = mile_stones_df.append(new_dict, ignore_index=True)
            mile_stones_df = pd.concat(
                [mile_stones_df, pd.DataFrame([new_dict])], ignore_index=True
            )
        mile_stones_i += 1

    bearing = None

geometry = [Point(xy) for xy in zip(mile_stones_df.lon, mile_stones_df.lat)]
gdf = GeoDataFrame(mile_stones_df, crs="EPSG:4326", geometry=geometry)
base, ext = os.path.splitext(file_url)
distance = mile_stones_df.iloc[-1]["seg_distance"]
gdf.to_file("%s_milestones_%0.2fkm.shp" % (base, distance / 1000), encoding="utf-8")
