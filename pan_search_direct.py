import sys
import os
# 获取当前脚本所在目录（项目根目录）
project_root = os.path.dirname(os.path.abspath(__file__))
# 将项目根目录和 OnePanSearchApi 目录添加到 Python 搜索路径
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, "OnePanSearchApi")) 

import asyncio
import argparse
from typing import Optional, List
from pydantic import BaseModel

# 导入 main.py 中的核心组件
from OnePanSearchApi.main import SourceQuery, search_pan  # 直接复用现有逻辑

def parse_arguments():
    """解析命令行参数，与 API 接口参数保持一致"""
    parser = argparse.ArgumentParser(description='直接调用网盘搜索核心逻辑')
    parser.add_argument('--keyword', required=True, help='搜索关键词（必填）')
    parser.add_argument('--fromSite', help='来源站点，多个用逗号分隔（如：kk大厅,夸克）')
    parser.add_argument('--type', help='网盘类型，多个用逗号分隔（如：夸克网盘,百度网盘）')
    parser.add_argument('--page', type=int, default=1, help='页码，默认1')
    parser.add_argument('--pageSize', type=int, default=10, help='每页数量，默认10')
    parser.add_argument('--output', choices=['json', 'simple'], default='simple', 
                      help='输出格式（json/simple）')
    return parser.parse_args()

def format_simple_output(result: dict):
    """以简洁格式打印结果"""
    print(f"🔍 搜索关键词: {result['data'][0]['name'] if result['data'] else '无结果'}")
    print(f"📊 搜索结果: 共 {result['total']} 条，当前第 {result['page']}/{(result['total'] + result['pageSize'] - 1) // result['pageSize']} 页")
    print("-" * 80)
    
    for item in result['data']:
        print(f"[{item['code']}] {item['name']}")
        print(f"类型: {item['type']}")
        print(f"来源: {item['fromSite']}")
        print(f"链接: {item['url']}")
        if item['pwd']:
            print(f"提取码: {item['pwd']}")
        print("-" * 80)

async def main():
    # 解析命令行参数
    args = parse_arguments()
    
    # 构造 SourceQuery 对象（复用 API 中的参数解析逻辑）
    # 模拟 FastAPI 的 Query 参数解析过程
    source = SourceQuery.from_query(
        keyword=args.keyword,
        fromSite=args.fromSite,
        type=args.type,
        page=args.page,
        pageSize=args.pageSize
    )
    
    # 直接调用搜索核心逻辑（跳过 HTTP 层）
    print(f"正在搜索: {args.keyword}（来源: {args.fromSite or '全部'}, 类型: {args.type or '全部'}）...")
    result = await search_pan(source)  # 直接调用 main.py 中的 search_pan 函数
    
    # 补充分页信息（原接口返回结果中没有 page 和 pageSize，手动添加）
    result['page'] = args.page
    result['pageSize'] = args.pageSize
    
    # 输出结果
    if args.output == 'json':
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        format_simple_output(result)

if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())