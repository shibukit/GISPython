# -*- coding: utf-8 -*-
"""
Created on Sun Oct 22 10:42:36 2023

開発者向けの仕様書
    https://www.esrij.com/getting-started/learn-more/shapefile/

@author: GIS技術者
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import os
import struct
from enum import IntEnum

pd.options.display.max_rows = 100
pd.options.display.max_columns = 100

# パスなど--------------------------------------------------------------
# 予報区等GISデータの一覧
# https://www.data.jma.go.jp/developer/gis.html
shp_plg_path = r"D:\data\23\1001_気象庁\予報区等GISデータ\市町村等（地震津波関係）\20190125_AreaInformationCity_quake_GIS\市町村等（地震津波関係）.shp"
shp_lin_path = r"D:\data\23\1001_気象庁\予報区等GISデータ\津波予報区\20190125_AreaTsunami_GIS\津波予報区.shp"
# 国土数値情報 市区町村役場データ
# https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-P34.html
shp_pnt_path = r"D:\data\23\1002_国土数値情報\市区町村役場データ\H26\新潟\P34-14_15_GML\P34-14_15.shp"
# -------------------------------------------------------------------




class ShpType(IntEnum):
    NullShape   =  0
    Point       =  1
    PolyLine    =  3
    Polygon     =  5
    MultiPoint  =  8
    PointZ      = 11
    PolyLineZ   = 13
    PolygonZ    = 15
    MultiPointZ = 18
    PointM      = 21
    PolyLineM   = 23
    PolygonM    = 25
    MultiPointM = 28
    MultiPatch  = 31



class Shp:       
    """
    .shpファイルの読み込みクラス
    """
    def __init__(self, shp_fullpath):
        self.fullpath = shp_fullpath
        self.filename = os.path.basename(shp_fullpath)
        
        fh1_tuple, fh2_tuple = self._getFileHeader()
        self.fileCode    = fh1_tuple[0] 
        self.tmp11       = fh1_tuple[1]
        self.tmp12       = fh1_tuple[2]
        self.tmp13       = fh1_tuple[3]
        self.tmp14       = fh1_tuple[4]
        self.tmp15       = fh1_tuple[5]
        self.fileLength  = fh1_tuple[6]
        self.fileVersion = fh2_tuple[0]
        self.shpType     = fh2_tuple[1]
        self.Xmin        = fh2_tuple[2]
        self.Ymin        = fh2_tuple[3]
        self.Xmax        = fh2_tuple[4]
        self.Ymax        = fh2_tuple[5]
        self.Zmin        = fh2_tuple[6]
        self.Zmax        = fh2_tuple[7]
        self.Mmin        = fh2_tuple[8]
        self.Mmax        = fh2_tuple[9]


    def _getFileHeader(self):
        """ファイルヘッダーを読み込む
        
        Returns:
            tuple: ビッグエンディアン部分のファイルヘッダー情報, リトルエンディアン部分のファイルヘッダー情報
        """
        with open(self.fullpath, "rb") as f:
            file_header1 = f.read(28)
            file_header2 = f.read(72)
            # バイト列をパックされたバイナリデータとして解釈する
            # https://docs.python.org/ja/3/library/struct.html
            file_header1_tuple = struct.unpack(">7i", file_header1)
            file_header2_tuple = struct.unpack("<2i8d", file_header2)
            return file_header1_tuple, file_header2_tuple
        
        
    def _getRecordHeader(self, recordNumber):
        """指定されたレコード番号のヘッダー情報を読み込む
        
        Args:
            recordNumber (int): 1から始まるレコード番号

        Returns:
            tuple: レコード番号, そのレコードのコンテンツまでのオフセット, そのレコードのコンテンツ長
        """
        with open(self.fullpath, "rb") as f:
            # ファイル先頭から、ファイルヘッダー分読み飛ばす
            seek_byte = 100
            record_header_byte = 8
            f.seek(seek_byte, 0)
            
            for i in np.arange(recordNumber):
                record_header = f.read(record_header_byte)
                record_number, content_length = struct.unpack(">2i", record_header)
                # ワードという単位になっているので、バイトに変換
                content_length_byte = content_length * 2
                # 現在のレコードのコンテンツ先頭から、次のレコードのヘッダーに移動
                f.seek(content_length_byte, 1)
                seek_byte = seek_byte + record_header_byte + content_length_byte
                
            
            seek_byte -= content_length_byte
            print(i, record_number, seek_byte, content_length_byte)
        return record_number, seek_byte, content_length_byte
    
    
    def _getPoint(self, seek_byte, content_length_byte):
        """対象レコードのコンテンツ内のポイントデータを読み込む
        
        Args:
            seek_byte (int): 対象レコードのコンテンツまでのオフセット
            content_length_byte (int): 対象レコードのコンテンツ長

        Returns:
            tuple: シェープ・タイプ, X, Y
        """
        with open(self.fullpath, "rb") as f:
            # ファイル先頭から、対象レコードの先頭まで読み飛ばす
            f.seek(seek_byte, 0)
            point_bainary = f.read(content_length_byte)
            shp_type, x, y = struct.unpack("<i2d", point_bainary)
        
        return shp_type, x, y
    

    def _getPolyLine(self, seek_byte, content_length_byte):
        """対象レコードのコンテンツ内のラインデータを読み込む
        
        Args:
            seek_byte (int): 対象レコードのコンテンツまでのオフセット
            content_length_byte (int): 対象レコードのコンテンツ長

        Returns:
            tuple: シェープ・タイプ, Box(Xmin, Ymin, Xmax, Ymax), NumParts, NumPoints, Parts, Points
        """
        header_byte = 4 + 8*4 + 4 + 4
        with open(self.fullpath, "rb") as f:
            # ファイル先頭から、対象レコードの先頭まで読み飛ばす
            f.seek(seek_byte, 0)
            line_header_bainary = f.read(header_byte)
            shp_type, xmin, ymin, xmax, ymax, num_parts, num_points = struct.unpack("<i4d2i", line_header_bainary)
            
            line_parts_bainary = f.read(num_parts*4)
            parts  = struct.unpack(f"<{num_parts}i", line_parts_bainary)
            points  = [struct.unpack("<2d", f.read(16)) for i in range(num_points)]
        
        return shp_type, xmin, ymin, xmax, ymax, num_parts, num_points, parts, points


    def _getPolygon(self, seek_byte, content_length_byte):
        """対象レコードのコンテンツ内のポリゴンデータを読み込む
        
        Args:
            seek_byte (int): 対象レコードのコンテンツまでのオフセット
            content_length_byte (int): 対象レコードのコンテンツ長

        Returns:
            tuple: シェープ・タイプ, Box(Xmin, Ymin, Xmax, Ymax), NumParts, NumPoints, Parts, Points
        """
        # ポリゴンとラインは、レコード内のコンテンツの構造が一緒なので、ラインと同じ方法で読み込める
        return self._getPolyLine(seek_byte, content_length_byte)




    def getRecordContent(self, recordNumber):
        """指定されたレコード番号のデータを読み込む
        
        Args:
            recordNumber (int): 1から始まるレコード番号

        Returns:
            tuple: 指定されたレコードのコンテンツ内容
        """
        
        record_number, seek_byte, content_length_byte = self._getRecordHeader(recordNumber)
                
        if ShpType.Point == self.shpType:
            return self._getPoint(seek_byte, content_length_byte)
        
        elif ShpType.PolyLine == self.shpType:
            return self._getPolyLine(seek_byte, content_length_byte)
        
        elif ShpType.Polygon == self.shpType:
            return self._getPolygon(seek_byte, content_length_byte)
            
        else:
            print(self.shpType, "については未実装です。")


if __name__ == "__main__":
    # ポイント--------------------------------------
    pnt = Shp(shp_pnt_path)
    # ヘッダー
    print(pnt.fileCode)
    print(pnt.tmp11, pnt.tmp12, pnt.tmp13, pnt.tmp14, pnt.tmp15)
    print(pnt.fileLength)
    print(pnt.fileVersion, pnt.shpType, ShpType(pnt.shpType))
    print(pnt.Xmin, pnt.Xmax, pnt.Ymin, pnt.Ymax, pnt.Zmin, pnt.Zmax, pnt.Mmin, pnt.Mmax)
    # レコード
    pnt_shp_type, pnt_x, pnt_y = pnt.getRecordContent(2)
    print(pnt_shp_type, ShpType(pnt_shp_type),  pnt_x, pnt_y)


    # ライン--------------------------------------
    lin = Shp(shp_lin_path)
    # ヘッダー
    print(lin.fileCode)
    print(lin.tmp11, lin.tmp12, lin.tmp13, lin.tmp14, lin.tmp15)
    print(lin.fileLength)
    print(lin.fileVersion, lin.shpType, ShpType(lin.shpType))
    print(lin.Xmin, lin.Xmax, lin.Ymin, lin.Ymax, lin.Zmin, lin.Zmax, lin.Mmin, lin.Mmax)
    # レコード
    lin_data = lin.getRecordContent(1)
    lin_shp_type, lin_xmin, lin_ymin, lin_xmax, lin_ymax, lin_num_parts, lin_num_points = lin_data[:7]
    lin_parts  = lin_data[7]
    lin_points = lin_data[8]
    print(lin_shp_type, ShpType(lin_shp_type), lin_xmin, lin_ymin, lin_xmax, lin_ymax, lin_num_parts, lin_num_points)
    # データが多いので、インデックスを用いてリストの最初の3つのみprint
    print(lin_parts[:3])
    print(lin_points[:3])


    # ポリゴン--------------------------------------
    plg = Shp(shp_plg_path)
    # ヘッダー
    print(plg.fileCode)
    print(plg.tmp11, plg.tmp12, plg.tmp13, plg.tmp14, plg.tmp15)
    print(plg.fileLength)
    print(plg.fileVersion, plg.shpType, ShpType(plg.shpType))
    print(plg.Xmin, plg.Xmax, plg.Ymin, plg.Ymax, plg.Zmin, plg.Zmax, plg.Mmin, plg.Mmax)
    # レコード
    plg_data = plg.getRecordContent(77+1)
    plg_shp_type, plg_xmin, plg_ymin, plg_xmax, plg_ymax, plg_num_parts, plg_num_points = plg_data[:7]
    plg_parts  = plg_data[7]
    plg_points = plg_data[8]
    print(plg_shp_type, ShpType(plg_shp_type), plg_xmin, plg_ymin, plg_xmax, plg_ymax, plg_num_parts, plg_num_points)
    # データが多いので、インデックスを用いてリストの最初の3つのみprint
    print(plg_parts[:3])
    print(plg_points[:3])







