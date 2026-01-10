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

    prompt = f"""请根据以下央视《焦点访谈》节目内容，写一篇申论风格的文章，适合发布在小红书上。

要求：
1. 标题：简洁有力，体现申论特点，可加emoji，20字以内
2. 正文结构：
   - 【背景引入】简述事件/话题背景（2-3句）
   - 【问题分析】分析存在的问题或现象（3-4点）
   - 【对策建议】提出解决思路或建议（3-4点）
   - 【总结升华】升华主题，展望未来（2-3句）
3. 语言风格：
   - 用词规范、逻辑清晰
   - 适当引用政策文件或领导讲话
   - 体现公务员思维和格局
4. 结尾加上3-5个话题标签

节目标题：{title}
节目内容：{content}

请输出：
【标题】...

【背景引入】
...

【问题分析】
...

【对策建议】
...

【总结升华】
...

【话题标签】#申论 #焦点访谈 ...
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

【对策建议】
建议观看完整节目了解详情。

【总结升华】
关注时事，提升申论思维。

【话题标签】#申论 #焦点访谈 #时事热点 #公务员考试"""


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
