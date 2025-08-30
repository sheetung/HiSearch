from __future__ import annotations
import sys
import os
import importlib.machinery
import types
from langbot_plugin.api.definition.components.common.event_listener import EventListener
from langbot_plugin.api.entities import events, context
from langbot_plugin.api.entities.builtin.platform import message as platform_message
from langbot_plugin.api.entities.builtin.provider import message as provider_message

# 获取当前脚本所在目录（项目根目录）
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))

# 确保项目根目录在 sys.path
if project_root not in sys.path:
    sys.path.append(project_root)

# ----------- 注册 driver 包别名 -----------
driver_path = os.path.join(project_root, "OnePanSearchApi", "driver")
if os.path.isdir(driver_path):
    if driver_path not in sys.path:
        sys.path.append(driver_path)

    # 构造一个虚拟包 "driver"，指向 OnePanSearchApi/driver
    spec = importlib.machinery.ModuleSpec("driver", None, is_package=True)
    driver_module = types.ModuleType("driver")
    driver_module.__path__ = [driver_path]
    sys.modules["driver"] = driver_module
# -----------------------------------------

from OnePanSearchApi.main import SourceQuery, search_pan


class DefaultEventListener(EventListener):

    def __init__(self):
        super().__init__()
        self.trigger_keyword = "搜"

        @self.handler(events.PersonMessageReceived)
        @self.handler(events.GroupMessageReceived)
        async def handle_search_request(event_context: context.EventContext):
            """处理用户搜索请求"""
            message_chain = event_context.event.message_chain
            user_text = self.get_user_text(message_chain)

            if not user_text.startswith(self.trigger_keyword):
                return

            search_content = user_text[len(self.trigger_keyword):].strip()
            if not search_content:
                await event_context.reply(
                    platform_message.MessageChain([
                        platform_message.Plain(
                            text="请输入搜索关键词，格式: 搜 <关键词>"
                        )
                    ])
                )
                return

            # 从插件配置读取参数
            plugin_config_ = self.plugin.get_config()
            # print(f'plugin_config_: {plugin_config_}')
            fromSite = plugin_config_.get("fromSite", "kk大厅")
            type_ = plugin_config_.get("type", "夸克网盘")
            # page = plugin_config_.get("resCounts", 1)
            page = 1
            pageSize = plugin_config_.get("resCounts", 5)

            # print(f'fromSite: {fromSite}, type: {type_}, page: {page}, pageSize: {pageSize}')

            try:
                # 构造 SourceQuery
                source = SourceQuery.from_query(
                    keyword=search_content,
                    fromSite=fromSite,
                    type=type_,
                    page=page,
                    pageSize=pageSize
                )

                await event_context.reply(
                    platform_message.MessageChain([
                        platform_message.Plain(
                            text=f"正在搜索: {search_content}"
                        )
                    ])
                )

                result = await search_pan(source)
                result['page'] = page
                result['pageSize'] = pageSize

                reply_text = self.format_search_result(result)
                await event_context.reply(
                    platform_message.MessageChain([platform_message.Plain(text=reply_text)])
                )

            except Exception as e:
                await event_context.reply(
                    platform_message.MessageChain([
                        platform_message.Plain(text=f"搜索出错: {str(e)}")
                    ])
                )

    def get_user_text(self, message_chain):
        """提取用户输入文本"""
        return "".join(
            element.text for element in message_chain
            if isinstance(element, platform_message.Plain)
        ).strip()

    def format_search_result(self, result) -> str:
        """格式化搜索结果为文本"""
        if not result or not result['data']:
            return "未找到相关资源"
        lines = []
        for i, item in enumerate(result['data'][:5], 1):
            lines.append(f"[{item.code}] {item.name}")
            lines.append(f"类型: {item.type}")
            lines.append(f"来源: {item.fromSite}")
            lines.append(f"链接: {item.url}")
            if item.pwd:
                lines.append(f"提取码: {item.pwd}")
            lines.append("-" * 3)
        if result['total'] > 5:
            lines.append(f"显示前5条，共{result['total']}条结果")
        return "\n".join(lines)

