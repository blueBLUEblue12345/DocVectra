import re
from typing import List, Dict, Tuple

from langchain_core.prompts import load_prompt

from processor.query_processor.prompt.answer_out import ANSWER_PROMPT
from tools.logger import logger

from processor.query_processor.base import NodeBase
from processor.query_processor.state import QueryGraphState
from utils.llm_utils import get_llm_client
from utils.mongo_history_utils import save_chat_message
from utils.sse_utils import push_to_session, SSEEvent
from utils.task_utils import add_done_task, set_task_result

MAX_CONTEXT_CHARS = 12000

class NodeAnswerOutput(NodeBase):
    """
    节点功能: 答案输出
    流程: 检查已有答案 → 构建提示词 → LLM 生成 → 写入历史 → 发送结束事件
    """

    # 覆盖基类的 name 属性，标识节点名称
    name: str = "node_answer_output"

    def process(self, state: QueryGraphState) -> QueryGraphState:
        """
        1 判断state 中的answer是否已经存在，如果存在直接输出answer中的答案，注意判断是否需要流式输出需要则流式输出
        2 根据state中的问题、重新问题、历史对话、提问商品（item_names）、 重排内容 组织prompt 并调用llm 生成答案
        3 调用大模型输出答案 注意判断是否需要流式输出需要则流式输出
        4 把答案写入到mongodb的history中 利用utils/mongo_history_utils.py中的save_chat_message方法
        5 做最后一次push操作（主要是为了触发前端图片渲染)
             {
                "answer": "HAK 180 烫金机的操作面板位于...（大模型生成的纯文本）...",
                "status": "completed",
                "image_urls": [
                    "http://local-server/images/panel_view.jpg",
                    "http://local-server/images/button_detail.jpg"
                ]
              }
        """

        # 阶段一：检查answer是否存在,如果存在直接输出answer中的答案
        answer_exists = self._step_1_check_answer(state)

        # 阶段二  如果没有answer则 构建 Prompt
        if not answer_exists:
            prompt = self._step_2_construct_prompt(state)
            state["prompt"] = prompt

            # 阶段三：  如果没有answer则 调用大模型输出答案
            self._step_3_generate_response(state, prompt)


            # 提取图片URL（用于历史记录和前端展示）
        image_urls = self._extract_images_from_docs(state.get("reranked_docs") or [])

        # 阶段四：把答案写入到mongodb的history中
        if state.get("answer"):
            logger.info("---写入MongoDB历史记录---")
            self._step_4_write_history(state, image_urls=image_urls)

        # 阶段五: 流式输出结束，发送 final 事件 [最后兜底，确保图片都能争取渲染和结束]
        logger.info(f"---发送 final 事件---图片为：{image_urls}")
        if state.get("is_stream"):
            push_to_session(
                state['session_id'],
                SSEEvent.FINAL,
                {
                    "answer": state["answer"],
                    "status": "completed",
                    "image_urls": image_urls  # 发送图片URL给前端
                }
            )

        logger.info("---node_answer_output 节点处理结束---")
        return state

    def _step_1_check_answer(self, state) -> bool:
        """
        阶段一：检查 state 中是否已有 answer。
        - 若已存在：按需推送流式 delta（用于 SSE），并返回 True
        - 若不存在：返回 False
        """
        answer = state.get("answer")
        is_stream = state.get("is_stream")
        if answer:
            if is_stream:
                logger.info("---Step 1: 发现已有答案，执行流式推送---")
                push_to_session(state["session_id"], SSEEvent.DELTA, {"delta": answer})
            else:
                set_task_result(state["session_id"], "answer", answer)
            return True
        else:
            return False

    def _step_2_construct_prompt(self, state: QueryGraphState) -> str:

        """
        阶段二：构建 Prompt
        根据state中的问题、重新问题、历史对话、提问商品（item_names）、 重排内容 组装 LLM 提示词
        """
        char_budget = MAX_CONTEXT_CHARS

        # 1. 获取问题和商品名
        # 优先使用重写后的问题
        question = state.get("rewritten_query") or state.get("original_query", "")
        item_names = state["item_names"]

        # 2. 格式化上下文文档
        context_str, char_budget = self._format_reranked_docs(
            state.get("reranked_docs") or [], char_budget
        )

        # 3. 格式化历史对话
        history_str, char_budget = self._format_chat_history(
            state.get("history") or [], char_budget
        )

        # 4. 格式化 Item Names (提问商品)
        item_names_str = ", ".join(item_names) if item_names else "无指定商品"

        # 5. 组装提示词
        prompt = ANSWER_PROMPT.format(
            context=context_str or "无参考内容",
            history=history_str if history_str else "暂无历史对话",
            item_names=item_names_str,
            question=question,
        )
        logger.info(f"组装后的提示词为：{prompt}")
        return prompt

    def _format_reranked_docs(self, reranked_docs: List[Dict], char_budget: int) -> Tuple[str, int]:
        """格式化重排序文档，带字符预算控制"""
        formatted_lines = []
        used_chars = 0

        # 从重排内容中，提取为资料字符串，不可超过限额
        # 优先使用结构化 reranked_docs（包含 source/chunk_id/url/score），便于约束与引用
        # ---------------------------------------------------------
        # 逻辑解释：
        # 1. 遍历重排序后的文档列表 (reranked_docs)，这些文档已经按相关性从高到低排序。
        # 2. 对每个文档提取关键信息 (text, source, chunk_id, url, title, score)。
        # 3. 构造 "元数据头 + 正文" 格式的字符串，例如：
        #    "[1] [local] [chunk_id=123] [score=0.95] [title=操作手册]
        #     这里是文档的正文内容..."
        # 4. 累加字符长度，如果超过 MAX_CONTEXT_CHARS (如 12000 字符)，则停止添加，
        #    确保 Prompt 长度在 LLM 的处理范围内，避免 Token 溢出。
        # ---------------------------------------------------------
        for idx, doc in enumerate(reranked_docs, start=1):
            content = doc.get("content")
            meta_tags = [f"[{idx}]"]
            for field, template in [
                ("source", "[source={}]"),
                ("chunk_id", "[chunk_id={}]"),
                ("url", "[url={}]"),
                ("title", "[title={}]"),
            ]:
                field_value = str(doc.get(field)).strip()
                if field_value:
                    meta_tags.append(template.format(field_value))

            relevance_score = doc.get("score")
            if relevance_score is not None:
                meta_tags.append(f"[score={float(relevance_score):.4f}]")

            doc_entry = " ".join(meta_tags) + "\n" + content

            if used_chars + len(doc_entry) > char_budget:
                break

            formatted_lines.append(doc_entry)
            used_chars += len(doc_entry) + 2

        return "\n\n".join(formatted_lines), char_budget - used_chars

    def _format_chat_history(self, chat_history: List[Dict], char_budget: int) -> Tuple[str, int]:
        """格式化历史对话"""
        formatted_lines = []
        used_chars = 0

        role_label_map = {"user": "用户", "assistant": "助手"}

        for message in chat_history:
            role = message.get("role", "")
            text = message.get("text", "")
            if not text or role not in role_label_map:
                continue

            formatted_line = f"{role_label_map[role]}: {text}"
            used_chars += len(formatted_line) + 1

            if used_chars > char_budget:
                return "\n".join(formatted_lines), char_budget - used_chars

            formatted_lines.append(formatted_line)

        return "\n".join(formatted_lines), char_budget - used_chars

    def _step_3_generate_response(self, state: QueryGraphState, prompt: str) -> QueryGraphState:
        """
        阶段三：生成回答
        调用llm生成答案，支持流式输出
        """
        logger.info("---Step 3: 开始生成回答 (LLM Generation)---")

        # 获取 LLM 客户端
        # 注意：这里我们使用统一的 get_llm_client 获取实例
        llm = get_llm_client()

        # 判断是否需要流式输出
        # 通常 state 中会注入 stream_queue 用于 SSE 推送
        session_id = state.get("session_id")
        is_stream = state.get("is_stream")

        if is_stream:
            logger.info(f"模式: 流式输出 (Streaming), Session: {session_id}")
            final_text = ""
            try:
                # 使用 stream 方法进行流式生成
                for chunk in llm.stream(prompt):
                    delta = getattr(chunk, "content", "") or ""
                    if delta:
                        final_text += delta
                        # 将增量内容放入队列
                        push_to_session(session_id, SSEEvent.DELTA, {"delta": delta})

                logger.info(f"流式输出完成，总长度: {len(final_text)}")

            except Exception as e:
                logger.error(f"流式生成出错: {e}", exc_info=True)
                # 发生错误时，尝试推送到前端
                push_to_session(session_id, SSEEvent.ERROR, {"error": str(e)})

            state["answer"] = final_text
        else:
            # 非流式直接调用
            logger.info(f"模式: 非流式输出 (Blocking), Session: {session_id}")
            try:
                response = llm.invoke(prompt)
                content = response.content
                state["answer"] = content
                set_task_result(session_id, "answer", content)
                logger.info(f"生成回答完成，长度: {len(content)}")
            except Exception as e:
                logger.error(f"生成回答出错: {e}", exc_info=True)
                state["answer"] = "抱歉，生成回答时出现错误。"

        return state

    def _extract_images_from_docs(self, docs):
        """
        辅助方法：从文档列表中提取图片URL

        核心逻辑：
        1. 遍历所有相关文档（包括本地知识库切片和联网搜索结果）。
        2. 策略一：直接检查文档的 'url' 字段（常见于联网搜索结果）。
           - 验证后缀名是否为图片格式 (.jpg, .png 等)。
        3. 策略二：使用正则表达式扫描文档 'text' 正文内容（常见于本地 Markdown 文档）。
           - 匹配 Markdown 图片语法: ![alt text](image_url)。
        4. 对提取到的 URL 进行去重处理，返回唯一图片列表。

        :param docs: 文档列表，每个文档为字典格式
        :return: 图片 URL 字符串列表
        """
        images = []
        seen = set() # 用于去重，避免同一张图片重复出现
        if not docs:
            return []
        # ---------------------------------------------------------
        # 正则表达式解释：r'!\[.*?\]\((.*?)\)'
        # 1. !\[   -> 匹配 Markdown 图片语法的开头 "![" (注意 [ 需要转义)
        # 2. .*?   -> 非贪婪匹配图片描述文本 (Alt Text)，即 [] 中间的内容
        # 3. \]    -> 匹配描述文本的结束符 "]"
        # 4. \(    -> 匹配 URL 部分的开始符 "("
        # 5. (.*?) -> 捕获组 (Group 1)：非贪婪匹配括号内的实际 URL 内容
        # 6. \)    -> 匹配 URL 部分的结束符 ")"
        # ( ... ) （不带反斜杠）：这就是 捕获组 。
        # 它的作用是告诉程序：“虽然我匹配了整个 ![...](...) 结构，但我 只要 这括号里的内容”。
        # ---------------------------------------------------------
        md_img_pattern = re.compile(r'!\[.*?\]\((.*?)\)')

        logger.info(f"开始提取图片，待处理文档数: {len(docs)}")

        for i, doc in enumerate(docs):
            # 1. 优先检查 url 字段 (主要针对 Web Search 结果)
            url = (doc.get("url") or "").strip()
            if url:
                # 简单后缀判断：确保是静态图片资源
                if url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg')):
                    if url not in seen:
                        logger.debug(f"文档[{i}] 发现图片 URL (字段): {url}")
                        seen.add(url)
                        images.append(url)

            # 2. 检查 text 字段中的 Markdown 图片 (主要针对 Local Chunk)
            text = (doc.get("content") or "").strip()
            if text:
                # findall 机制解释：
                # 正则表达式 r'!\[.*?\]\((.*?)\)' 中包含一个捕获组 (.*?)
                # 当存在捕获组时，findall 只返回括号内匹配到的内容（即 URL），而不是整个 ![...](...) 字符串
                # 示例：
                # 输入 text: "参考图片 ![面板图](http://img.com/1.jpg) 如下"
                # 返回 matches: ['http://img.com/1.jpg']
                matches = md_img_pattern.findall(text)
                for img_url in matches:
                    img_url = img_url.strip()
                    if img_url and img_url not in seen:
                        logger.debug(f"文档[{i}] 正文发现 Markdown 图片: {img_url}")
                        seen.add(img_url)
                        images.append(img_url)

        logger.info(f"图片提取完成，共找到 {len(images)} 张唯一图片: {images}")
        return images

    def _step_4_write_history(self, state: QueryGraphState, image_urls = None) -> QueryGraphState:
        """
        阶段四：把本轮答案写入 MongoDB history。
        利用 utils/mongo_history_utils.py 中的 save_chat_messages 方法。
        """
        session_id = state.get("session_id", "default")
        answer = (state.get("answer") or "").strip()
        item_names = state.get("item_names") or []

        try:
            if answer:
                save_chat_message(
                    session_id=session_id,
                    role="assistant",
                    text=answer,
                    rewritten_query="",
                    item_names=item_names,
                    image_urls=image_urls,
                    message_id=None
                )
        except Exception as e:
            # 写历史失败不应影响主链路
            logger.error(f"写入Mongo历史记录失败: {e}")

        return state

