import re
from urllib.parse import urljoin

import aiohttp

from driver.common.utils.link_util import extract_info_entity2
from driver.panSearch import error
from driver.panSearch.model.search_result import SearchResult
from driver.common.utils.pan_type_util import get_pan_type


def parse_links(data: str):
    list = extract_info_entity2(data)
    results = []
    for link_info in list:
        results.append({
            "url": link_info['url'],
            "pwd": link_info['pwd'],
            'type': get_pan_type(link_info['url'])
        })
    return results


class KKKOB:

    @staticmethod
    def _isBadRequest(self, r, msg, key="code", value=200, message_key="message"):
        # 是否为不好的请求
        if r[key] != value:
            raise error.ServerError(msg + ":" + r[message_key])

    @staticmethod
    async def _request(endpoint: str, method: str, path: str, *args, **kwargs) -> dict:
        url = urljoin(endpoint, path)
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, *args, **kwargs) as response:
                return await response.json()

    @staticmethod
    async def getToken(endpoint: str, path: str):
        try:
            res = await KKKOB._request(
                endpoint, "GET", path,
                headers={"Content-Type": "application/json"},
                ssl=False
            )
            return res.get("token")
        except Exception as e:
            print(f"ERROR || 获取token失败 || {e}")
            return ""

    @staticmethod
    async def search(keyword: str, token: str, endpoint: str, path: str, **keywords) -> list[SearchResult]:
        payload = {
            "name": keyword,
            "token": token,
            'tabN': f"movie_{keywords.get('userid')}",
            'topNo': 10,
            'whr': f'question like "%{keyword}%"',
            'orderType': 'DESC',
            'keys': 'question,answer,isTop,id'
        }
        try:
            res = await KKKOB._request(
                endpoint, "POST", path,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=payload,
                ssl=False
            )
        except Exception as e:
            print(e)
            return []
        # 转换原始数据到实体模型
        raw_list = res.get('list', [])
        results = []
        try:
            for item in raw_list:
                parsed = parse_links(item.get('answer'))
                for parsed_item in parsed:
                    # 确保所有字段存在（使用dict.get处理缺失字段）
                    results.append(SearchResult(
                        id=item.get('id', ''),
                        name=item.get('question', ''),
                        url=parsed_item.get('url', ''),
                        type=parsed_item.get('type', ''),
                        pwd=parsed_item.get('pwd', ''),
                        fromSite=keywords.get('from_site', ''),
                        code="0"
                    ))
        except Exception as e:
            print(e)
        return results


