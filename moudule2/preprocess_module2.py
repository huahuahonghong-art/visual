#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块二：歌曲流行度影响因素分析 - 数据预处理脚本

输入：Spotify Tracks Dataset CSV，例如 dataset.csv
输出：前端 ECharts 可直接读取的 JSON：
  src/data/module2_popularity_analysis.json

运行示例：
  python scripts/preprocess_module2.py --input dataset.csv --output src/data/module2_popularity_analysis.json
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


CORE_FEATURES = [
    "danceability",
    "energy",
    "valence",
    "acousticness",
    "instrumentalness",
    "liveness",
    "speechiness",
]

OPTIONAL_NUMERIC_FEATURES = [
    "tempo",
    "duration_ms",
    "loudness",
]

KEY_COLUMNS = [
    "track_id",
    "artists",
    "track_name",
    "popularity",
    "track_genre",
    *CORE_FEATURES,
]


def to_builtin(obj):
    """把 numpy / pandas 类型转换成 JSON 可序列化的 Python 原生类型。"""
    if isinstance(obj, dict):
        return {str(k): to_builtin(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_builtin(v) for v in obj]
    if isinstance(obj, tuple):
        return [to_builtin(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        if np.isnan(obj):
            return None
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if pd.isna(obj):
        return None
    return obj


def popularity_level(value):
    """按项目建议书口径划分低/中/高流行度。"""
    if value <= 30:
        return "low"
    if value <= 60:
        return "medium"
    return "high"


def safe_round(value, ndigits=4):
    if value is None or pd.isna(value):
        return None
    return round(float(value), ndigits)


def load_and_clean(input_path: Path):
    raw_df = pd.read_csv(input_path)
    raw_count = len(raw_df)

    df = raw_df.copy()

    # 删除无意义索引列
    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=["Unnamed: 0"])

    # 检查必要字段
    missing_cols = [col for col in KEY_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"数据缺少模块二必要字段：{missing_cols}")

    # 文本字段去空格
    text_cols = ["track_id", "artists", "album_name", "track_name", "track_genre"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()

    # 数值字段转换
    numeric_cols = ["popularity", *CORE_FEATURES, *OPTIONAL_NUMERIC_FEATURES]
    numeric_cols = [col for col in numeric_cols if col in df.columns]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 删除关键字段缺失
    before_dropna = len(df)
    df = df.dropna(subset=KEY_COLUMNS)
    removed_missing = before_dropna - len(df)

    # 合法范围检查
    valid_mask = df["popularity"].between(0, 100)
    for col in CORE_FEATURES:
        valid_mask &= df[col].between(0, 1)

    # tempo 和 duration_ms 如果存在，只保留正数
    if "tempo" in df.columns:
        valid_mask &= df["tempo"].isna() | (df["tempo"] > 0)
    if "duration_ms" in df.columns:
        valid_mask &= df["duration_ms"].isna() | (df["duration_ms"] > 0)

    before_range = len(df)
    df = df[valid_mask].copy()
    removed_invalid_range = before_range - len(df)

    # 新增分析字段
    df["popularity_level"] = df["popularity"].apply(popularity_level)
    df["is_popular"] = df["popularity"] >= 70

    # genre_view：保留歌曲-流派关系，用于流派统计和筛选
    genre_view = df.copy()

    # song_view：按 track_id 去重，用于整体相关性/画像/箱线图，避免重复歌曲影响统计
    # 同一首歌如果对应多个流派，保留所有流派列表，同时保留第一个流派作为 primary_genre
    agg_map = {
        "artists": "first",
        "album_name": "first" if "album_name" in df.columns else "first",
        "track_name": "first",
        "popularity": "first",
        "duration_ms": "first" if "duration_ms" in df.columns else "first",
        "explicit": "first" if "explicit" in df.columns else "first",
        "danceability": "first",
        "energy": "first",
        "key": "first" if "key" in df.columns else "first",
        "loudness": "first" if "loudness" in df.columns else "first",
        "mode": "first" if "mode" in df.columns else "first",
        "speechiness": "first",
        "acousticness": "first",
        "instrumentalness": "first",
        "liveness": "first",
        "valence": "first",
        "tempo": "first" if "tempo" in df.columns else "first",
        "time_signature": "first" if "time_signature" in df.columns else "first",
        "popularity_level": "first",
        "is_popular": "first",
    }
    agg_map = {k: v for k, v in agg_map.items() if k in df.columns}

    song_view = (
        df.sort_values(["track_id", "popularity"], ascending=[True, False])
        .groupby("track_id", as_index=False)
        .agg(agg_map)
    )

    genre_lists = (
        df.groupby("track_id")["track_genre"]
        .apply(lambda x: sorted(set(x.dropna().astype(str))))
        .reset_index(name="genres")
    )
    song_view = song_view.merge(genre_lists, on="track_id", how="left")
    song_view["primary_genre"] = song_view["genres"].apply(lambda x: x[0] if isinstance(x, list) and x else None)

    clean_report = {
        "raw_count": raw_count,
        "genre_view_count": len(genre_view),
        "song_view_count": len(song_view),
        "removed_missing": removed_missing,
        "removed_invalid_range": removed_invalid_range,
        "removed_total": raw_count - len(genre_view),
        "duplicate_track_id_count": int(genre_view["track_id"].duplicated().sum()),
    }

    return raw_df, genre_view, song_view, clean_report


def build_summary(song_view: pd.DataFrame, genre_view: pd.DataFrame):
    top_row = song_view.sort_values("popularity", ascending=False).iloc[0]
    popular_count = int((song_view["popularity"] >= 70).sum())
    total_tracks = int(len(song_view))

    return {
        "total_tracks": total_tracks,
        "genre_relation_rows": int(len(genre_view)),
        "avg_popularity": safe_round(song_view["popularity"].mean(), 2),
        "median_popularity": safe_round(song_view["popularity"].median(), 2),
        "max_popularity": safe_round(song_view["popularity"].max(), 2),
        "popular_track_count": popular_count,
        "popular_track_ratio": safe_round(popular_count / total_tracks if total_tracks else 0, 4),
        "genre_count": int(genre_view["track_genre"].nunique()),
        "top_track": {
            "track_id": top_row.get("track_id"),
            "track_name": top_row.get("track_name"),
            "artists": top_row.get("artists"),
            "genre": top_row.get("primary_genre"),
            "genres": top_row.get("genres", []),
            "popularity": safe_round(top_row.get("popularity"), 2),
        },
    }


def build_popularity_distribution(song_view: pd.DataFrame):
    bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    labels = ["0-10", "11-20", "21-30", "31-40", "41-50", "51-60", "61-70", "71-80", "81-90", "91-100"]

    # popularity 是整数，使用 include_lowest 保证 0 被统计进去
    cut_result = pd.cut(
        song_view["popularity"],
        bins=bins,
        labels=labels,
        include_lowest=True,
        right=True,
    )

    counts = cut_result.value_counts().reindex(labels, fill_value=0)

    return [
        {
            "range": label,
            "count": int(count),
        }
        for label, count in counts.items()
    ]


def build_feature_correlations(song_view: pd.DataFrame):
    features = [f for f in [*CORE_FEATURES, "tempo", "duration_ms", "loudness"] if f in song_view.columns]
    records = []

    for feature in features:
        valid = song_view[["popularity", feature]].dropna()
        if len(valid) < 2 or valid[feature].std() == 0:
            corr = None
        else:
            corr = valid["popularity"].corr(valid[feature], method="pearson")

        if corr is None or pd.isna(corr) or abs(corr) < 1e-8:
            direction = "none"
        elif corr > 0:
            direction = "positive"
        else:
            direction = "negative"

        records.append(
            {
                "feature": feature,
                "correlation": safe_round(corr, 6),
                "abs_correlation": safe_round(abs(corr), 6) if corr is not None and not pd.isna(corr) else None,
                "direction": direction,
            }
        )

    records.sort(key=lambda x: x["abs_correlation"] if x["abs_correlation"] is not None else -1, reverse=True)
    return records


def build_level_feature_stats(song_view: pd.DataFrame):
    result = {}
    levels = ["low", "medium", "high"]

    for level in levels:
        part = song_view[song_view["popularity_level"] == level]
        result[level] = {}

        for feature in CORE_FEATURES:
            s = part[feature].dropna()
            if len(s) == 0:
                result[level][feature] = None
                continue

            result[level][feature] = {
                "min": safe_round(s.min(), 4),
                "q1": safe_round(s.quantile(0.25), 4),
                "median": safe_round(s.median(), 4),
                "q3": safe_round(s.quantile(0.75), 4),
                "max": safe_round(s.max(), 4),
                "mean": safe_round(s.mean(), 4),
                "count": int(s.count()),
                # ECharts boxplot 常用顺序：[min, Q1, median, Q3, max]
                "boxplot": [
                    safe_round(s.min(), 4),
                    safe_round(s.quantile(0.25), 4),
                    safe_round(s.median(), 4),
                    safe_round(s.quantile(0.75), 4),
                    safe_round(s.max(), 4),
                ],
            }

    return result


def mean_profile(df: pd.DataFrame):
    return {feature: safe_round(df[feature].mean(), 4) for feature in CORE_FEATURES}


def build_popular_profile(song_view: pd.DataFrame):
    return {
        "features": CORE_FEATURES,
        "all_tracks_profile": mean_profile(song_view),
        "popular_tracks_profile": mean_profile(song_view[song_view["popularity"] >= 70]),
        "low_tracks_profile": mean_profile(song_view[song_view["popularity"] <= 30]),
    }


def build_scatter_sample(song_view: pd.DataFrame, max_total=6000, random_state=42):
    # 分层抽样：优先保留高流行度，同时兼顾中低流行度
    high = song_view[song_view["popularity_level"] == "high"]
    medium = song_view[song_view["popularity_level"] == "medium"]
    low = song_view[song_view["popularity_level"] == "low"]

    high_n = min(len(high), int(max_total * 0.40))
    medium_n = min(len(medium), int(max_total * 0.35))
    low_n = min(len(low), max_total - high_n - medium_n)

    parts = []
    if high_n > 0:
        parts.append(high.sample(n=high_n, random_state=random_state))
    if medium_n > 0:
        parts.append(medium.sample(n=medium_n, random_state=random_state))
    if low_n > 0:
        parts.append(low.sample(n=low_n, random_state=random_state))

    sample_df = pd.concat(parts, ignore_index=True) if parts else song_view.head(0)

    cols = [
        "track_id",
        "track_name",
        "artists",
        "primary_genre",
        "genres",
        "popularity",
        "popularity_level",
        *CORE_FEATURES,
    ]

    if "tempo" in sample_df.columns:
        cols.append("tempo")
    if "duration_ms" in sample_df.columns:
        cols.append("duration_ms")

    records = sample_df[cols].rename(columns={"primary_genre": "genre"}).to_dict(orient="records")
    return records


def build_genre_popularity_stats(genre_view: pd.DataFrame, min_count=50):
    group = genre_view.groupby("track_genre")

    records = []
    for genre, part in group:
        count = len(part)
        if count < min_count:
            continue

        item = {
            "genre": genre,
            "track_count": int(count),
            "avg_popularity": safe_round(part["popularity"].mean(), 4),
            "median_popularity": safe_round(part["popularity"].median(), 4),
            "popular_track_ratio": safe_round((part["popularity"] >= 70).mean(), 4),
        }

        for feature in CORE_FEATURES:
            item[f"avg_{feature}"] = safe_round(part[feature].mean(), 4)

        records.append(item)

    records.sort(key=lambda x: x["avg_popularity"], reverse=True)
    return records


def build_output(input_path: Path):
    raw_df, genre_view, song_view, clean_report = load_and_clean(input_path)

    output = {
        "summary": build_summary(song_view, genre_view),
        "popularity_distribution": build_popularity_distribution(song_view),
        "feature_correlations": build_feature_correlations(song_view),
        "level_feature_stats": build_level_feature_stats(song_view),
        "popular_profile": build_popular_profile(song_view),
        "scatter_sample": build_scatter_sample(song_view),
        "genre_popularity_stats": build_genre_popularity_stats(genre_view),
        "metadata": {
            "source_file": str(input_path),
            "raw_count": clean_report["raw_count"],
            "cleaned_genre_view_count": clean_report["genre_view_count"],
            "cleaned_song_view_count": clean_report["song_view_count"],
            "removed_count": clean_report["removed_total"],
            "removed_missing": clean_report["removed_missing"],
            "removed_invalid_range": clean_report["removed_invalid_range"],
            "duplicate_track_id_count": clean_report["duplicate_track_id_count"],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "features_used": CORE_FEATURES,
            "popularity_level_rule": {
                "low": "0-30",
                "medium": "31-60",
                "high": "61-100",
            },
            "popular_rule": "popularity >= 70",
            "note": "song_view 按 track_id 去重，用于整体影响因素分析；genre_view 保留歌曲-流派关系，用于流派统计。",
        },
    }

    return output


def main():
    parser = argparse.ArgumentParser(description="Preprocess Spotify dataset for module 2 popularity analysis.")
    parser.add_argument("--input", type=str, default="dataset.csv", help="输入 CSV 文件路径，默认 dataset.csv")
    parser.add_argument(
        "--output",
        type=str,
        default="src/data/module2_popularity_analysis.json",
        help="输出 JSON 文件路径，默认 src/data/module2_popularity_analysis.json",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"找不到输入文件：{input_path}")

    output = build_output(input_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(to_builtin(output), f, ensure_ascii=False, indent=2)

    print("模块二数据预处理完成")
    print(f"输入文件：{input_path}")
    print(f"输出文件：{output_path}")
    print(f"原始行数：{output['metadata']['raw_count']}")
    print(f"清洗后歌曲-流派行数：{output['metadata']['cleaned_genre_view_count']}")
    print(f"按 track_id 去重后歌曲数：{output['metadata']['cleaned_song_view_count']}")
    print(f"重复 track_id 行数：{output['metadata']['duplicate_track_id_count']}")


if __name__ == "__main__":
    main()
