import json
from pathlib import Path
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import json
import numpy as np

def summary_separator():
    # --- Load JSON summaries ---
    input_dir = Path("json_outputs")
    summaries = []
    files = []

    for f in input_dir.glob("*.json"):
        data = json.load(open(f, encoding="utf-8"))
        summaries.append(data.get("summary", ""))
        files.append(f.name)

    # --- Vectorize summaries ---
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(summaries)

    # --- DBSCAN clustering ---
    db = DBSCAN(eps=0.7, min_samples=1, metric="cosine")
    labels = db.fit_predict(X)

    # --- Print cluster assignments ---
    cluster_dict = {}
    for file_name, label in zip(files, labels):
        cluster_dict.setdefault(label, []).append(file_name)

    for cluster_label, file_list in cluster_dict.items():
        if cluster_label == -1:
            print(f"\nNoise points ({len(file_list)} summaries):")
        else:
            print(f"\nCluster {cluster_label} contains {len(file_list)} summaries:")
        for name in file_list:
            print("  ", name)

    # --- PCA for visualization ---
    pca = PCA(n_components=2)
    X_reduced = pca.fit_transform(X.toarray())

    plt.figure(figsize=(10, 7))
    unique_labels = sorted(set(labels))
    colors = plt.cm.get_cmap('tab10', len(unique_labels))

    for idx, cluster_label in enumerate(unique_labels):
        cluster_idx = np.where(labels == cluster_label)[0]
        plt.scatter(X_reduced[cluster_idx, 0], X_reduced[cluster_idx, 1],
                    color=colors(idx), label=f"Cluster {cluster_label}", s=80, alpha=0.7)
        for j in cluster_idx:
            plt.annotate(files[j], (X_reduced[j, 0], X_reduced[j, 1]), fontsize=8, alpha=0.6)

    plt.title("DBSCAN Clusters of JSON Summaries (eps=0.7)")
    plt.xlabel("PCA 1")
    plt.ylabel("PCA 2")
    plt.legend()
    plt.show()

def main():
    summary_separator()

if __name__ == "__main__":
    main()
