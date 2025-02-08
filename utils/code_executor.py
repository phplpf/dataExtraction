import requests
import textwrap  # 用于移除多余缩进
import json

class CodeExecutor:
    BASE_URL = "http://localhost:8194/v1/sandbox/run"
    HEADERS = {
        "X-Api-Key": "dify-sandbox",
        "Authorization": "Bearer dify-sandbox",
        "Content-Type": "application/json"
    }

    @staticmethod
    def execute(code: str, language: str = "python3", enable_network: bool = True, preload: str = "preload"):
        """
        发送代码到沙盒并执行。

        :param code: 待执行的代码字符串
        :param language: 编程语言（默认：python3）
        :param enable_network: 是否启用网络支持（默认：True）
        :param preload: 预加载配置（默认："preload"）
        :return: 执行结果或错误信息
        """
        try:
            payload = {
                "language": language,
                "preload": preload,
                "enable_network": enable_network,
                "code": code
            }

            response = requests.post(CodeExecutor.BASE_URL, json=payload, headers=CodeExecutor.HEADERS)
            
            if response.status_code == 200:
                result = response.json()
                result = json.loads(result)
                return result["data"]
            else:
                raise Exception(f"Request failed with status code {response.status_code}: {response.text}")
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def build_code(main_code: str, data: dict,type:int):
        """
        构建完整的代码字符串，将数据动态插入代码中。

        :param main_code: 主逻辑代码字符串
        :param data: 要传递给代码的外部输入数据
        :type: 1,前处理代码。 2,后处理代码
        :return: 拼接完成的代码字符串
        """
        try:
            if type == 1:
                external_input = f"""
data = {data}
result = data_pre_process(data)
print(result)
"""
            elif type == 2:
                external_input = f"""
data = {data}
result = data_post_process(data)
print(result)
"""   

            return textwrap.dedent(main_code) + "\n" + external_input
        except Exception as e:
            return None

if __name__ == "__main__":
    # 定义主逻辑代码
    # main_code = """
    # def data_pre_process(input_data):
    #     '''
    #     对输入数据进行预处理 
    #     '''
    #     output_result = []

    #     for item in input_data:
    #         item["name"] = item["name"].replace(" ", "_")
    #         item["name"] = item["name"].replace("-", "_")
    #         output_result.append(item)
    #     return output_result
    # """

    main_code = "\n    def data_pre_process(input_data):\n        '''\n        对输入数据进行预处理 \n        '''\n        output_result = input_data\n\n        #此处填写前处理逻辑 ...\n\n        return output_result\n    "

    # 外部传入的数据
    data = [
        {"name": "hello world", "age": 20},
        {"name": "hello-dify-sandbox", "age": 20}
    ]

    # 构建完整代码
    full_code = CodeExecutor.build_code(main_code, data,1)

    # 执行代码并获取结果
    result = CodeExecutor.execute(full_code)
    print(result)
