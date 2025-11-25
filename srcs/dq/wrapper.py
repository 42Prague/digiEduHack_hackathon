import pandas as pd

from srcs.dq.embedding import Embedding
from srcs.dq.storage import Storage


def process_df(df):
    embedder = Embedding()
    storage = Storage(name="tmp-tmp-name", embedding_size=384)

    rename_map = {}

    for col in df.columns:
        embedded_col = embedder.embed_text(col)[0]
        res_flag, new_name = storage.smart_load(embedded_col, col, df[col].tolist())
        
        if not res_flag and col != new_name:
            rename_map[col] = new_name
    
    if rename_map:
        df = df.rename(columns=rename_map)

    return df

# storage = Storage(name="tmp-name", embedding_size=384)

# datf = pd.read_csv("/Users/nazarskiy/Workspace/souteze/digiEduHack_hackathon/data/synthetic_samples/modified_student_ranking.csv")
# print("DATF:")
# print(datf)
# print("List data")
# pprint.pprint(storage.list_data())

# new_datf = process_df(datf)
# print("NEW DATF:")
# print(new_datf)
# print("List data")
# pprint.pprint(storage.list_data())

# datf1 = pd.read_json("/Users/nazarskiy/Workspace/souteze/digiEduHack_hackathon/data/synthetic_samples/modified_grades_random.json")
# print("DATF1:")
# print(datf1)
# print("List data")
# pprint.pprint(storage.list_data())

# new_datf1 = process_df(datf1)
# print("NEW DATF1:")
# print(new_datf1)
# print("List data")
# pprint.pprint(storage.list_data())
