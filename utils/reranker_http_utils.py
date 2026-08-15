import dashscope
from dotenv import load_dotenv


load_dotenv()

def rerank_documents(query: str, documents: list[str]) -> list[float]:

    from processor.import_processor.config import get_config
    cfg = get_config()
    dashscope.api_key = cfg.text_rerank_api_key
    response = dashscope.TextReRank.call(
        model=cfg.text_rerank_model,
        query=query,
        documents=documents,
        top_n=len(documents),
        return_documents=False,
        instruct=cfg.text_rerank_instruct,
    )

    status_code = response.get("status_code")
    if status_code != 200:
        message = response.get("message")
        raise RuntimeError(f"DashScope rerank 调用失败: {message}")

    results = response.output.get("results", [])
    scores = [0.0] * len(documents)
    for item in results:
        index = item.get("index")
        score = item.get("relevance_score")
        scores[int(index)] = float(score)
    return scores