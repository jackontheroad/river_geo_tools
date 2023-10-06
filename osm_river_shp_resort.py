# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.

pip install geopandas pandas shapely
"""

import geopandas
import pandas as pd
import os

# from shapely.geometry import Point
# from shapely import from_wkb, from_wkt
from shapely.ops import split

# url = "D:\geo\guijiang_final\guijiang_river_osm.shp"
# url = "D:/geo/dongjiang/dongjiang_river_osm.shp"
url = r"c:\Users\jack\Desktop\test\emuerhe_network_osm.shp"
# url = r"D:/geo/xiangjiang/yongminghe_river_osm.shp"

# start_osm_id = "923896248"
# end_osm_ids = ["38802349"]
start_osm_id = "674455140"
end_osm_ids = ["229395587","229395588","27803429"]
abnormal_osm_ids = []

df = geopandas.read_file(url)

df = df.reset_index()
kvDict = {}
bakKvDict = {}
for index, row in df.iterrows():
    osm_id = row["osm_id"]
    if osm_id in abnormal_osm_ids:
        continue
    first, last = row["geometry"].boundary.geoms
    entity = {
        "data": row,
        "next": None,
        "last": None,
        "lastPointWkt": last.wkt,
        "osm_id": row["osm_id"],
        "lastPoint": last,
    }
    if kvDict.get(first.wkt) != None:
        print(
            "Segments %s and %s have the same starting point, you may want to solve it manually. Selecting route randomly by default"
            % (kvDict.get(first.wkt)["osm_id"], osm_id)
        )
        print(
            "片段 %s 和 %s 有共同的起始点, 你或许需要手动解决一下，默认随机选择路线。"
            % (kvDict.get(first.wkt)["osm_id"], osm_id)
        )
        bakKvDict[first.wkt] = entity
        continue
    kvDict[first.wkt] = entity


theFirstLineKey = ""

for key, val in kvDict.items():
    lastPointWkt = val["lastPointWkt"]
    nextLine = kvDict.get(lastPointWkt, None)
    if nextLine is not None:
        val["next"] = nextLine
        nextLine["last"] = val

for key, val in bakKvDict.items():
    lastPointWkt = val["lastPointWkt"]
    nextLine = kvDict.get(lastPointWkt, None)
    if nextLine is not None:
        val["next"] = nextLine

newDataFrame = []
iterator = None
index = 0
issueList = []
issue1List = []
sortedOsmIdList = []
for key, val in kvDict.items():
    lastLine = val["last"]
    nextLine = val["next"]
    # if lastLine is None and nextLine is not None:
    if lastLine is None:
        if start_osm_id is not None and val["osm_id"] == start_osm_id:
            val["data"]["index"] = index
            val["data"]["sort"] = index
            index = index + 1
            newDataFrame.append(val["data"])
            iterator = val
            issueList.append(val)
            # print('----------------------- osm_id', val['osm_id'])
            break
    elif lastLine is None or nextLine is None:
        issue1List.append(val)

# 处理下一段
while iterator is not None and iterator["next"] is not None:
    iterator = iterator["next"]
    iterator["data"]["index"] = index
    iterator["data"]["sort"] = index
    index = index + 1
    newDataFrame.append(iterator["data"])
    sortedOsmIdList.append(iterator["osm_id"])

# 如果有首尾连不上的片段，意思是一个片段起始端 跟另一个片段的中间部分相连，像树枝一样，下边代码将把像树枝一样的连接，切断无用部分，改为首尾相连。
# some line segments they are not connected by end to end but they are connected by one seg's end to the other seg's middle part like a branch.
# the following code will break the segment from connecting point and drop the useless part to create a seg connection by end to end.
while iterator["osm_id"] not in end_osm_ids:
    print("-----------------lastPointWkt", iterator["lastPointWkt"])
    for key, val in kvDict.items():
        osm_id = val["osm_id"]
        # print('osm_id-----test-----', osm_id)
        line = val["data"]["geometry"]
        if osm_id not in sortedOsmIdList and iterator["lastPoint"].within(line):
            print("----------------------- next osm_id", val["osm_id"])
            val["data"]["geometry"] = split(line, iterator["lastPoint"]).geoms[1]
            iterator["next"] = val
            break
    if iterator["next"] is None:
        for key, val in bakKvDict.items():
            osm_id = val["osm_id"]
            # print('osm_id-----test-----', osm_id)
            line = val["data"]["geometry"]
            if osm_id not in sortedOsmIdList and iterator["lastPoint"].within(line):
                print("----------------------- next osm_id", val["osm_id"])
                val["data"]["geometry"] = split(line, iterator["lastPoint"]).geoms[1]
                iterator["next"] = val
                break
    if iterator["next"] is None:
        print(
            "----------------------error----------------- osm_id--", iterator["osm_id"]
        )
        break
    # 处理下一段
    # processing next segment
    while iterator["next"] is not None:
        iterator = iterator["next"]
        iterator["data"]["index"] = index
        iterator["data"]["sort"] = index
        index = index + 1
        newDataFrame.append(iterator["data"])
        sortedOsmIdList.append(iterator["osm_id"])


print("..............writing to file.................")
# df2 = pd.DataFrame(newDataFrame)
df2 = geopandas.GeoDataFrame(newDataFrame,crs="EPSG:4326")
# df2.to_file("sorted.shp")
df2.to_file(os.path.splitext(url)[0]+'_sorted.shp', encoding='utf-8')
