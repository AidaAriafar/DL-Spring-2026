import re
def _tokenize(text: str) -> set[str]:
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return set(text.split())

def jaccard_similarity(set1: set[str], set2: set[str]) -> float:
    if not set1 or not set2: return 0.0
    return len(set1.intersection(set2)) / len(set1.union(set2))

def deduplicate_paragraphs(text: str, threshold: float = 0.7) -> str:
    paragraphs = [p.strip() for p in text.split('\n') if len(p.strip()) > 30]
    unique_paras =[]
    unique_tokens_list= []
    
    for p in paragraphs:
        p_tokens = _tokenize(p)
        if not p_tokens: continue
            
        is_duplicate = any(
            jaccard_similarity(p_tokens, u_tokens) > threshold 
            for u_tokens in unique_tokens_list
        )
        if not is_duplicate:
            unique_paras.append(p)
            unique_tokens_list.append(p_tokens)
    return "\n\n".join(unique_paras)
