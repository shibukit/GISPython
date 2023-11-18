# -*- coding: utf-8 -*-
"""
Created on Sun Oct 22 10:35:21 2023

@author: GIS技術者
"""

import geopandas as gpd
import pandas as pd

pd.options.display.max_rows = 100
pd.options.display.max_columns = 100

# パスなど--------------------------------------------------------------
# 予報区等GISデータの一覧
# https://www.data.jma.go.jp/developer/gis.html
shp_lin_path = r"D:\data\23\1001_気象庁\予報区等GISデータ\津波予報区\20190125_AreaTsunami_GIS\津波予報区.shp"
shp_plg_path = r"D:\data\23\1001_気象庁\予報区等GISデータ\市町村等（地震津波関係）\20190125_AreaInformationCity_quake_GIS\市町村等（地震津波関係）.shp"
# 国土数値情報 市区町村役場データ
# https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P34.html
shp_pnt_path = r"D:\data\23\1002_国土数値情報\市区町村役場データ\H26\新潟\P34-14_15_GML\P34-14_15.shp"
# -------------------------------------------------------------------


gdf_lin = gpd.read_file(shp_lin_path, encoding="utf-8")
gdf_plg = gpd.read_file(shp_plg_path, encoding="utf-8")
gdf_pnt = gpd.read_file(shp_pnt_path, encoding="cp932")

gdf_plg_notna = gdf_plg[gdf_plg["regionname"].notna()]

# 新潟市を抽出
niigata_plg_gdf = gdf_plg_notna[gdf_plg_notna["regioncode"].str.startswith("1510")]

print(niigata_plg_gdf)
# niigata_plg_gdf.plot()
