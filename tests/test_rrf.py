"""RRF 融合算法单元测试"""
import pytest


def rrf_merge(rrf_inputs, k=60, max_results=None):
    """
    RRF 融合算法实现（从 node_rrf.py 提取）
    """
    chunk_scores = {}
    chunk_data = {}

    for rrf_input, weight in rrf_inputs:
        for rank, doc in enumerate(rrf_input, start=1):
            chunk_id = doc.get('chunk_id')
            chunk_scores[chunk_id] = chunk_scores.get(chunk_id, 0.0) + weight / (k + rank)
            chunk_data.setdefault(chunk_id, doc)

    unsorted_results = [(chunk_data[cid], score) for cid, score in chunk_scores.items()]
    sorted_results = sorted(unsorted_results, key=lambda x: x[1], reverse=True)

    return sorted_results[:max_results] if max_results else sorted_results


class TestRrfMerge:
    """测试 RRF 融合算法"""

    def test_single_source_basic(self):
        """单路搜索基础场景"""
        rrf_inputs = [
            ([{"chunk_id": "c1", "content": "内容1"}], 1.0),
        ]
        results = rrf_merge(rrf_inputs, k=60)

        assert len(results) == 1
        assert results[0][0]["chunk_id"] == "c1"
        assert results[0][1] == pytest.approx(1.0 / (60 + 1))

    def test_two_sources_same_chunk(self):
        """两路搜索命中同一 chunk，分数应累加"""
        doc = {"chunk_id": "c1", "content": "内容1"}
        rrf_inputs = [
            ([doc], 1.0),
            ([doc], 1.0),
        ]
        results = rrf_merge(rrf_inputs, k=60)

        assert len(results) == 1
        expected_score = 1.0 / (60 + 1) + 1.0 / (60 + 1)
        assert results[0][1] == pytest.approx(expected_score)

    def test_two_sources_different_chunks(self):
        """两路搜索命中不同 chunk，按分数排序"""
        doc1 = {"chunk_id": "c1", "content": "内容1"}
        doc2 = {"chunk_id": "c2", "content": "内容2"}
        rrf_inputs = [
            ([doc1], 1.0),
            ([doc2], 0.5),
        ]
        results = rrf_merge(rrf_inputs, k=60)

        assert len(results) == 2
        assert results[0][0]["chunk_id"] == "c1"
        assert results[1][0]["chunk_id"] == "c2"
        assert results[0][1] > results[1][1]

    def test_rank_position_matters(self):
        """排名位置影响分数，rank 1 > rank 2"""
        doc1 = {"chunk_id": "c1", "content": "内容1"}
        doc2 = {"chunk_id": "c2", "content": "内容2"}
        rrf_inputs = [
            ([doc1, doc2], 1.0),
        ]
        results = rrf_merge(rrf_inputs, k=60)

        assert results[0][0]["chunk_id"] == "c1"
        assert results[0][1] > results[1][1]

    def test_weight_affects_score(self):
        """权重影响最终分数"""
        doc = {"chunk_id": "c1", "content": "内容1"}
        results_high = rrf_merge([([doc], 2.0)], k=60)
        results_low = rrf_merge([([doc], 0.5)], k=60)

        assert results_high[0][1] > results_low[0][1]

    def test_max_results_limit(self):
        """max_results 参数限制返回数量"""
        docs = [{"chunk_id": f"c{i}", "content": f"内容{i}"} for i in range(10)]
        rrf_inputs = [(docs, 1.0)]
        results = rrf_merge(rrf_inputs, k=60, max_results=5)

        assert len(results) == 5

    def test_empty_input(self):
        """空输入返回空列表"""
        results = rrf_merge([], k=60)
        assert results == []

    def test_duplicate_chunk_keeps_first(self):
        """重复 chunk_id 保留首次出现的版本"""
        doc_v1 = {"chunk_id": "c1", "content": "版本1"}
        doc_v2 = {"chunk_id": "c1", "content": "版本2"}
        rrf_inputs = [
            ([doc_v1], 1.0),
            ([doc_v2], 1.0),
        ]
        results = rrf_merge(rrf_inputs, k=60)

        assert len(results) == 1
        assert results[0][0]["content"] == "版本1"
