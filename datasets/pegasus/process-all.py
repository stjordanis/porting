#!/usr/bin/env python
# coding: utf-8

# this script prepares data for pegasus evals

# 0. install the prerequisites (see README.md)
#
# note: since many of these datasets require manual building before they can be used, you will have to follow the instructions in each `process.txt` file under the corresponding to the dataset sub-dir

# set TEST_ONLY=False if you want to build all 3 splits and not just `test` in process.py and process-all.py scripts

# 1. build most of them
# ./process-all.py

# 2. build xsum
# cd xsum
# ./process.py
# mv data ../data/xsum
# cd -

# 3. tar them all and upload to s3
# cd data
# find . -type d -maxdepth 1 -mindepth 1 -exec tar cvzf {}.tar.gz {}  \;
# cd -
# mkdir -p pegasus_data
# cp data/*tgz pegasus_data
# export ds=s3://datasets.huggingface.co
# aws s3 sync pegasus_data $ds/summarization/pegasus_data

from pegasus.data import all_datasets
from pathlib import Path
import re

dss = dict(
    aeslc="tfds:aeslc",
    # big_patent="tfds:big_patent/all", # can't build tfds:big_patent at the moment, see https://github.com/google-research/pegasus/issues/114
    billsum="tfds_transformed:billsum",
    cnn_dailymail="tfds:cnn_dailymail/plain_text",
    gigaword="tfds:gigaword",
    multi_news="tfds:multi_news",
    newsroom="tfds:newsroom",
    reddit_tifu="tfds_transformed:reddit_tifu/long",
    arxiv="tfds:scientific_papers/arxiv",
    pubmed="tfds:scientific_papers/pubmed",
    wikihow="tfds:wikihow/all",
#    xsum="tfds:xsum", # uses datasets' xsum - so use xsum/process.py
)

RULE75 = False
TEST_ONLY = True

splits = ['test'] if TEST_ONLY else ['test', 'validation', 'train']

for dataset_name, input_pattern in dss.items():
    ds_ok = True
    for split in splits:
        if not ds_ok: continue
        try:
            ds = all_datasets.get_dataset(input_pattern + "-" + split, shuffle_files=False)
        except:
            ds_ok = False
            print(f"✗ {dataset_name} requires manual building once. "
                  "See {dataset_name}/process.txt for instructions")
            continue
            
        save_path = Path(f"data/{dataset_name}")
        save_path.mkdir(parents=True, exist_ok=True)
        src_path = save_path / f"{split}.source"
        tgt_path = save_path / f"{split}.target"
        with open(src_path, 'wt') as src_file, open(tgt_path, 'wt') as tgt_file:
            for i, d in enumerate(ds):
                src = d["inputs"].numpy().decode()
                tgt = d["targets"].numpy().decode()
                src_len, tgt_len = len(src), len(tgt)

                # sanity check: skip broken entries with len 0
                if not src_len or not tgt_len:
                    continue

                # a threshold to remove articles with summaries almost as long as the source
                if RULE75 and tgt_len >= 0.75*src_len:
                    continue
                
                src = re.sub(r'[\r\n]+', '<n>', src)
                tgt = re.sub(r'[\r\n]+', '<n>', tgt)
                
                src_file.write(src + '\n')
                tgt_file.write(tgt + '\n')        

        print(f"✓ {src_path}")
        print(f"✓ {tgt_path}")
