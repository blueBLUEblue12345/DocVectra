import asyncio
import json

import httpx
from mcp.client.streamable_http import streamable_http_client
from mcp import ClientSession

from processor.query_processor.base import NodeBase
from processor.query_processor.state import QueryGraphState
from tools.logger import logger
from utils.json_format_utils import format_json


class NodeWebSearchMcp(NodeBase):
    """
    节点功能，调用外部搜索引擎补充信息
    """

    # 覆盖基类的 name 属性，标识节点名称
    name: str = "node_web_search_mcp"

    def process(self, state: QueryGraphState) -> QueryGraphState:

        query = state.get("rewritten_query", "")
        docs = []
        # 如果没有查询内容，直接返回
        if query:
            try:
                result = asyncio.run(self._mcp_call(query))
            except BaseException as e:
                logger.error(f"MCP 调用异常: {e!r}")
                if hasattr(e, 'exceptions'):
                    for sub in e.exceptions:
                        logger.error(f"  子异常: {sub!r}")
                return {}

            if result:
                logger.info(f"MCP 原始返回类型: {type(result)}")
                logger.info(f"MCP 原始返回: {result}")

                # 解析返回结果
                if hasattr(result, 'content') and result.content:
                    for content_block in result.content:
                        logger.info(f"content_block 类型: {type(content_block)}, 内容: {content_block}")
                        text = getattr(content_block, 'text', None) or str(content_block)
                        if not text or not text.strip():
                            continue
                        try:
                            data = json.loads(text)
                            pages = data.get("pages") or []
                            for item in pages:
                                snippet = (item.get("snippet") or "").strip()
                                url = (item.get("url") or "").strip()
                                title = (item.get("title") or "").strip()
                                if not snippet:
                                    continue
                                docs.append({"title": title, "url": url, "snippet": snippet})
                        except json.JSONDecodeError:
                            logger.warning(f"非 JSON 内容: {text[:200]}")

                logger.info(f"MCP 搜索结果: {docs}")

        if docs:
            return {"web_search_docs": docs}
        return {}


    async def _mcp_call(self, query):
        mcp_url = self.config.mcp_base_url
        api_key = self.config.mcp_api_key

        # 创建带鉴权头的 httpx 客户端
        http_client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0
        )

        async with streamable_http_client(mcp_url, http_client=http_client) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # 列出可用工具
                tools = await session.list_tools()
                logger.info(f"可用工具: {[t.name for t in tools.tools]}")

                # 调用搜索工具
                result = await session.call_tool(
                    name="bailian_web_search",
                    arguments={"query": query, "count": 5}
                )
                return result




if __name__ == "__main__":

    init_state = {
        "rewritten_query": "关于Lenovo激光多功能一体机，感光鼓和墨粉盒有多久寿命？"
    }

    # 执行节点的业务调用
    node_web_search_mcp = NodeWebSearchMcp()
    result = node_web_search_mcp(init_state)
    logger.info(format_json(result, indent=4))