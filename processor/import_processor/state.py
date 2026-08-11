"""
导入流程状态类型定义

定义完整的状态结构和辅助函数
"""

from typing import TypedDict, List
import copy


class ImportGraphState(TypedDict):
    """
    导入流程图状态

    包含整个导入流程中传递的所有数据。
    使用 total=False 表示所有字段都是可选的。
    """

    # ==================== 任务标识 ====================
    task_id: str                    # 任务 ID，用于任务追踪

    # ==================== 控制标志 ====================
    is_md_read_enabled: bool        # 是否启用 MD 读取
    is_pdf_read_enabled: bool       # 是否启用 PDF 读取

    # ==================== 路径信息 ====================
    import_file_path: str           # 导入文件路径（原始输入）
    file_dir: str                   # 导入(出)文件目录
    pdf_path: str                   # PDF 文件路径
    md_path: str                    # 转换后 Markdown 文件路径

    # ==================== 文件信息 ====================
    file_title: str                 # 文件标题（不含扩展名）
    item_name: str                  # 识别出的商品/产品名称

    # ==================== 处理中间数据 ====================
    md_content: str                 # Markdown 文档内容
    chunks: List                    # 文档切片列表


GRAPH_DEFAULT_STATE: ImportGraphState = {

    "task_id": "",

    "is_pdf_read_enabled": False,

    "is_md_read_enabled": False,

    "file_dir": "",

    "import_file_path": "",

    "pdf_path": "",

    "md_path": "",

    "file_title": "",

    "md_content": "",

    "chunks": [],

    "item_name": "",

}

def get_default_state() -> ImportGraphState:
    """
    获取默认状态副本
    :return: 状态副本（避免全局污染）
    """
    return copy.deepcopy(GRAPH_DEFAULT_STATE)