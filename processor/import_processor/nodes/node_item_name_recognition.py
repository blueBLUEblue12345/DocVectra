import json
import logging
from typing import Tuple, List, Dict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pymilvus import DataType

from processor.import_processor import config
from processor.import_processor.base import BaseNode, setup_logging
from processor.import_processor.exceptions import StateFieldError
from processor.import_processor.state import ImportGraphState
from utils.embedding_utils import generate_embeddings
from utils.milvus_utils import escape_milvus_string, get_milvus_client


class NodeItemNameRecognition(BaseNode):
    """
    主体识别节点：主体识别与标签提取
    """

    name: str = "node_item_name_recognition"

    def process(self, state: ImportGraphState) -> ImportGraphState:
        """
        LangGraph 核心节点：商品主体名称识别
        流程总览：
            1. 提取输入
            2. 构建大模型上下文
            3. 调用大模型识别商品名称
            4. 回填商品名称到状态和切片
            5. 生成商品名称的稠密/稀疏向量
            6. 将数据存入Milvus向量数据库

        必要参数：task_id、file_title, chunks
        更新参数：item_name

        :param state: 工作流状态对象
        :return: 更新后的状态对象
        """

        # 步骤1：提取并校验输入
        file_title, chunks = self._step_1_get_inputs(state)

        # 步骤2：构建大模型识别的上下文
        context = self._step_2_build_context(chunks)

        # 步骤3：调用大模型识别商品名称
        item_name = self._step_3_call_llm(file_title, context)

        # 步骤4：回填商品名称到状态和切片
        self._step_4_update_chunks(state, chunks, item_name)

        # 步骤5：为商品名称生成稠密/稀疏向量
        dense_vector, sparse_vector = self._step_5_generate_vectors(item_name)

        # 步骤6：将数据存入Milvus向量数据库
        self._step_6_save_to_milvus(state, file_title, item_name, dense_vector, sparse_vector)


        # 打印识别结果
        self.logger.info(f"--- 识别完成: {item_name} ---")

        return state




    def _step_1_get_inputs(self, state: ImportGraphState) -> Tuple[str, List[Dict]]:
        """
        步骤 1: 接收并校验流程输入
        核心作用：
            1. 从流程状态中提取文件标题、文本切片核心数据
            2. 基础数据类型校验，保证下游流程输入有效性
        依赖的状态数据（上游节点产出）：
            - state["file_title"]: 上游提取的文件标题
            - state["chunks"]: 文本切片列表
        返回值：
            Tuple[str, List[Dict]]: (处理后的文件标题, 校验后的文本切片列表)
        """

        # 1、参数校验
        file_title = state.get("file_title")
        if not file_title:
            raise StateFieldError(field_name="file_title", message="文件标题不能为空", expected_type=str)

        chunks = state.get("chunks")
        if not chunks:
            raise StateFieldError(field_name="chunks", message="chunks不能为空", expected_type=list)

        if not isinstance(chunks, list):
            raise StateFieldError(field_name="chunks", message="chunks数据类型不正确", expected_type=list)

        return file_title, chunks


    def _step_2_build_context(self, chunks: List[Dict]) -> str:
        """
        步骤 2: 构造大模型商品名称识别的标准化上下文
        核心作用：
            1. 限制切片数量：仅取前k个切片，避免上下文过长
            2. 限制字符长度：总上下文字符限制，适配大模型输入上限
            3. 格式化内容：带序号的结构化格式，提升大模型识别精度
        参数说明：
            chunks: 文本切片列表
        返回值：
            str: 格式化后的上下文字符串
        """

        parts: List[str] = []
        total_chars = 0
        for idx, chunk in enumerate(chunks[:self.config.item_name_chunk_k], start = 1):

            # 1. 提取前k的切片，避免上下文过长
            chunk_title = chunk.get("title").strip()
            chunk_content = chunk.get("content").strip()

            # 2. 格式化切片
            piece = f"【切片{idx}】\n标题{chunk_title}\n内容：{chunk_content}"
            parts.append(piece)

            # 3. 计算累计的字符数
            total_chars += len(piece)

            # 4. 判断是否需要继续切分
            if total_chars > self.config.item_name_chunk_size:
                self.logger.warning(f"累计字符数{total_chars}已超过限制{self.config.item_name_chunk_size}，停止切分")
                break

        # 5. 使用换行符对切分后的片段进行连接
        context = "\n\n".join(parts).strip()

        # 6. 对返回结果进行二次截断
        final_context = context[:self.config.item_name_chunk_size]

        return final_context

    def _step_3_call_llm(self, file_title: str, context: str) -> str:
        """
        步骤 3: 调用大模型实现商品名称/型号精准识别
        核心逻辑：
            1. 上下文为空 → 直接返回file_title（兜底，无需调用大模型）
            2. 上下文非空 → 加载标准化prompt模板，构建大模型对话消息
            3. 调用大模型后对返回结果做清洗，过滤无效字符
            4. 大模型返回空/调用异常 → 均返回file_title兜底，保证流程不中断
        核心特性：
            - 提示词解耦：通过load_prompt加载本地模板，无需硬编码
            - 格式兼容：兼容不同LLM客户端返回格式，防止属性报错
            - 异常兜底：全异常捕获，大模型服务不可用时不影响主流程
        参数：
            file_title: 处理后的文件标题（异常/空值时的兜底值）
            context: 步骤2构建的结构化切片上下文（大模型识别的核心依据）
        返回值：
            str: 清洗后的商品名称（异常/空值时返回原始file_title）
        """

        # 1. 上下文为空时，直接返回文件标题，跳过大模型调用
        if not context:
            return file_title

        try:
            # 2. 加载商品名称识别prompt模板，动态传入文件标题和上下文
            # 构建大模型提示词（Prompt）
            prompt = f"""
                       请从以下信息中识别出商品名称与型号：
                       文件名：{file_title}

                       正文切片（用于辅助识别）：
                       {context}

                       要求：
                       1. 返回内容为字符串形式，最好是带品牌、型号和名称的完整商品名称。比如：苏伯尓5000W大功率电磁炉；
                       2. 返回结果应该只包含商品名称，不要添加任何解释或其他内容；
                       3. 如果无法识别商品名称,请返回空字符串。
                       """
            # 3. 初始化大模型客户端
            llm = ChatOpenAI(
                model=self.config.item_model,
                api_key=self.config.openai_api_key,
                base_url=self.config.openai_api_base,
                temperature=0.1,
                extra_body={"enable_thinking": False}
            )

            # 4. 标准化构建大模型对话消息：SystemMessage定义角色 + HumanMessage传递业务请求
            messages = [
                SystemMessage(content="你是一个专业的商品名称识别模型，请根据提供的信息，识别商品名称。"),
                HumanMessage(content=prompt)
            ]

            # 5. 调用大模型并获取返回结果
            resp = llm.invoke(messages)

            # 6. 获取返回值
            item_name = resp.content

            # 7. 数据清洗
            item_name = item_name.replace(" ", "").replace("\n", "").replace("\r", "").replace("\t", "")

            # 8. 大模型返回空 → 用文件标题兜底
            if not item_name:
                return file_title

            # 9. 返回识别的商品名称
            return item_name

        # 捕获所有异常：大模型调用超时、网络错误、格式错误等，均不中断主流程
        except Exception as e:
            self.logger.exception(f"步骤3：大模型调用失败，原因：{str(e)}")
            # 异常时返回文件标题兜底，保证流程继续执行
            return file_title

    def _step_4_update_chunks(self, state: ImportGraphState, chunks: List[Dict[str, str]], item_name: str):
        """
        步骤 4: 回填商品名称到流程状态和所有文本切片
        核心作用：
            1. 全局状态更新：将item_name存入state，供下游所有节点直接使用
            2. 切片数据补全：为每个切片添加item_name字段，保证数据一致性
            3. 状态同步：更新state中的chunks，确保切片修改全局生效
        设计思路：
            所有切片关联同一商品名称，保证后续向量入库、检索时的维度一致性
        参数：
            state: 流程状态对象
            chunks: 校验后的文本切片列表
            item_name: 步骤3识别并清洗后的商品名称
        """

        # 1. 遍历所有切片，为每个切片添加商品名字段，保证数据全链路一致
        for chunk in chunks:
            chunk["item_name"] = item_name

        # 2. 同步更新state中的切片列表，确保修改全局生效
        state["chunks"] = chunks

        # 3. 将商品名称存入全局状态，供下游节点调用
        state["item_name"] = item_name

    def _step_5_generate_vectors(self, item_name: str) -> Tuple[List, Dict]:
        """
        步骤 5: 为商品名称生成 BGE-M3 稠密 + 稀疏双向量（Milvus 向量检索核心）
        核心说明：
            - 稠密向量（dense_vector）：BGE-M3 固定 1024 维，记录文本深层语义信息
            - 稀疏向量（sparse_vector）：变长键值对，记录文本关键词/特征位置信息
        依赖工具：
            generate_embeddings：封装 BGE-M3 模型，批量生成双向量，兼容单条/批量输入
        参数：
            item_name: 步骤 3 识别的商品名称（非空，空值时直接返回空向量）
        返回值：
            Tuple[List, Dict]: (稠密向量列表，稀疏向量字典)
        """

        # 1. 商品名称为空 → 直接返回空向量
        if not item_name:
            return None, None

        # 2、调用向量生成工具：传入列表支持批量生成，单条数据仍用列表保证格式统一
        vectors = generate_embeddings([item_name])
        return vectors["dense"][0], vectors["sparse"][0]

    def _step_6_save_to_milvus(self, state: ImportGraphState, file_title: str, item_name: str, dense_vector,
                               sparse_vector):
        """
        步骤 6: 将商品名称、文件标题、双向量持久化到 Milvus 向量数据库
        核心逻辑：
            1. 客户端获取：获取单例 Milvus 客户端，连接失败则跳过
            2. 集合初始化：无集合则创建（定义 Schema+索引），有集合则直接使用
            3. 幂等性处理：删除同名商品数据，避免重复存储
            4. 数据插入：构造符合 Schema 的数据，非空向量才添加
            5. 集合加载：插入后强制加载集合，确保数据立即可查/Attu 可见
        参数：
            state: 流程状态对象，用于最终状态同步
            file_title: 处理后的文件标题
            item_name: 识别后的商品名称（主键去重依据）
            dense_vector: 步骤 5 生成的稠密向量（1024 维列表）
            sparse_vector: 步骤 5 生成的稀疏向量（字典格式）
        """
        try:

            # 1. 获取 Milvus 单例客户端，连接失败则直接返回
            # milvus_client = MilvusClient(uri=milvus_uri)
            milvus_client = get_milvus_client()
            if not milvus_client:
                self.logger.warning("无法获取 Milvus 客户端（连接失败），跳过数据保存")
                return

            # 2. 创建集合（如果不存在）
            collection_name = self.config.item_name_collection  # 集合名称
            if not milvus_client.has_collection(collection_name):
                self._create_item_name_collection(collection_name, milvus_client)

            # 3. 幂等性处理：删除同名商品数据（避免重复存储）
            # 转义商品名称（防止特殊字符导致filter解析失败）
            safe_item_name = escape_milvus_string(item_name)
            # 构建过滤表达式：item_name等于目标值
            filter_expr = f'item_name=="{safe_item_name}"'
            # 删除符合条件的数据
            milvus_client.delete(collection_name=collection_name, filter=filter_expr)

            # 4. 准备插入Milvus的数据
            data = {
                "file_title": file_title,  # 文件标题
                "item_name": item_name  # 商品名称
            }
            # 稠密向量非空则添加
            if dense_vector is not None:
                data["dense_vector"] = dense_vector
            # 稀疏向量非空则添加
            if sparse_vector is not None:
                data["sparse_vector"] = sparse_vector

            # 5. 插入数据（传入列表支持批量插入，这里仅1条）
            milvus_client.insert(collection_name=collection_name, data=[data])

            # 6. 把商品名称存入state（供下游节点使用）
            state["item_name"] = item_name

        # 捕获所有Milvus操作异常：连接中断、入库失败、索引错误等，不中断主流程
        except Exception as e:
            self.logger.warning(f"数据存入Milvus失败，原因：{str(e)}", exc_info=True)

    def _create_item_name_collection(self, collection_name, milvus_client):
        # 创建Schema（数据结构定义）
        # auto_id=True：主键自动生成；enable_dynamic_field=True：支持动态字段（允许插入 Schema 中未定义的字段）
        schema = milvus_client.create_schema(auto_id=True, enable_dynamic_field=True)

        # 添加主键字段（INT64类型，自增）
        schema.add_field(
            field_name="pk",
            datatype=DataType.INT64,
            is_primary=True,
            auto_id=True
        )
        # 添加文件标题字段（VARCHAR类型，最大长度65535）
        schema.add_field(
            field_name="file_title",
            datatype=DataType.VARCHAR,
            max_length=100
        )
        # 添加商品名称字段（VARCHAR类型，最大长度65535）
        schema.add_field(
            field_name="item_name",
            datatype=DataType.VARCHAR,
            max_length=100
        )
        # 添加稠密向量字段（FLOAT_VECTOR类型，1024维，BGE-M3模型固定维度）
        schema.add_field(
            field_name="dense_vector",
            datatype=DataType.FLOAT_VECTOR,
            dim=1024
        )
        # 添加稀疏向量字段（SPARSE_FLOAT_VECTOR类型，变长，适配BGE-M3的稀疏向量）
        schema.add_field(field_name="sparse_vector", datatype=DataType.SPARSE_FLOAT_VECTOR)

        # 3. 构建索引参数（提升向量检索性能）
        index_params = milvus_client.prepare_index_params()
        # 为稠密向量创建索引（IVF_FLAT：兼容性好，适合小数据量）
        # 核心是 “先聚类分桶、再桶内暴力精确检索”。
        index_params.add_index(
            field_name="dense_vector",  # 字段名
            index_name="dense_vector_index",  # 索引名
            index_type="IVF_FLAT",  # 索引类型（兼容所有Milvus版本）
            metric_type="COSINE",  # 相似度计算方式（余弦相似度）
            params={"nlist": 128}  # 聚类数（影响检索精度/速度）
        )

        # 为稀疏向量创建索引（SPARSE_INVERTED_INDEX：稀疏向量专用索引）
        index_params.add_index(
            field_name="sparse_vector",  # 字段名
            index_name="sparse_vector_index",  # 索引名
            index_type="SPARSE_INVERTED_INDEX",  # 索引类型
            metric_type="IP",  # 相似度计算方式（内积）
            params={
                "inverted_index_algo": "DAAT_MAXSCORE",
                # 高效的稀疏检索算法

                "normalize": True,
                # ↑ L2 归一化，让内积 (IP) 等价于余弦相似度

                "quantization": "none"
                # ↑ 关闭量化，保持原始精度：模型生成的向量已经压缩的一半的精度了（BGE_FP16=1），这里就不再压缩了
                # "quantization": "none" → 存储原始向量，不压缩
                # "quantization": "sq8" → 存储压缩后的向量（8-bit 量化
            })

        # 4. 创建集合（Schema + 索引）
        milvus_client.create_collection(
            collection_name=collection_name,
            schema=schema,
            index_params=index_params
        )




if __name__ == "__main__":

    setup_logging()

    md_path = r"E:\output\M7268系列用户手册\chunks.json"
    with open(md_path, "r", encoding="utf-8") as f:
        chunks_json = f.read()

    chunks = json.loads(chunks_json)
    init_state = {
        "chunks": chunks,
        "file_title": "M7268系列用户手册"
    }

    # 执行核心处理流程
    node_item_name_recognition = NodeItemNameRecognition()
    result = node_item_name_recognition(init_state)

    logging.getLogger().info(json.dumps(result, ensure_ascii=False, indent=4))