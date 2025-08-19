import os
import json
from .utils import *
import pandas as pd
from transformers import AutoModel

class RAG:
    
    def __init__(self, data_path, cache_dir, encoder_id, llm_tokenizer, llm_model):

        self.encoder = self.load_encoder(cache_dir, encoder_id)
        self.tokenizer = self.load_tokenizer(cache_dir, encoder_id)
        self.index = self.load_index(data_path)
        self.llm_tokenizer = llm_tokenizer
        self.llm_model = llm_model
        self.index_id, self.id_corpus = self.load_corpus(data_path)
        
    @staticmethod
    def load_index(data_path):
        index = load_faiss_index(data_path + '/indexes/ivf/snowflake_ivf_6216.faiss')
        return index
    
    @staticmethod
    def load_corpus(data_path):
        corpus = pd.read_csv(data_path + 'data/CAST2019collection.tsv', sep='\\t')
        id_mapping = pd.read_csv(data_path + 'data/CAST2019_ID_Mapping.tsv', sep='\\t')
        index_id = dict(zip(id_mapping.index, id_mapping.id))
        id_corpus = dict(zip(corpus.id, corpus.text))
        
        return index_id, id_corpus
    
    @staticmethod
    def load_tokenizer(cache_dir, encoder_id):
        encoder_tokenizer = AutoTokenizer.from_pretrained(encoder_id, device_map='auto', cache_dir=cache_dir)
        return encoder_tokenizer
    
    @staticmethod
    def load_encoder(cache_dir, encoder_id):    
        encoder = AutoModel.from_pretrained(encoder_id, device_map='auto', cache_dir=cache_dir, add_pooling_layer=False)
        return encoder

    def handle_information_request(self, query, docs, mode = 'RAG'):
        
        indices = search_docs(query, self.encoder, self.tokenizer, self.index, top_k=5)
        docs = get_corpus(indices, self.index_id, self.id_corpus)
        
        if mode == 'RAG':
            prompt = "Provide a complete and accurate answer based on the background information above and your own knowledge. Do not mention the background source explicitly.\n\n"+f"Question: {query}\n\nBackground Information:\n" + "\n".join(docs)
            
            instruction = "You are a helpful assistant that answers questions clearly and accurately, using background information provided when helpful. Do not refer to 'passages' or any retrieval process. Just answer naturally, as if you know the information. If the backgroud do not contain helpful information, use all your knowledge to satisfy the information need."                   
        else:            
            prompt = query
            
            instruction =  "You are a helpful assistant that answers users' questions clearly and accurately."
        
        response = query_llm(prompt, instruction, self.llm_tokenizer, self.llm_model, temperature=0.7, max_new_tokens=1000)
        
        return response

    def handle_spatial_request(self, query, json_path):
        instruction = """
            You are a smart route summarizer. Your task is to generate a concise, natural-language description of a walking route based on the provided JSON input.

            The JSON contains:
            - Total path length and time,
            - A list of segments with navigation instructions (if any),
            - POIs (Points of Interest) per segment, categorized (e.g., cafe, restaurant, park),
            - Timing and distance information to and from origin/destination for each segment.

            Your job is to:
            1. Start with a short summary of the total route length and walking time.
            2. Describe segments embedding the navigation instruction (if available) and mentioning any interesting POIs in a friendly, conversational tone.
            3. Handle user constraints only if present in the user query. Constraints may involve:
            - Time (e.g., "stop around 5 minutes before arrival"),
            - Distance (e.g., "within 100 meters of the destination"),
            - POI type (e.g., "find a place to drink coffee").

            If a time-based constraint is mentioned, search for matching POIs in segments where `time_to_destination_min <= requested time`.
            If a distance-based constraint is mentioned, search in segments where `distance_to_destination_m <= requested distance`.

            Important:
            - Only apply these filters if the user mentions them.
            - Translate fuzzy POI goals like "drink a coffee" into relevant categories: [`cafe`, `bar`, `restaurant`, `bakery`].
            - If no POIs matching the constraint are found, say so clearly.

            The tone should be helpful and conversational. No Python or JSON output — only fluent text.
        """
        
        with open(json_path, "rt") as f:
            file_json = json.load(f)
            
        prompt = json.dumps(file_json)
        response = query_llm(prompt, instruction, self.llm_tokenizer, self.llm_model, max_new_tokens=2000, temperature=0.3)
        
        return response