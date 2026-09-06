import asyncio
from contextvars import ContextVar

# 创建上下文变量
# 参数1：上下文变量名称
# 参数2：默认值，未设置值时返回'None'
_req_id_context_var = ContextVar('request_id', default='None')

# 设置请求id
def set_req_id(rid: str):
    _req_id_context_var.set(rid)

# 获取请求id
def get_req_id()->str:
    return _req_id_context_var.get()

# 测试
if __name__ == '__main__':
    # 模拟两个异步请求：
    # 多个协程之间的数据互相隔离
    async def request1():
        print(f'请求1开始执行，req_id={get_req_id()}') # None
        set_req_id('111')
        print(f'请求1执行结束，req_id={get_req_id()}') # 111

    async def request2():
        print(f'请求2开始执行，req_id={get_req_id()}') # None
        set_req_id('222')
        print(f'请求2执行结束，req_id={get_req_id()}') # 222

    async def test():
        await asyncio.gather(request1(),request2())

    asyncio.run(test())