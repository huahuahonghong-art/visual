import pandas as pd
import json

# ==================== 1. 读取数据 ====================
df = pd.read_csv('spotify_tracks.csv')

# ==================== 2. 筛选必要字段 ====================
features = ['danceability', 'energy', 'valence', 'acousticness',
            'instrumentalness', 'speechiness', 'liveness', 'tempo']
required_cols = ['track_genre', 'track_name', 'artists'] + features
available_cols = [col for col in required_cols if col in df.columns]

if 'track_genre' not in df.columns:
    # 尝试备选列名
    for col in df.columns:
        if 'genre' in col.lower():
            df.rename(columns={col: 'track_genre'}, inplace=True)
            break

df = df[available_cols]

# ==================== 3. 剔除缺失值与异常值 ====================
df = df.dropna(subset=['track_genre'] + features)
for col in features:
    df = df[df[col] >= 0]
    if col != 'tempo':
        df = df[df[col] <= 1]

# ==================== 4. 按流派分组，取所有流派（不限制数量） ====================
genre_counts = df['track_genre'].value_counts()
all_genres = genre_counts.index.tolist()          # 所有流派名称
df_top = df[df['track_genre'].isin(all_genres)]   # 或者直接 df_top = df

print(f"共有 {len(all_genres)} 个流派，样本量分布（前15个）：")
for genre in all_genres[:15]:
    count = genre_counts[genre]
    print(f"  {genre}: {count}")
if len(all_genres) > 15:
    print(f"  ... 等共 {len(all_genres)} 个流派")

# ==================== 5. 计算每个流派各特征的均值 ====================
genre_means = df_top.groupby('track_genre')[features].mean()

# ==================== 6. 最小-最大标准化（Min-Max Normalization） ====================
def min_max_normalize(series):
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return series * 0
    return (series - min_val) / (max_val - min_val)

genre_norm = genre_means.copy()
for col in features:
    genre_norm[col] = min_max_normalize(genre_norm[col])

# ==================== 7. 提取每个流派的典型歌曲示例 ====================
def get_example_songs(genre, n=3):
    genre_df = df_top[df_top['track_genre'] == genre]
    # 用popularity列排序取最热门的歌曲
    if 'popularity' in genre_df.columns:
        genre_df = genre_df.sort_values('popularity', ascending=False)
    elif 'track_popularity' in genre_df.columns:
        genre_df = genre_df.sort_values('track_popularity', ascending=False)
    songs = genre_df[['track_name', 'artists']].head(n)
    return [f"{row['track_name']} — {row['artists']}" for _, row in songs.iterrows()]

# ==================== 8. 生成JSON数据 ====================
genres_data = []
for genre in all_genres:      # 遍历所有流派
    genre_data = {
        'name': genre,
        'sample_count': int(genre_counts[genre]),
        'features': {
            feature: float(genre_means.loc[genre, feature]) for feature in features
        },
        'normalized_features': {
            feature: float(genre_norm.loc[genre, feature]) for feature in features
        },
        'example_songs': get_example_songs(genre)
    }
    genres_data.append(genre_data)

# 保存为JavaScript文件
output_js = """// 自动生成的数据文件（包含所有流派）
const SPOTIFY_DATA = """ + json.dumps(genres_data, indent=2, ensure_ascii=False) + """;

const FEATURES = """ + json.dumps(features, indent=2) + """;

const FEATURE_DESCRIPTIONS = {
    'danceability': '舞蹈性 - 适合跳舞的程度',
    'energy': '能量 - 强度与活跃度',
    'valence': '愉悦度 - 音乐的积极性与欢乐感',
    'acousticness': '声学度 - 原声乐器占比',
    'instrumentalness': '器乐度 - 无人声程度',
    'speechiness': '言语度 - 口语或说唱占比',
    'liveness': '现场感 - 现场录音的可能性',
    'tempo': '节奏 - 每分钟节拍数'
};
"""

with open('../web/genre_analysis_data.js', 'w', encoding='utf-8') as f:
    f.write(output_js)

print(f"\n✅ 数据处理完成！已生成 genre_analysis_data.js")
print(f"✅ 共处理 {len(genres_data)} 个流派，{len(features)} 个音频特征")