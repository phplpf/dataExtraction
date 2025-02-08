import threading
import os
import json
import traceback
import sys
from openai import OpenAI
import re


def clean_and_replace(text):
    # 去除字符串开头和结尾的|符号
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]

    # 替换字符串中连续的||为|
    while "||" in text:
        text = text.replace("||", "|")

    # 将字符串中的|替换成"或者"
    text = text.replace("|", "或者")

    return text

def filter_operators(input_string):
    try:
        # 定义运算符列表
        operators = [
            r'\+', r'\-', r'\*', r'\/', r'%', r'=', r'<', r'>', r'&', r'\|', r'\^', r'~', r'!',
            r'==', r'!=', r'>=', r'<=', r'<<', r'>>', r'\/\/=', r'\*\*=', r'and', r'or', r'not',
            r'is', r'is not', r'in', r'not in'
        ]
        # 将运算符列表拼接成一个正则表达式模式
        pattern = r'(' + r'|'.join(operators) + r')'
        # 使用 re.sub() 函数将匹配的运算符替换为空字符串
        filtered_string = re.sub(pattern, '', input_string)
        return filtered_string
    except Exception as e:
        print(e)
        return input_string

class TestLLMEngine:
    def __init__(self) -> None:
        pass


    def parse_llm_info(self,text):
        # text = "{提示词｜抽取结果｜结果所在的短句}"
        # 正则表达式模式，匹配 { 和 } 中间的三部分内容
        pattern = r'\{([^｜]+)｜([^｜]+)｜([^}]+)\}'
        # 使用 re.match() 函数匹配模式
        match = re.match(pattern, text)
        result = None
        if match:
            part1 = match.group(1)  # 提取第一部分内容
            part2 = match.group(2)  # 提取第二部分内容
            part3 = match.group(3)  # 提取第三部分内容
            if part1 == '提示词':
                return None
            if part2 == 'None':
                part2 = ""
            if part3 == 'None':
                part3 = ""
            result = {"prompt":part1,"extract_content":part2,"origin_text":part3}
            return result
        else:
            print("匹配失败")
            return result

    def get_prompt(self,voice_prompt, origin_text):
        #获取提示词
        # 实体抽取 
        prompt = (
            "我希望你充当文本抽取工具。您的角色是在给定的原文中，根据提示词，抽取想要的信息，并给出抽取内容在原文中的位置。"
            "原文内容我会用原文:开头来提醒，提示词我会用提示词:来提醒。对于每一个抽取的结果，请用一行来表示，一行内依次展示以下信息："
            "提示词、抽取结果、结果所在的短句。格式如：{提示词｜抽取结果｜结果所在的短句}。"
            "如果某一个提示词没有任何结果请返回{提示词｜None｜None}。 抽取结果必须来自于原文，结果所在的短句必须来自于原文，"
            "抽取的内容要在结果所在的短句里出现。如果抽取的内容位置不同也算是不同的抽取内容。同一个提示词抽出多个结果，请用不同的行展示。"
            "尽量抽取更多的内容，不要回答除了抽取内容以外的信息。\n"
            "原文: %s \n"
            "提示词: %s"
        )
        return prompt % (origin_text, voice_prompt)
    

    def procsss_data(self,template_info):
        #数据预处理
        entites_list = [] #实体抽取
        entites = template_info["entities_info"]
        if type(entites) == str:
            entites = eval(entites)
        for entity in entites:
            entity_prompt_config = entity["prompt_config"]
            entity_name = entity["entity_name"]
            entity_attr_id = entity["entity_attr_id"]
            exrtact_data = {"entity_name":entity_name,"entity_key":entity["entity_key"],"entity_attr_id":entity_attr_id,"prompt_configs":[entity_prompt_config]}
            entites_list.append(exrtact_data)
   
        rules_list = [] #规则抽取
        rules = template_info["rule_info"]
      
        if rules is not None:
            if type(rules) == str:
                rules = eval(rules)
            for rule in rules:
                rules_list.append(rule)
                
        return entites_list,rules_list  


    #模型预测
    def predict(self,template_info,data):
         #数据预处理
            entites_list,rules_list = self.procsss_data(template_info)
            #提示词+抽取规则
            #实体抽取
            origin_data = {}
            for entites in entites_list:
                all_response = []
                prompt = entites["prompt_configs"][0]
                # print("实体抽取prompt:",prompt)

                prompt_filter = clean_and_replace(prompt)
                prompt_filter = filter_operators(prompt_filter)
                origin_data["entity_name"] = entites["entity_name"]
                origin_data["response"] = []
                page = 1
                for origin_text in data:
                    prompt_sentence = self.get_prompt(prompt_filter, origin_text)
                    response = self.ask_llm(prompt_sentence)
                    if response is None:
                        page += 1
                        continue
                    response_list = response.split("\n")
                    for item in response_list:
                        result = self.parse_llm_info(item)
                        if result:
                            print("*"*20)
                            print("%s:%s"%(result["prompt"],result["extract_content"]))

    def ask_llm(self,prompt):
        try:
            client = OpenAI(
                api_key = "EMPTY",
                base_url = "http://192.168.0.12:8000/v1",
            )
            completion = client.chat.completions.create(
                model = "Qwen2.5-32B-Instruct-GPTQ-Int8",
                messages=[
                    {'role': 'user', 'content': prompt}
                ],
                extra_body={
                    "top_k": 1,
                }
            )
            model_response = completion.dict()
            return model_response["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"get_response Error: {e}")


    def run(self,template_info,data):
        self.predict(template_info,data)


if __name__ == "__main__":

    template_info = {
        "id": 43,
        "name": "监测报告-测试",
        "description": "测试",
        "workflow_id": 1,
        "entities_info": [
            {
                "entity_key": "1",
                "entity_name": "监测机构名称",
                "prompt_config": "监测单位名称",
                "entity_attr_id": 1
            },
            {
                "entity_key": "2",
                "entity_name": "委托单位名称",
                "prompt_config": "委托单位名称",
                "entity_attr_id": 1
            },
            {
                "entity_key": "3",
                "entity_name": "监测报告编号",
                "prompt_config": "监测报告编号",
                "entity_attr_id": 1
            },
            {
                "entity_key": "4",
                "entity_name": "监测地点",
                "prompt_config": "基站地址|建设地点|监测地点",
                "entity_attr_id": 1
            },
            {
                "entity_key": "5",
                "entity_name": "站址经度和纬度",
                "prompt_config": "经纬度",
                "entity_attr_id": 2
            },
            {
                "entity_key": "6",
                "entity_name": "铁塔站址编码",
                "prompt_config": "铁塔站址编码",
                "entity_attr_id": 1
            },
            {
                "entity_key": "7",
                "entity_name": "网络制式",
                "prompt_config": "网络制式|网络系统",
                "entity_attr_id": 1
            },
            {
                "entity_key": "8",
                "entity_name": "频率范围",
                "prompt_config": "发射频率范围",
                "entity_attr_id": 2
            },
            {
                "entity_key": "9",
                "entity_name": "天线数量",
                "prompt_config": "天线数量",
                "entity_attr_id": 2
            },
            {
                "entity_key": "12",
                "entity_name": "监测日期",
                "prompt_config": "监测日期",
                "entity_attr_id": 1
            },
            {
                "entity_key": "13",
                "entity_name": "监测时间",
                "prompt_config": "监测时间",
                "entity_attr_id": 1
            },
            {
                "entity_key": "14",
                "entity_name": "天气情况",
                "prompt_config": "天气",
                "entity_attr_id": 1
            },
            {
                "entity_key": "15",
                "entity_name": "环境温度",
                "prompt_config": "环境温度",
                "entity_attr_id": 1
            },
            {
                "entity_key": "16",
                "entity_name": "相对湿度",
                "prompt_config": "相对湿度",
                "entity_attr_id": 1
            },
            {
                "entity_key": "17",
                "entity_name": "监测所依据的技术文件名称及代号",
                "prompt_config": "监测所依据的技术文件名称及代号",
                "entity_attr_id": 1
            },
            {
                "entity_key": "18",
                "entity_name": "监测使用辐射检测仪器的设备名称、型号规格及编号",
                "prompt_config": "仪器名称|型号规格|探头型号|探头编号|生产厂家",
                "entity_attr_id": 1
            },
            {
                "entity_key": "19",
                "entity_name": "辐射检测仪器的频率范围、量程、校准证书及有效期",
                "prompt_config": "辐射检测仪器的频率范围、量程、校准证书及有效期",
                "entity_attr_id": 1
            }
        ],
        "rule_info": None,
        "enable": True,
        "last_update_time": 1733730691,
        "delete_status": True,
        "create_time": 1733730691,
        "user": "disifanshi"
    }
    data = [
        "<html><body><table><tr><td rowspan=1 colspan=1>监测项目</td><td rowspan=1 colspan=3>泉州惠安崇武莲西搬迁-HLH</td></tr><tr><td rowspan=1 colspan=1>委托单位</td><td rowspan=1 colspan=3>中国电信股份有限公司泉州分公司<br>中国移动通信集团福建有限公司泉州分公司</td></tr><tr><td rowspan=1 colspan=1>委托单位地址</td><td rowspan=1 colspan=3>电信：泉州市丰泽区刺桐南路西侧电信大楼<br>移动：泉州市丰泽区安吉南路567号</td></tr><tr><td rowspan=1 colspan=1>监测类别</td><td rowspan=1 colspan=1>委托监测</td><td rowspan=1 colspan=1>监测方式</td><td rowspan=1 colspan=1>现场监测</td></tr><tr><td rowspan=1 colspan=1>委托日期</td><td rowspan=1 colspan=3>2024年11月</td></tr><tr><td rowspan=1 colspan=1>监测日期</td><td rowspan=1 colspan=1>2024年11月05日</td><td rowspan=1 colspan=1>监测时间</td><td rowspan=1 colspan=1>12:37~13:26</td></tr><tr><td rowspan=1 colspan=1>监测的<br>环境条件</td><td rowspan=1 colspan=3>天气：晴；环境温度：27.6℃；相对湿度：67.3%</td></tr><tr><td rowspan=1 colspan=1>监测所依据的技术<br>文件名称及代号</td><td rowspan=1 colspan=3>HJ1151-2020《5G移动通信基站电磁辐射环境监测方法（试行）》</td></tr><tr><td rowspan=1 colspan=1>判定依据</td><td rowspan=1 colspan=3>1、GB8702-2014《电磁环境控制限值》<br>2、HJ/T10.3-1996《辐射环境保护管理导则-电磁辐射环境影响评价方<br>法与标准》</td></tr><tr><td rowspan=1 colspan=1>使用的主要仪器设<br>备名称、型号规格<br>及编号</td><td rowspan=1 colspan=3>1、仪器名称：选频式电磁辐射监测仪；<br>2、型号规格：OS-4P；设备编号：S-1482<br>3、探头型号规格：SRF-06三轴全向电场天线；探头编号：A-1557<br>4、生产厂家：北京森馥科技股份有限公司</td></tr><tr><td rowspan=1 colspan=1>仪器主要<br>技术指标</td><td rowspan=1 colspan=3>频率响应范围：30MHz~6GHz<br>量程范围：1mV/m~300V/m（即2.65×10-7μW/cm²~2.38×104μW/cm²)<br>计量校准证书号：2024F33-10-5094021003<br>校准单位：上海市计量测试研究院<br>校准有效期：2024-02-19~2025-02-18</td></tr><tr><td rowspan=1 colspan=1>监<br>测<br>结<br>论</td><td rowspan=1 colspan=3>说明：由监测结果可知，泉州惠安崇武莲西搬迁-HLH基站各检测点位<br>的功率密度满足《电磁环境控制限值》（GB8702-2014）和《辐射环境<br>保护管理导则-电磁辐射环境影响评价方法与标准》》（HJ/T10.3-1996)<br>的限值要求。<br>签发日期：20W年1月7日</td></tr><tr><td rowspan=1 colspan=1>备注</td><td rowspan=1 colspan=3></td></tr><tr><td rowspan=1 colspan=4></td></tr></table></body></html> "
    ]
    llm = TestLLMEngine()


    llm.run(template_info,data)