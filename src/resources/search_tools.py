#%%
import os
import argparse
import faiss
import numpy as np
import pandas as pd
from time import time
from transformers import AutoModel, AutoTokenizer
from resources.tools import embed_passages
from argparse import Namespace
#%%
def generate_query_embeddings(queries, model_name, max_length=512, device='cuda'):
    """
    Generate embeddings for queries using a specified transformer model.
    """
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name, device_map='auto')
    model.eval()
    print(f"Generating embeddings using {model_name} model...")
    embeddings = embed_passages(queries, model, tokenizer, device=device, max_length=max_length)
    print(f"Generated embeddings for {len(queries)} queries.")
    return embeddings

def load_faiss_index(index_path):
    """Load a FAISS index from a file."""
    print(f"Loading FAISS index from: {index_path}")
    index = faiss.read_index(index_path)
    print(f"Index loaded successfully with {index.ntotal} vectors.")
    return index

def load_faiss_index_gpu(index_path):
    """Load a FAISS index from a file."""
    print(f"Loading FAISS index from: {index_path}")
    index = faiss.read_index(index_path)
    print("Moving index to GPU...")
    res = faiss.StandardGpuResources()
    index = faiss.index_cpu_to_gpu(index)
    print(f"Index loaded successfully with {index.ntotal} vectors.")
    return index

def search_index(index, query_embeddings, top_k):

    distances, indices = index.search(query_embeddings, top_k)

    return distances, indices

def load_data(file_path,  column_names=None,sep =None):
    """Generic function to load a dataset from a given file path."""
    if sep is None:
        df = pd.read_csv(file_path, header=None)
    else:
        df = pd.read_csv(file_path, sep=sep, header=None)
    if column_names:
        df.columns = column_names
    return df

def map_results(indices, distances, qids, id_mapping, top_k):
    """Convert FAISS search results into a structured DataFrame for evaluation."""
    results = {'qid': [], 'docno': [], 'rank': [], 'score': []}
    
    for i in range(len(distances)):
        topic_id = [qids[i]] * top_k
        doc_indices = [x for x in indices[i]]
        dist = distances[i].tolist()
        doc_ids = id_mapping.loc[doc_indices]['id'].tolist()
        rank = [j+1 for j in range(top_k)]
        
        if len(topic_id) == len(doc_ids) == len(rank) == len(dist):
            results['qid'] += topic_id
            results['docno'] += doc_ids
            results['rank'] += rank
            results['score'] += dist
            
    return pd.DataFrame(results)

