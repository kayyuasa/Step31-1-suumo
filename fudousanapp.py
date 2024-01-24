#ライブラリをimport
import streamlit as st
from PIL import Image #イメージを表示
import folium
from streamlit_folium import folium_static
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
load_dotenv()
import os

SPREADSHEET_KEY = os.getenv('SPREADSHEET_KEY')

scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
Auth = 'suumo-step3-1-33c7f663e7dd.json'
credentials = ServiceAccountCredentials.from_json_keyfile_name(Auth, scope)
gs = gspread.authorize(credentials)
worksheet = gs.open_by_key(SPREADSHEET_KEY).worksheet("Tokyo")
unique_data = pd.DataFrame(worksheet.get_all_values(), columns=worksheet.get_all_values()[0])
unique_data = unique_data.drop(unique_data.index[0])

#CSVからデータを取ってくる

# CSVファイルのパス
#csv_file_path = 'unique_output.csv'

# CSVファイルを読み込む
#unique_data = pd.read_csv(csv_file_path)  

# 国土地理院のAPIを利用して緯度と経度を取得する関数
def get_coordinates(address):
    response = requests.get(f"https://msearch.gsi.go.jp/address-search/AddressSearch?q={urllib.parse.quote(address)}")
    if response.json():
        lon, lat = response.json()[0]["geometry"]["coordinates"]
        return [lat, lon]
    else:
        return [None, None]
    


#<Streamlitでフロント画面を作成>------ここから

st.title("都市部不動産一発検索アプリ") # タイトル

image = Image.open('image1.png') #画像挿入
st.image(image, caption=None)

st.markdown("お好みのエリア、家賃、間取りを選択してください")

st.sidebar.header("検索条件を選び「検索」をクリック")

area = st.sidebar.multiselect(
    "エリアを選択",
    ['港区', '目黒区', '品川区','千代田区','中央区','新宿区','文京区','渋谷区','台東区','墨田区','江東区','荒川区','足立区','葛飾区','江戸川区','大田区','世田谷区','中野区','杉並区','練馬区','豊島区','北区','板橋区'],
    ['港区', '目黒区', '品川区']
)

expense = st.sidebar.slider(
    '家賃の範囲を選択（万円）',
    min_value=0,  # Minimum value
    max_value=50, # Maximum value
    value=(10, 25),  # Default range
    step=1  # Step size
)

madori = st.sidebar.multiselect(
    '間取り',
    ['1LDK', '2LDK', '3LDK', '4LDK', '1SLDK', '2DK', '2K', '1K','1DK'],
    ['2DK', '2LDK','1LDK']  # オプションの中からデフォルト選択を指定
)

# ボタンを押した時に検索
if st.sidebar.button("検索") :

    filtered_data = unique_data.copy()

    # エリアに基づいてフィルタリング
    if area:
        # 選択されたエリアのリストから正規表現パターンを作成
        regex_pattern = '|'.join([re.escape(a) for a in area])
        # 選択されたエリアのいずれかが含まれている行をフィルタリング
        filtered_data = filtered_data[filtered_data['アドレス'].str.contains(regex_pattern, regex=True)]

    # '家賃' 列の数値以外の文字を取り除く（例：通貨記号や単位など）
    filtered_data['家賃'] = filtered_data['家賃'].replace('[^0-9.]', '', regex=True)

    # 文字列を浮動小数点数に変換する
    filtered_data['家賃'] = filtered_data['家賃'].astype(float)

    # 経費に基づいてフィルタリング
    filtered_data = filtered_data[(filtered_data['家賃'] >= expense[0]) & (filtered_data['家賃'] <= expense[1])]  

    # 間取りに基づいてフィルタリング
    if madori:
        filtered_data = filtered_data[filtered_data['間取り'].isin(madori)] 

    # フィルタリングされたデータを表示
    #st.dataframe(filtered_data)

    count_all = len(filtered_data)
    #st.write(f'検索結果数: {count_all}')
    st.write(f'{count_all}件見つかりました')


    # ------------------------地図作成------------------------

    # マップオブジェクトを作成する関数

    # 住所のカラムにジオコーディングを適用
    filtered_data['Coordinates'] = filtered_data['アドレス'].apply(get_coordinates)

        # フィルタリングされた物件の座標の平均を計算
    valid_coords = filtered_data['Coordinates'].dropna()
    if len(valid_coords) > 0:
        average_lat = valid_coords.apply(lambda x: x[0]).mean()
        average_lon = valid_coords.apply(lambda x: x[1]).mean()
        map_center = [average_lat, average_lon]
    else:
        # 有効な座標がない場合、デフォルトの中心座標を使用
        map_center = [35.6895, 139.6917]

    # 'Coordinates'列から緯度と経度を分けて、新しい列を作成
    filtered_data['lat'] = filtered_data['Coordinates'].apply(lambda coord: coord[0] if coord else None)
    filtered_data['lon'] = filtered_data['Coordinates'].apply(lambda coord: coord[1] if coord else None)



    def create_map(filtered_data):
        # 特定の緯度経度でマップオブジェクトを初期化
        m = folium.Map(location=map_center, zoom_start=14)
        
        # フィルタリングされたデータに基づいてマーカーを追加
        for index, row in filtered_data.iterrows():
            # マーカーをクリックした時に表示されるポップアップ
            #popup = folium.Popup(row['名称'], max_width=300)
            popup = folium.Popup(f'<a href="{row["リンク"]}" target="_blank">{row["名称"]}</a>', max_width=300)
            
            # マーカーを地図に追加
            folium.Marker(
                location=[row['lat'], row['lon']],  # ここで緯度経度情報をDataFrameから取得
                popup=popup
            ).add_to(m)
        
        return m

    # フィルタリングされたデータに基づいてマップを生成
    m = create_map(filtered_data)
        
    # Streamlitアプリにマップを表示
    folium_static(m)

    # ------------------------表作成------------------------

    # 表示したい列のリスト
    columns_to_display = ['名称', '築年数', '構造','間取り', '家賃','敷金','礼金', '階数','リンク']

    # 必要な列のみを含む新しいDataFrameを作成
    dataframe_to_display = filtered_data[columns_to_display]

    # DataFrameに変換
    #dataframe = pd.DataFrame(filtered_data)

    # DataFrame内の各行に対してHTMLリンクを含む表を作成
    def generate_table(dataframe):
        header_html = "<table><tr><th>番号</th>"  # 先頭列に番号のヘッダーを追加
        # ヘッダーの追加
        for col in dataframe.columns:
            if col != 'リンク':  # リンク列を除外
                header_html += f"<th>{col}</th>"
        header_html += "</tr>"

        # 各行のデータに対してHTMLタグを追加
        rows_html = ""
        counter = 1
        for index, row in dataframe.iterrows():
            rows_html += f"<tr><td>{counter}</td>"  
            counter += 1
            for col in dataframe.columns:
                # 名称列にリンクを挿入
                if col == '名称':
                    rows_html += f"<td><a href='{row['リンク']}' target='_blank'>{row[col]}</a></td>"
                elif col != 'リンク': 
                    rows_html += f"<td>{row[col]}</td>"
            rows_html += "</tr>"

        # 終了タグ
        footer_html = "</table>"

        # ヘッダー、行、フッターを合わせて全体のHTMLを作成
        full_html = header_html + rows_html + footer_html
        return full_html

    # HTML形式の表を生成
    table_html = generate_table(dataframe_to_display)

    # StreamlitアプリにHTMLテーブルを表示
    st.markdown(table_html, unsafe_allow_html=True)
