
#调用函数是未传入参数会使用默认值
def response(data=None,message="seccess",code=0):
    # 如果数据为None，设置为空列表
    if data is None:
        data = []
    #Flask会自动将返回字典转换为JSON格式响应给客户端
    return {
        "code": code,        # 状态码
        "msg": message,      # 响应消息
        "data": data         # 响应数据
    }