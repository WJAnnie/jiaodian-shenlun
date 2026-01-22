"""
小红书焦点访谈申论内容生成器
- 获取央视焦点访谈最新一期
- AI改写成申论格式
- 微信推送
"""

import requests
import os
from datetime import datetime

# ============ 配置 ============
SERVERCHAN_KEY = os.environ.get("SERVERCHAN_KEY", "")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")


# ============ 焦点访谈爬取 ============
def fetch_jiaodian_fangtan():
    """获取央视焦点访谈最新一期"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        url = 'https://api.cntv.cn/NewVideo/getVideoListByColumn?id=TOPC1451558976694518&n=5&sort=desc&p=1&mode=0&serviceId=tvcctv'
        resp = requests.get(url, headers=headers, timeout=15)
        data = resp.json()

        if data.get('data') and data['data'].get('list'):
            video_list = data['data']['list']
            if video_list:
                latest = video_list[0]
                return {
                    'title': latest.get('title', ''),
                    'brief': latest.get('brief', ''),
                    'time': latest.get('time', ''),
                    'url': latest.get('url', ''),
                    'length': latest.get('length', '')
                }

        print("未获取到焦点访谈数据")
        return None

    except Exception as e:
        print(f"获取焦点访谈失败: {e}")
        return None


# ============ AI申论改写 ============
def rewrite_as_shenlun(title, content):
    """使用DeepSeek API改写成申论格式"""
    if not DEEPSEEK_API_KEY:
        return simple_rewrite(title, content)

    prompt = f"""请基于央视《焦点访谈》节目内容，提炼公务员面试高频考点素材，形成结构化积累内容，需满足以下要求：​
标题：精准概括核心话题，体现面试考点属性，15 字以内，可标注话题领域（如 “民生类”“治理类”）​
内容结构（每部分需简洁精炼，适配面试答题逻辑，便于口头表述）：​
【背景引入】：用 2-3 句话说明事件 / 话题的社会背景、政策语境，可关联近期国家大政方针（如 “在‘十四五’规划推进背景下”“围绕高质量发展要求”）​
【话题意义】：从政府职能、群众利益、社会发展等维度，用 2-3 句话阐述话题价值，可引用领导人相关讲话（如 “正如习近平总书记强调的‘以人民为中心的发展思想’”）或政策文件精神（如《政府工作报告》相关部署）​
【问题分析】：提炼 3-4 个核心问题，需结合实际案例（节目标注案例优先），体现问题的普遍性、关联性（如 “政策落地‘最后一公里’梗阻”“监管协同机制不健全”）​
【对策建议】：提出 3-4 条可操作对策，对应问题且符合政府工作逻辑（如 “强化部门联动，建立‘清单式’监管机制”“完善基层治理体系，推动资源下沉”），可参考已有政策实践经验​
【总结升华】：用 2-3 句话升华主题，关联国家发展战略（如 “推进国家治理体系和治理能力现代化”“实现共同富裕”），体现公务员视角的格局与担当​
附加要求：​
语言口语化适配面试表达，避免过于书面化表述​
每个部分标注 “答题可用角度”（如 “背景部分可用于综合分析题开篇”“对策部分可适配解决问题类题目”）​
结尾标注 “高频考点标签”（如 #面试综合分析 #民生治理 #政策落实）​
"""

    try:
        resp = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2048
            },
            timeout=90
        )
        result = resp.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"DeepSeek API调用失败: {e}")
        return simple_rewrite(title, content)


def simple_rewrite(title, content):
    """简单改写（无API时使用）"""
    return f"""【标题】{title}

【背景引入】
{content[:200]}

【问题分析】
详见原节目内容。

【话题意义】
（内容）+ 答题可用角度

【对策建议】
建议观看完整节目了解详情。

【总结升华】
关注时事，提升申论思维。

【话题标签】#申论 #焦点访谈 #时事热点 #公务员考试

​
"""


# ============ 微信推送 ============
def send_to_wechat(title, content):
    """通过Server酱推送到微信"""
    if not SERVERCHAN_KEY:
        print("未配置Server酱Key")
        return False

    url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
    data = {"title": title[:100], "desp": content}

    try:
        resp = requests.post(url, data=data, timeout=10)
        result = resp.json()
        if result.get('code') == 0:
            print("微信推送成功！")
            return True
        else:
            print(f"推送失败: {result}")
            return False
    except Exception as e:
        print(f"推送异常: {e}")
        return False


# ============ 主流程 ============
def main():
    print(f"=== 焦点访谈申论生成器 ===")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 1. 获取焦点访谈
    print("正在获取焦点访谈...")
    episode = fetch_jiaodian_fangtan()

    if not episode:
        send_to_wechat("获取失败", "今日未获取到焦点访谈")
        return

    print(f"获取到: {episode['title']}")
    print(f"播出时间: {episode['time']}")

    # 2. AI申论改写
    print("正在生成申论...")
    content = episode['brief'] or episode['title']
    shenlun = rewrite_as_shenlun(episode['title'], content)

    # 3. 组装推送内容
    today = datetime.now().strftime('%Y年%m月%d日')
    push_title = f"今日焦点访谈申论 - {today}"

    push_content = f"""## 今日小红书发布内容

---

{shenlun}

---

### 原节目信息
- **节目**：{episode['title']}
- **播出时间**：{episode['time']}
- **链接**：{episode.get('url', '')}
"""

    # 4. 推送
    print("正在推送...")
    send_to_wechat(push_title, push_content)
    print("\n=== 完成 ===")


if __name__ == "__main__":
    main()
