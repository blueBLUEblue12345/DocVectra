"""断崖检测逻辑单元测试"""
import pytest


RERANK_MAX_TOPK = 10
RERANK_MIN_TOPK = 3
RERANK_GAP_ABS = 0.5
RERANK_GAP_RATIO = 0.25


def cliff_cutoff(ranked_docs):
    """
    断崖检测截断（从 node_rerank.py 提取）
    """
    if not ranked_docs:
        return []

    upper_bound = min(RERANK_MAX_TOPK, len(ranked_docs))
    lower_bound = min(RERANK_MIN_TOPK, upper_bound)

    cutoff_pos = upper_bound

    for idx in range(lower_bound - 1, upper_bound - 1):
        current_score = ranked_docs[idx].get("score")
        next_score = ranked_docs[idx + 1].get("score")

        if current_score is None or next_score is None:
            continue

        abs_gap = current_score - next_score
        rel_gap = abs_gap / (abs(current_score) + 1e-6)

        if abs_gap >= RERANK_GAP_ABS or rel_gap >= RERANK_GAP_RATIO:
            cutoff_pos = idx + 1
            break

    return ranked_docs[:cutoff_pos]


class TestCliffCutoff:
    """测试断崖检测截断逻辑"""

    def test_no_cliff_returns_all(self):
        """无断崖时返回全部文档"""
        docs = [
            {"content": "内容1", "score": 0.95},
            {"content": "内容2", "score": 0.90},
            {"content": "内容3", "score": 0.85},
        ]
        result = cliff_cutoff(docs)
        assert len(result) == 3

    def test_absolute_gap_triggers_cutoff(self):
        """绝对差距超过阈值触发截断（需要至少 4 条文档）"""
        docs = [
            {"content": "内容1", "score": 0.95},
            {"content": "内容2", "score": 0.90},
            {"content": "内容3", "score": 0.85},
            {"content": "内容4", "score": 0.30},
        ]
        result = cliff_cutoff(docs)
        assert len(result) == 3

    def test_relative_gap_triggers_cutoff(self):
        """相对差距超过阈值触发截断（需要至少 4 条文档）"""
        docs = [
            {"content": "内容1", "score": 0.90},
            {"content": "内容2", "score": 0.85},
            {"content": "内容3", "score": 0.80},
            {"content": "内容4", "score": 0.50},
        ]
        result = cliff_cutoff(docs)
        assert len(result) == 3

    def test_min_topk_respected(self):
        """最小 TopK 限制：即使有断崖也至少保留 MIN_TOPK 条"""
        docs = [
            {"content": "内容1", "score": 0.95},
            {"content": "内容2", "score": 0.30},
            {"content": "内容3", "score": 0.25},
        ]
        result = cliff_cutoff(docs)
        assert len(result) >= 3

    def test_max_topk_respected(self):
        """最大 TopK 限制：即使无断崖也不超过 MAX_TOPK 条"""
        docs = [{"content": f"内容{i}", "score": 0.95 - i * 0.01} for i in range(15)]
        result = cliff_cutoff(docs)
        assert len(result) <= 10

    def test_empty_input(self):
        """空输入返回空列表"""
        result = cliff_cutoff([])
        assert result == []

    def test_single_document(self):
        """单条文档直接返回"""
        docs = [{"content": "内容1", "score": 0.95}]
        result = cliff_cutoff(docs)
        assert len(result) == 1

    def test_none_scores_skipped(self):
        """None 分数跳过断崖检测"""
        docs = [
            {"content": "内容1", "score": 0.95},
            {"content": "内容2", "score": None},
            {"content": "内容3", "score": 0.85},
        ]
        result = cliff_cutoff(docs)
        assert len(result) == 3

    def test_exact_threshold_boundary(self):
        """恰好在阈值边界（需要至少 4 条文档）"""
        docs = [
            {"content": "内容1", "score": 0.95},
            {"content": "内容2", "score": 0.90},
            {"content": "内容3", "score": 0.85},
            {"content": "内容4", "score": 0.35},
        ]
        result = cliff_cutoff(docs)
        assert len(result) == 3
