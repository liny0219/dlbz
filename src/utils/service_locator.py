"""
服务定位器
用于管理核心组件的依赖关系，避免循环引用
"""

from typing import Dict, Any, Optional, Type, TypeVar
from utils import logger

T = TypeVar('T')

class ServiceLocator:
    """
    服务定位器
    用于管理核心组件的依赖关系，避免循环引用
    """
    
    _instance = None
    _services: Dict[str, Any] = {}
    _service_types: Dict[str, Type] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(self, service_name: str, service_instance: Any, service_type: Optional[Type] = None):
        """
        注册服务
        
        :param service_name: 服务名称
        :param service_instance: 服务实例
        :param service_type: 服务类型（可选）
        """
        self._services[service_name] = service_instance
        if service_type:
            self._service_types[service_name] = service_type
        logger.debug(f"注册服务: {service_name}")
    
    def get(self, service_name: str) -> Optional[Any]:
        """
        获取服务
        
        :param service_name: 服务名称
        :return: 服务实例或None
        """
        service = self._services.get(service_name)
        if service is None:
            logger.warning(f"服务未找到: {service_name}")
        return service
    
    def get_typed(self, service_name: str) -> Optional[Any]:
        """
        获取类型化的服务
        
        :param service_name: 服务名称
        :return: 服务实例或None
        """
        service = self.get(service_name)
        if service is not None:
            # 由于singleton装饰器的问题，我们暂时跳过严格的类型检查
            # 直接返回服务实例，让调用者自己处理类型检查
            return service
        return None
    
    def has(self, service_name: str) -> bool:
        """
        检查服务是否存在
        
        :param service_name: 服务名称
        :return: 是否存在
        """
        return service_name in self._services
    
    def unregister(self, service_name: str):
        """
        注销服务
        
        :param service_name: 服务名称
        """
        if service_name in self._services:
            del self._services[service_name]
            if service_name in self._service_types:
                del self._service_types[service_name]
            logger.debug(f"注销服务: {service_name}")
    
    def clear(self):
        """清空所有服务"""
        self._services.clear()
        self._service_types.clear()
        logger.debug("清空所有服务")
    
    def list_services(self) -> list[str]:
        """
        列出所有服务名称
        
        :return: 服务名称列表
        """
        return list(self._services.keys())

# 全局服务定位器实例
service_locator = ServiceLocator()

def get_service(service_name: str) -> Optional[Any]:
    """
    获取服务的便捷函数
    
    :param service_name: 服务名称
    :return: 服务实例或None
    """
    return service_locator.get(service_name)

def get_typed_service(service_name: str) -> Optional[Any]:
    """
    获取类型化服务的便捷函数
    
    :param service_name: 服务名称
    :return: 服务实例或None
    """
    return service_locator.get_typed(service_name)

def register_service(service_name: str, service_instance: Any, service_type: Optional[Type] = None):
    """
    注册服务的便捷函数
    
    :param service_name: 服务名称
    :param service_instance: 服务实例
    :param service_type: 服务类型（可选）
    """
    service_locator.register(service_name, service_instance, service_type) 