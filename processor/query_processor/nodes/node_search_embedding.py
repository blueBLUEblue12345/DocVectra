from processor.query_processor.base import NodeBase
from processor.query_processor.state import QueryGraphState
from tools.logger import logger


class NodeSearchEmbedding(NodeBase):
     """
    节点功能：基于已确认主体名+改写后的用户问题，执行Milvus向量数据库混合检索
    """

     # 覆盖基类的 name 属性，标识节点名称
     name: str = "node_search_embedding"

     def process(self, state: QueryGraphState) -> QueryGraphState:
         """
         节点逻辑
         :param state: 工作流状态对象
         :return: 更新后的状态对象
         """

         # TODO
         logger.info(f"【{self.name}】节点逻辑")

         # return state
         return {"embedding_chunks":  []}
