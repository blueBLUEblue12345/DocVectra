"""Milvus 表达式转义单元测试"""
import pytest


def escape_milvus_string(value):
    """
    转义 Milvus 表达式中的特殊字符（从 milvus_utils.py 提取）
    """
    if not isinstance(value, str):
        value = str(value)
    return value.replace("\\", "\\\\").replace("'", "\\'")


class TestEscapeMilvusString:
    """测试 Milvus 表达式字符串转义"""

    def test_no_special_chars(self):
        """无特殊字符直接返回"""
        result = escape_milvus_string("华为P60")
        assert result == "华为P60"

    def test_escape_single_quote(self):
        """转义单引号"""
        result = escape_milvus_string("华为'P60")
        assert result == "华为\\'P60"

    def test_escape_backslash(self):
        """转义反斜杠"""
        result = escape_milvus_string("华为\\P60")
        assert result == "华为\\\\P60"

    def test_escape_both(self):
        """同时转义反斜杠和单引号"""
        result = escape_milvus_string("华为\\'P60")
        assert result == "华为\\\\\\'P60"

    def test_empty_string(self):
        """空字符串返回空"""
        result = escape_milvus_string("")
        assert result == ""

    def test_multiple_quotes(self):
        """多个单引号全部转义"""
        result = escape_milvus_string("华为'P60'Pro")
        assert result == "华为\\'P60\\'Pro"

    def test_non_string_input(self):
        """非字符串输入转为字符串"""
        result = escape_milvus_string(123)
        assert result == "123"

    def test_chinese_characters(self):
        """中文字符不转义"""
        result = escape_milvus_string("华为激光多功能一体机")
        assert result == "华为激光多功能一体机"

    def test_mixed_content(self):
        """混合内容：中文 + 英文 + 特殊字符"""
        result = escape_milvus_string("华为'P60\\Pro")
        assert result == "华为\\'P60\\\\Pro"

    def test_injection_prevention(self):
        """防止注入：转义后的字符串在表达式中安全"""
        malicious = "test' OR '1'='1"
        result = escape_milvus_string(malicious)
        assert result == "test\\' OR \\'1\\'=\\'1"

        quoted = f'"{result}"'
        expr = f"item_name in [{quoted}]"
        assert expr == 'item_name in ["test\\\' OR \\\'1\\\'=\\\'1"]'
