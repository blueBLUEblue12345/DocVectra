from abc import abstractmethod, ABC
from typing import TypeVar
from tools.logger import logger
from processor.import_processor.config import get_config

T = TypeVar("T")  # 泛型状态类型
class NodeBase(ABC):

    name: str = "base_node"  # 节点名称，子类应覆盖

    @property
    def config(self):
        """获取全局配置单例，供子类通过 self.config 访问配置项"""
        return get_config()

    def __call__(self, state: T) -> T:
        """
        节点执行入口
        """
        try:
            # 1. 开始准备执行节点
            logger.info(f"--- {self.name} 开始啦 ---")

            # 2. 执行节点
            result = self.process(state)

            # 3. 执行节点成功
            logger.info(f"--- {self.name} 完成啦 ---")

            return result

        except Exception as e:
            logger.error(f"{self.name} 执行失败: {e}")
            raise

    @abstractmethod
    def process(self, state: T) -> T:
        """
        节点核心处理逻辑
        子类必须实现此方法
        :param state: 工作流状态对象
        :return: 更新后的状态对象
        """
        pass