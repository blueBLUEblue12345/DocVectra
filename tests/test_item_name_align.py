"""商品名对齐规则单元测试"""
import pytest


def align_item_names(query_results):
    """
    商品名对齐规则（从 node_item_name_confirm.py 提取）
    """
    confirmed_item_names = []
    options = []

    for res in query_results:
        extracted_name = (res.get("extracted_name", "") or "").strip()
        matches = res.get("matches", []) or []
        if not matches:
            continue

        high = [m for m in matches if m.get("score", 0) > 0.85]
        mid = [m for m in matches if m.get("score", 0) >= 0.6]

        if len(high) == 1:
            confirmed_item_names.append(high[0].get("item_name"))
            continue

        if len(high) > 1:
            picked = None
            if extracted_name:
                for m in high:
                    if m.get("item_name") == extracted_name:
                        picked = m
                        break
            if not picked:
                picked = high[0]
            confirmed_item_names.append(picked.get("item_name"))
            continue

        if len(mid) > 0:
            for m in mid[:5]:
                options.append(m.get("item_name"))

    return {
        "confirmed_item_names": list(set(confirmed_item_names)),
        "options": list(set(options))
    }


class TestItemNameAlign:
    """测试商品名对齐 4 级规则"""

    def test_rule_a_single_high_confidence(self):
        """规则 a：单个高置信度（>0.85）直接确认"""
        query_results = [
            {
                "extracted_name": "华为P60",
                "matches": [
                    {"item_name": "华为P60 128G", "score": 0.90},
                ]
            }
        ]
        result = align_item_names(query_results)

        assert len(result["confirmed_item_names"]) == 1
        assert result["confirmed_item_names"][0] == "华为P60 128G"
        assert len(result["options"]) == 0

    def test_rule_b_multiple_high_confidence(self):
        """规则 b：多个高置信度（>0.85）优先匹配原始名"""
        query_results = [
            {
                "extracted_name": "华为P60",
                "matches": [
                    {"item_name": "华为P60", "score": 0.92},
                    {"item_name": "华为P60 Pro", "score": 0.88},
                ]
            }
        ]
        result = align_item_names(query_results)

        assert len(result["confirmed_item_names"]) == 1
        assert result["confirmed_item_names"][0] == "华为P60"

    def test_rule_b_no_exact_match_takes_highest(self):
        """规则 b：无精确匹配时取分数最高"""
        query_results = [
            {
                "extracted_name": "华为P60",
                "matches": [
                    {"item_name": "华为P60 Pro", "score": 0.90},
                    {"item_name": "华为P60 Art", "score": 0.87},
                ]
            }
        ]
        result = align_item_names(query_results)

        assert len(result["confirmed_item_names"]) == 1
        assert result["confirmed_item_names"][0] == "华为P60 Pro"

    def test_rule_c_mid_confidence_as_options(self):
        """规则 c：无高置信度，中置信度（≥0.6）作为候选"""
        query_results = [
            {
                "extracted_name": "华为P60",
                "matches": [
                    {"item_name": "华为P60 128G", "score": 0.75},
                    {"item_name": "华为P60 Pro", "score": 0.70},
                    {"item_name": "华为P50", "score": 0.65},
                ]
            }
        ]
        result = align_item_names(query_results)

        assert len(result["confirmed_item_names"]) == 0
        assert len(result["options"]) == 3
        assert "华为P60 128G" in result["options"]

    def test_rule_d_no_match(self):
        """规则 d：无匹配（<0.6）返回空"""
        query_results = [
            {
                "extracted_name": "华为P60",
                "matches": [
                    {"item_name": "小米15", "score": 0.45},
                    {"item_name": "iPhone 15", "score": 0.40},
                ]
            }
        ]
        result = align_item_names(query_results)

        assert len(result["confirmed_item_names"]) == 0
        assert len(result["options"]) == 0

    def test_empty_matches(self):
        """空匹配列表返回空"""
        query_results = [
            {
                "extracted_name": "华为P60",
                "matches": []
            }
        ]
        result = align_item_names(query_results)

        assert len(result["confirmed_item_names"]) == 0
        assert len(result["options"]) == 0

    def test_multiple_extracted_names(self):
        """多个提取的商品名分别处理"""
        query_results = [
            {
                "extracted_name": "华为P60",
                "matches": [{"item_name": "华为P60 128G", "score": 0.90}]
            },
            {
                "extracted_name": "小米15",
                "matches": [{"item_name": "小米15 Pro", "score": 0.88}]
            }
        ]
        result = align_item_names(query_results)

        assert len(result["confirmed_item_names"]) == 2

    def test_deduplication(self):
        """去重：相同商品名不重复确认"""
        query_results = [
            {
                "extracted_name": "华为P60",
                "matches": [{"item_name": "华为P60 128G", "score": 0.90}]
            },
            {
                "extracted_name": "P60",
                "matches": [{"item_name": "华为P60 128G", "score": 0.88}]
            }
        ]
        result = align_item_names(query_results)

        assert len(result["confirmed_item_names"]) == 1

    def test_exact_threshold_0_85(self):
        """恰好 0.85 分不算高置信度"""
        query_results = [
            {
                "extracted_name": "华为P60",
                "matches": [{"item_name": "华为P60 128G", "score": 0.85}]
            }
        ]
        result = align_item_names(query_results)

        assert len(result["confirmed_item_names"]) == 0
        assert len(result["options"]) == 1
