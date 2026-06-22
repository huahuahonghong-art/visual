import pandas as pd
import json
import os

# 读取数据
df = pd.read_csv('dataset.csv')

print("=== 开始处理歌手数据（仅保留歌曲数 > 20 的歌手）===\n")

def prepare_singer_data(df, min_songs=20, top_n_songs=5):
    """
    准备歌手数据
    
    参数:
    - df: 原始数据 DataFrame
    - min_songs: 至少包含多少首歌的歌手才保留（默认 20）
    - top_n_songs: 每个歌手选取的代表歌曲数量
    """
    
    # 根据实际列名进行映射
    df_clean = df[['artists', 'track_name', 'valence', 'energy', 'popularity', 'track_genre']].copy()
    
    # 重命名列，方便处理
    df_clean = df_clean.rename(columns={
        'artists': 'artist_name',
        'track_name': 'track_name',
        'valence': 'valence',
        'energy': 'energy',
        'popularity': 'popularity',
        'track_genre': 'genre'
    })
    
    # 删除空值
    initial_count = len(df_clean)
    df_clean = df_clean.dropna()
    print(f"删除空值后剩余: {len(df_clean)} 条记录 (删除 {initial_count - len(df_clean)} 条)")
    
    # 按歌手分组处理
    singer_data = {}
    skipped_artists = []
    
    for artist, group in df_clean.groupby('artist_name'):
        song_count = len(group)
        
        # 只保留歌曲数量 > min_songs 的歌手
        if song_count <= min_songs:
            skipped_artists.append(f"{artist} ({song_count}首歌)")
            continue
        
        # 获取该歌手的所有歌曲
        songs = []
        for _, row in group.iterrows():
            songs.append({
                "name": str(row['track_name']),
                "valence": float(row['valence']),
                "energy": float(row['energy']),
                "popularity": int(row['popularity']) if pd.notna(row['popularity']) else 0,
                "genre": str(row['genre']) if pd.notna(row['genre']) else "unknown"
            })
        
        # 按流行度排序，选取代表歌曲（取前 top_n_songs 首）
        songs_sorted = sorted(songs, key=lambda x: x['popularity'], reverse=True)
        representative_songs = songs_sorted[:top_n_songs]
        
        # 存储
        singer_data[artist] = {
            "representative_songs": representative_songs,
            "all_songs": songs,
            "song_count": song_count,
            "avg_popularity": round(sum(s['popularity'] for s in songs) / song_count, 2),
            "avg_valence": round(sum(s['valence'] for s in songs) / song_count, 3),
            "avg_energy": round(sum(s['energy'] for s in songs) / song_count, 3)
        }
        
        print(f"✓ {artist}: {song_count}首歌, 平均流行度 {singer_data[artist]['avg_popularity']}")
    
    print(f"\n=== 统计 ===")
    print(f"总计处理歌手数: {len(singer_data)}")
    print(f"跳过的歌手数 (歌曲数 ≤ {min_songs}): {len(skipped_artists)}")
    
    # 显示前10位歌曲数最多的歌手
    if len(singer_data) > 0:
        print(f"\n=== 歌曲数最多的前10位歌手 ===")
        sorted_artists = sorted(singer_data.items(), key=lambda x: x[1]['song_count'], reverse=True)
        for i, (artist, info) in enumerate(sorted_artists[:10]):
            print(f"{i+1}. {artist} - {info['song_count']}首歌")
    
    return singer_data

# 执行处理（min_songs=20 表示只保留歌曲数 > 20 的歌手）
singer_data = prepare_singer_data(df, min_songs=20, top_n_songs=5)

# 保存为 JSON 文件
output_file = 'singer_data.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(singer_data, f, ensure_ascii=False, indent=2)

print(f"\n✅ 数据已保存到 {output_file}")
print(f"文件大小: {os.path.getsize(output_file) / 1024:.2f} KB")

# 生成歌手列表
artist_list = list(singer_data.keys())
with open('artist_list.json', 'w', encoding='utf-8') as f:
    json.dump(artist_list, f, ensure_ascii=False, indent=2)
print(f"✅ 歌手列表已保存到 artist_list.json (共 {len(artist_list)} 位歌手)")