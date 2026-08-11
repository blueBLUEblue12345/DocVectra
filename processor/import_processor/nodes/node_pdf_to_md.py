import json
import logging
import shutil
import time
import zipfile
from pathlib import Path

import requests

from processor.import_processor.base import BaseNode, setup_logging
from processor.import_processor.exceptions import StateFieldError, FileProcessingError, ConfigurationError, \
    PdfConversionError
from processor.import_processor.nodes.node_entry import NodeEntry
from processor.import_processor.state import ImportGraphState


class NodePDFToMD(BaseNode):
    """
    PDF 转 Markdown 节点：PDF结构化解析
    """

    name = "node_pdf_to_md"

    def process(self, state: ImportGraphState):
        #1.参数校验并返回Path结果
        pdf_path_obj,output_dir_obj = self.step_1_validate_paths(state)

        #2.将PDF上传到MinerU并轮询结果最后得到解压文件路径
        zip_url = self._step_2_upload_and_poll(pdf_path_obj)
        self.logger.info(zip_url)

        #3.下载ZIP包并解压并且得到md的绝对路径
        md_path = self._step_3_download_and_extract(zip_url,output_dir_obj,pdf_path_obj.stem)

        # 4.将MD文件的内容都取出来
        with open(md_path,"r",encoding="utf-8") as f:
            md_content = f.read()

        #5.返回结果
        return {
            "md_content": md_content,
            "md_path": md_path
        }


    def step_1_validate_paths(self, state: ImportGraphState):
        """
        步骤1：校验PDF文件路径和输出目录
        核心职责：参数非空校验 | 路径转换 | PDF文件有效性校验 | 输出目录自动创建
        返回：合法的PDF文件Path对象、输出目录Path对象
        异常：StateFieldError(参数缺失)、FileProcessingError(文件无效)
        """
        #1.参数的非空校验
        pdf_path = state.get("pdf_path")
        if not pdf_path:
            raise StateFieldError(filed_name="pdf_path",message="pdf_path路径不能为空",expected_type=str)

        file_dir = state.get("file_dir")
        if not file_dir:
            raise StateFieldError(filed_name="file_dir", message="file_dir路径不能为空", expected_type=str)
        #2.转换为Path对象
        pdf_path_obj = Path(pdf_path)
        file_dir_obj = Path(file_dir)

        #3.pdf是否存在
        if not pdf_path_obj.exists():
            raise FileProcessingError(f"该文件{pdf_path_obj.name}不存在")

        #4.输出目录不存在则创建目录
        if not file_dir_obj.exists():
            self.logger.info("输出目录{file_dir_obj.absolute()}不存在创建中.....")
            file_dir_obj.mkdir(parents=True,exist_ok=True)

        return pdf_path_obj, file_dir_obj

    def _step_2_upload_and_poll(self, pdf_path_obj: Path):
        """
        步骤2：上传PDF至MinerU并轮询解析任务状态
        核心流程：配置校验 → 获取上传链接 → 文件上传 → 任务轮询（直至完成/失败/超时）
        参数：pdf_path_obj-已校验的PDF Path对象
        返回：解析结果ZIP包下载链接full_zip_url
        异常：ValueError(配置缺失)、RuntimeError(请求/上传失败)、TimeoutError(任务超时)
        """
        # 1、配置文件校验
        if not self.config.mineru_base_url:
            raise ConfigurationError("MinerU配置缺失：请在 .env 文件中正确配置 MINERU_BASE_URL 参数")
        if not self.config.mineru_api_token:
            raise ConfigurationError("MinerU配置缺失：请在 .env 文件中正确配置 MINERU_API_TOKEN 参数")

        #2.调用MinerU的远程APi接口，实现文档上传

        token = self.config.mineru_api_token
        url = f"{self.config.mineru_base_url}/file-urls/batch"
        header = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        data = {
            "files": [
                {"name": "demo.pdf", "data_id": "abcd"}
            ],
            "model_version": "vlm"
        }
        file_path = ["demo.pdf"]
        response = requests.post(url, headers=header, json=data)
        if response.status_code != 200:
            raise PdfConversionError('获取上传链接失败. 响应码:{} ,响应结果:{}'.format(response.status_code, response))

        result = response.json()
        if result["code"] != 0:
            raise PdfConversionError('获取上传链接失败. 返回数据'.format(result["msg"]))

        batch_id = result["data"]["batch_id"]
        urls = result["data"]["file_urls"]


        #3.文档上传
        with open(pdf_path_obj, 'rb') as f:
            res_upload = requests.put(urls[0], data=f)
            if res_upload.status_code != 200:
                raise PdfConversionError(f"文件{urls[0]}上传失败.")


            self.logger.info("文件上传成功")

        #4.获取解析结果
        poll_url = f"{self.config.mineru_base_url}/extract-results/batch/{batch_id}"


        #轮询解析结果
        start_time = time.time() #记录当前时间
        timeout_seconds =600 #最大的超时时间
        poll_interval =3 #轮询间隔
        self.log_step(step_name="轮询开始",
                             message=f"轮询间隔:{poll_interval}s,超时时间:{timeout_seconds}s,batch_id:{batch_id}"
                             )
        while True:
            # 已消耗时间
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_seconds:
                raise TimeoutError(f"【任务轮询】超时！任务处理超{timeout_seconds}秒，batch_id：{batch_id}")

            # 发起轮询请求，短超时10秒，异常则重试
            try:
                res_poll = requests.get(url=poll_url, headers=header, timeout=10)
            except Exception as e:
                self.logger.warning(f"【任务轮询】网络请求异常，{poll_interval}秒后重试：{str(e)}，batch_id：{batch_id}")
                time.sleep(poll_interval)
                continue

            # 处理HTTP响应错误
            if res_poll.status_code != 200:
                raise PdfConversionError(f"【任务轮询】HTTP请求失败，状态码：{res_poll.status_code}，响应内容：{res_poll}")

            # 解析轮询结果，校验业务状态
            poll_data = res_poll.json()
            if poll_data["code"] != 0:
                raise PdfConversionError(f"【任务轮询】业务错误，返回数据：{poll_data}")

            extract_results = poll_data["data"]["extract_result"]

            # 获取结果
            result_item = extract_results[0]
            data_state = result_item["state"]

            # 状态为 done
            if data_state == "done":
                self.logger.info(f"【任务轮询】解析任务完成！总耗时{int(elapsed_time)}s，batch_id：{batch_id}")

                full_zip_url = result_item["full_zip_url"]
                self.logger.info(f"【任务轮询】返回ZIP包下载链接：{full_zip_url}，batch_id：{batch_id}")

                return full_zip_url

            elif data_state == "failed":
                err_msg = result_item.get("err_msg", "未知错误，无具体信息")
                raise PdfConversionError(f"【任务轮询】解析任务失败！batch_id：{batch_id}，错误信息：{err_msg}")

            else:
                self.logger.info(
                    f"【任务轮询】处理中... 已耗时{int(elapsed_time)}s，状态：{data_state}， batch_id：{batch_id}")
                time.sleep(poll_interval)

    def _step_3_download_and_extract(self, zip_url: str, output_dir_obj: Path, pdf_stem: str) -> str:
        """
       步骤3：下载MinerU解析结果ZIP包并解压，提取目标MD文件
       核心流程：下载ZIP → 清理旧目录并解压 → 查找MD文件 → 重命名统一为PDF同名
       参数：zip_url-ZIP包下载链接；output_dir_obj-输出目录Path；pdf_stem-PDF无后缀纯名称
       返回：最终MD文件的字符串格式绝对路径
       异常：RuntimeError(下载失败)
       """
        response = requests.get(zip_url)

        if response.status_code != 200:
            raise FileProcessingError(f"下载失败")

        #定义zip包的保存路径
        zip_save_path = output_dir_obj/f"{pdf_stem}_result.zip"
        with open(zip_save_path, 'wb') as f:
            f.write(response.content)
        self.logger.info(f"下载成功")

        #解压zip

        #解压目录
        extract_target_dir = output_dir_obj/pdf_stem
        #删除原有目录
        if extract_target_dir.exists():
            shutil.rmtree(extract_target_dir)
        #创建解压目录
        extract_target_dir.mkdir(parents=True, exist_ok=True)
        #在目录下打开zip
        with zipfile.ZipFile(zip_save_path, "r") as zip_file_obj:
            zip_file_obj.extractall(extract_target_dir)

        self.logger.info(f"zip解压完成，解压目录在{extract_target_dir}")

        #改名然后返回绝对路径
        target_md_file =extract_target_dir/"full.md"
        new_md_path = target_md_file.with_name(f"{pdf_stem}.md")
        target_md_file.rename(new_md_path)

        return str(new_md_path.absolute())


if __name__ =="__main__":
    # 激活日志的全局配置
    setup_logging()

    #初始化图状态
    init_state = {
        "import_file_path":r"E:\doc\M7268系列用户手册.pdf",
        "file_dir":r"E:\output"
    }

    #创建节点对象
    node_entry = NodeEntry()
    #执行节点的元测试
    result = node_entry(init_state)

    #执行PDF转MD节点
    node_pdf_to_md = NodePDFToMD()
    result = node_pdf_to_md(result)

    #将返回的图状态进行json的序列化
    json_state = json.dumps(result,ensure_ascii = False,indent = 4)
    #输出
    logging.getLogger().info(json_state)