import pandas as pd
import json
import numpy as np

# ========== 配置 ==========
file_path = "F:/vis/music_project/dataset.csv"
output_dir = "F:/vis/music_project/"

# ========== 1. 读取数据 ==========
print("正在读取数据...")
df = pd.read_csv(file_path)
print(f"总数据量: {len(df)} 条")

# ========== 2. 提取需要的列 ==========
features = ['valence', 'energy', 'danceability', 'track_genre']
df_filtered = df[features].copy()
print(f"提取特征: {features}")

# ========== 3. 计算总体相关系数矩阵 ==========
print("\n===== 计算总体相关系数 =====")
corr_matrix = df_filtered[['valence', 'energy', 'danceability']].corr()

# 保存总体热力图数据
heatmap_overall = {
    "xAxis": ["valence", "energy", "danceability"],
    "yAxis": ["valence", "energy", "danceability"],
    "data": []
}

for i, row_name in enumerate(['valence', 'energy', 'danceability']):
    for j, col_name in enumerate(['valence', 'energy', 'danceability']):
        heatmap_overall["data"].append({
            "x": col_name,
            "y": row_name,
            "value": round(corr_matrix.iloc[i, j], 3)
        })

# 保存总体热力图 JSON
with open(f"{output_dir}heatmap_overall.json", "w", encoding="utf-8") as f:
    json.dump(heatmap_overall, f, indent=2)
print(" 已保存: heatmap_overall.json")

# ========== 4. 计算每个流派的热力图数据 ==========
print("\n===== 计算各流派相关系数 =====")
genres = df_filtered['track_genre'].unique()
genre_heatmaps = {}

for genre in genres:
    genre_df = df_filtered[df_filtered['track_genre'] == genre]
    if len(genre_df) >= 10:  # 至少需要10个样本
        genre_corr = genre_df[['valence', 'energy', 'danceability']].corr()
        genre_heatmaps[genre] = {
            "valence_energy": round(genre_corr.loc['valence', 'energy'], 3),
            "valence_danceability": round(genre_corr.loc['valence', 'danceability'], 3),
            "energy_danceability": round(genre_corr.loc['energy', 'danceability'], 3)
        }

print(f" 计算了 {len(genre_heatmaps)} 个流派的热力图数据")

# 保存流派热力图数据
with open(f"{output_dir}heatmap_genres.json", "w", encoding="utf-8") as f:
    json.dump(genre_heatmaps, f, indent=2)
print(" 已保存: heatmap_genres.json")

# ========== 5. 生成 3D 散点图数据（每个流派采样 N 首） ==========
print("\n===== 生成 3D 散点图数据 =====")
samples_per_genre = 30  # 每个流派采样 30 首（可调整：20-50）
sampled_data = []

for genre in genres:
    genre_df = df_filtered[df_filtered['track_genre'] == genre]
    if len(genre_df) > samples_per_genre:
        genre_df = genre_df.sample(n=samples_per_genre, random_state=42)
    for _, row in genre_df.iterrows():
        sampled_data.append([
            float(row['valence']),
            float(row['energy']),
            float(row['danceability']),
            row['track_genre']
        ])

print(f" 生成 {len(sampled_data)} 个数据点")

with open(f"{output_dir}scatter3d_data.json", "w", encoding="utf-8") as f:
    json.dump(sampled_data, f, indent=2)
print(" 已保存: scatter3d_data.json")

# ========== 6. 生成流派列表（用于前端下拉框） ==========
genre_list = sorted([g for g in genres if g in genre_heatmaps])
with open(f"{output_dir}genres_list.json", "w", encoding="utf-8") as f:
    json.dump(genre_list, f, indent=2)
print(" 已保存: genres_list.json")

# ========== 7. 生成流派统计信息 ==========
genre_counts = df_filtered['track_genre'].value_counts().to_dict()
genre_stats = {g: {"count": genre_counts.get(g, 0)} for g in genre_list}
for g in genre_stats:
    if g in genre_heatmaps:
        genre_stats[g].update(genre_heatmaps[g])

with open(f"{output_dir}genre_stats.json", "w", encoding="utf-8") as f:
    json.dump(genre_stats, f, indent=2)
print(" 已保存: genre_stats.json")

# ========== 8. 打印总结 ==========
print("\n" + "="*50)
print(" 数据生成完成！")
print("="*50)
print(f"总数据量: {len(df)} 条")
print(f"流派数量: {len(genres)} 种")
print(f"有效流派（样本≥10）: {len(genre_heatmaps)} 种")
print(f"3D图数据点: {len(sampled_data)} 个")
print("\n生成的文件:")
print("  - heatmap_overall.json    (总体热力图)")
print("  - heatmap_genres.json     (各流派热力图数据)")
print("  - scatter3d_data.json     (3D散点图数据)")
print("  - genres_list.json        (流派列表)")
print("  - genre_stats.json        (流派统计)")
print("="*50)
