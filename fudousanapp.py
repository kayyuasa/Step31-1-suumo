#ライブラリをimport
import streamlit as st
from PIL import Image #イメージを表示
import folium
from streamlit_folium import folium_static
import pandas as pd
import requests
from bs4 import BeautifulSoup


#CSVからデータを取ってくる

# CSVファイルのパス
csv_file_path = 'unique_output.csv'

# CSVファイルを読み込む
unique_data = pd.read_csv(csv_file_path)  


#<Streamlitでフロント画面を作成>------ここから

st.title("都市部不動産一発検索アプリ") # タイトル

image = Image.open('image1.png') #画像挿入
st.image(image, caption=None)

st.markdown("すぐに検索できます")

st.sidebar.header("検索条件を選び「検索」をクリック")

area = st.sidebar.radio(
    "エリアを選択",
    options=['港区', '目黒区', '品川区']
)

expense = st.sidebar.slider(
    '',
    min_value=0,  # Minimum value
    max_value=50, # Maximum value
    value=(35, 45),  # Default range
    step=1  # Step size
)

madori = st.sidebar.multiselect(
  '間取り',
  ['1LDK', '2LDK', '3LDK', '4LDK', '1K', '2K', '3K', '4K'],
  ['1LDK', '2LDK']  # オプションの中からデフォルト選択を指定
)

# ボタンを押した時に検索
if st.sidebar.button("検索") :

    # フィルタリングされたデータを表示
    filtered_data = unique_data.copy()

    # エリアに基づいてフィルタリング
    if area:
        filtered_data = filtered_data[filtered_data['アドレス'].str.contains(area)]  # 'area_column'を該当するエリアの列名に置き換えてください

    # 経費に基づいてフィルタリング
    filtered_data = filtered_data[(filtered_data['家賃'] >= expense[0]) & (filtered_data['家賃'] <= expense[1])]  # 'expense_column'を該当する経費の列名に置き換えてください

    # 間取りに基づいてフィルタリング
    if madori:
        filtered_data = filtered_data[filtered_data['間取り'].isin(madori)]  # 'layout_column'を該当する間取りの列名に置き換えてください

    # フィルタリングされたデータを表示
    st.dataframe(filtered_data)



    # ------------------------地図作成------------------------

    # マップオブジェクトを作成する関数

    def create_map(filtered_data):
        # 特定の緯度経度でマップオブジェクトを初期化（ここでは東京駅周辺をデフォルトとしています）
        m = folium.Map(location=[35.681236, 139.767125], zoom_start=14)
        
        # フィルタリングされたデータに基づいてマーカーを追加
        for index, row in filtered_data.iterrows():
            # マーカーをクリックした時に表示されるポップアップ
            popup = folium.Popup(row['名称'], max_width=300)
            
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

    # DataFrameに変換
    dataframe = pd.DataFrame(filtered_data)

    # DataFrame内の各行に対してHTMLリンクを含む表を作成
    def generate_table(dataframe):
        header_html = "<table><tr>"  # 開始タグ
        # ヘッダーの追加
        for col in dataframe.columns:
            header_html += f"<th>{col}</th>"
        header_html += "</tr>"

        # 各行のデータに対してHTMLタグを追加
        rows_html = ""
        for index, row in dataframe.iterrows():
            rows_html += "<tr>"
            for col in dataframe.columns:
                # 名称列にリンクを挿入（あなたのDataFrameにurl列があることを想定しています）
                if col == '名称':
                    rows_html += f"<td><a href='{row['url']}' target='_blank'>{row[col]}</a></td>"
                else:
                    rows_html += f"<td>{row[col]}</td>"
            rows_html += "</tr>"

        # 終了タグ
        footer_html = "</table>"

        # ヘッダー、行、フッターを合わせて全体のHTMLを作成
        full_html = header_html + rows_html + footer_html
        return full_html

    # HTML形式の表を生成
    table_html = generate_table(filtered_data)

    # StreamlitアプリにHTMLテーブルを表示
    st.markdown(table_html, unsafe_allow_html=True)
