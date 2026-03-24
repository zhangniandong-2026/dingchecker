# daily_check.py 工作流程详解

## 整体流程图

```
开始
  ↓
1. 连接Chrome调试端口 (CDP)
  ↓
2. 导航到主页面
  ↓
3. 【循环】处理每个业务单元 (共6个)
  ├─ 3.1 点击业务单元链接 (切换工作表)
  │   ├─ 在所有Frame中查找包含该单元名称的元素
  │   ├─ 找到后点击
  │   ├─ 等待5秒让页面加载
  │   └─ 验证表格是否加载完成
  ↓
  ├─ 3.2 提取当前工作表的数据
  │   ├─ 查找包含"提交日期"和"AI听记链接"的Frame
  │   ├─ 在表格中查找目标日期
  │   ├─ 找到日期后，定位同一行的链接
  │   ├─ 点击链接（会打开新标签页）
  │   ├─ 访问新打开的听记页面
  │   ├─ 提取听记内容
  │   └─ 关闭标签页
  ↓
  ├─ 3.3 返回主页面
  │   └─ 重新导航到主页面URL
  ↓
  └─ 重复3.1-3.3直到所有单元处理完
  ↓
4. 生成报告
  ├─ 统计各种状态
  ├─ 调用Gemini AI分析
  └─ 保存到文件
  ↓
结束
```

## 详细步骤解析

### 阶段1: 初始化连接

```python
# 第565-574行
browser = await p.chromium.connect_over_cdp("http://localhost:9222")
context = browser.contexts[0]
pages = context.pages
page = pages[0]  # 使用第一个标签页
```

**关键点**：
- 连接到已启动的Chrome调试端口
- 不需要重新登录，复用现有会话
- 使用第一个标签页作为主页面

### 阶段2: 导航到主页面

```python
# 第26-37行: navigate_to_main_page()
main_url = "https://alidocs.dingtalk.com/i/nodes/93NwLYZXWygvM0mMuk4O7vj7JkyEqBQm"
await page.goto(main_url, wait_until='domcontentloaded', timeout=60000)
await page.wait_for_timeout(3000)  # 等待3秒
```

**关键点**：
- 固定的主页面URL
- 等待DOM加载完成
- 额外等待3秒确保iframe也加载

### 阶段3: 点击业务单元 (核心逻辑)

#### 3.1 查找业务单元链接

```python
# 第66-77行: click_sheet_link()
frames = [page] + page.frames  # 主页面 + 所有iframe

for frame in frames:
    # 使用Playwright的text选择器
    element = await frame.query_selector(f'text="{sheet_name}"')
```

**查找策略**：
1. 遍历主页面和所有iframe
2. 使用`text="xxx"`选择器查找文本完全匹配的元素
3. 如果没找到，尝试滚动页面到底部再查找

**Frame结构说明**：
```
页面Frame结构:
├─ Frame 0: 主页面 (alidocs.dingtalk.com/i/nodes/...)
├─ Frame 1: 钉钉表格iframe (alidocs.dingtalk.com/iframe/notable)
│   └─ 包含左侧业务单元列表
├─ Frame 2: 文档编辑iframe (alidocs.dingtalk.com/note/edit)
│   └─ 也包含业务单元列表
└─ Frame 3: 统计/追踪iframe
```

#### 3.2 点击元素

```python
# 第112-127行
# 方法1: JavaScript点击（更稳定）
await frame.evaluate('''
    (text) => {
        const element = document.evaluate(
            `//*[text()="${text}"]`,  // XPath: 查找文本内容为指定值的任意元素
            document,
            null,
            XPathResult.FIRST_ORDERED_NODE_TYPE,
            null
        ).singleNodeValue;
        if (element) {
            element.click();
            return true;
        }
        return false;
    }
''', sheet_name)
```

**点击策略**：
1. 优先使用JavaScript的evaluate在浏览器上下文中点击
2. 如果失败，尝试Playwright的常规点击
3. 最多尝试3次

**为什么用JavaScript点击？**
- 绕过某些反自动化检测
- 可以点击被其他元素遮挡的元素
- 更稳定，不受页面滚动影响

#### 3.3 验证表格加载

```python
# 第152-160行
for _ in range(10):  # 最多等5秒
    frames_check = page.frames
    for f in frames_check:
        content = await f.content()
        if '提交日期' in content and 'AI听记链接' in content:
            found_table = True
            return True
    await page.wait_for_timeout(500)
```

**验证逻辑**：
- 检查是否有包含"提交日期"和"AI听记链接"的Frame
- 这两个关键词表示表格已加载
- 最多轮询10次（5秒）

### 阶段4: 提取数据 (最复杂的部分)

#### 4.1 查找表格Frame

```python
# 第156-180行: extract_content_for_current_sheet()
target_frame = None
for attempt in range(5):  # 最多尝试5次
    frames = page.frames
    for frame in frames:
        content = await frame.content()
        if '提交日期' in content and 'AI听记链接' in content:
            target_frame = frame
            break
```

#### 4.2 在表格中定位日期和链接

这是最核心的逻辑！使用JavaScript在浏览器中执行：

```python
# 第182-277行
result = await target_frame.evaluate('''
    (targetDate) => {
        // === 步骤1: 查找日期元素 ===
        function findDateElement() {
            const allElements = document.querySelectorAll('*');
            for (const elem of allElements) {
                // 只检查没有子元素的叶子节点（避免匹配父容器）
                if (elem.children.length === 0) {
                    const text = elem.textContent.trim();
                    if (text === targetDate) {  // 完全匹配
                        return elem;
                    }
                }
            }
            return null;
        }

        const dateElement = findDateElement();
        if (!dateElement) {
            return { success: false, reason: 'date-not-found' };
        }

        // === 步骤2: 滚动到日期元素 ===
        dateElement.scrollIntoView({ behavior: 'auto', block: 'center' });

        // === 步骤3: 获取日期元素的位置 ===
        const dateRect = dateElement.getBoundingClientRect();
        const dateY = dateRect.top + dateRect.height / 2;  // Y坐标中心点
        const dateRight = dateRect.right;                   // 右边界

        // === 步骤4: 查找右侧的链接元素 ===
        const allLinks = document.querySelectorAll('a, [role="link"]');
        const candidates = [];

        for (const link of allLinks) {
            const linkRect = link.getBoundingClientRect();
            const linkY = linkRect.top + linkRect.height / 2;  // 链接Y坐标
            const linkX = linkRect.left;                        // 链接X坐标
            const href = link.href || '';

            // 判断条件：
            // 1. Y坐标接近（同一行，误差<20像素）
            // 2. X坐标在日期右侧（linkX > dateRight - 100）
            // 3. 必须是shanji.dingtalk.com的链接
            if (Math.abs(linkY - dateY) < 20 &&
                linkX > dateRight - 100 &&
                href.includes('shanji.dingtalk.com')) {
                candidates.push({
                    element: link,
                    href: href,
                    distanceX: linkX - dateRight,
                    distanceY: Math.abs(linkY - dateY)
                });
            }
        }

        if (candidates.length === 0) {
            return { success: false, reason: 'link-not-found' };
        }

        // === 步骤5: 选择距离最近的链接 ===
        candidates.sort((a, b) => {
            // 计算欧氏距离
            const distA = Math.sqrt(a.distanceX ** 2 + a.distanceY ** 2);
            const distB = Math.sqrt(b.distanceX ** 2 + b.distanceY ** 2);
            return distA - distB;
        });

        // 返回最近的链接的XPath
        return {
            success: true,
            xpath: getXPath(candidates[0].element),
            linkText: candidates[0].text
        };
    }
''', target_date)
```

**定位策略详解**：

```
表格结构示例:
┌──────────┬──────────────┬──────────────────────────┐
│ 提交日期 │ 业务单元     │ AI听记链接               │
├──────────┼──────────────┼──────────────────────────┤
│2026-03-02│ 政府行业一组 │ https://shanji.dingtalk...│ ← 我们要找这个
└──────────┴──────────────┴──────────────────────────┘

定位逻辑:
1. 找到"2026-03-02"这个文本节点
2. 获取它的屏幕坐标 (X, Y)
3. 找所有链接 <a>
4. 筛选条件：
   - 链接的Y坐标 ≈ 日期的Y坐标 (同一行)
   - 链接的X坐标 > 日期的X坐标 (在右边)
   - 链接包含 shanji.dingtalk.com
5. 选择距离最近的那个
```

#### 4.3 点击链接并处理新标签页

```python
# 第283-342行
# 记录点击前的页面
initial_urls = set(pg.url for pg in page.context.pages)

# 点击链接
await target_frame.evaluate(f'''
    (xpath) => {{
        const element = document.evaluate(xpath, ...).singleNodeValue;
        if (element) {{
            element.click();
            return true;
        }}
    }}
''', result['xpath'])

# 等待新标签页打开（最多10秒）
for _ in range(20):
    await page.wait_for_timeout(500)

    # 检查是否有新页面打开
    for pg in page.context.pages:
        if pg.url not in initial_urls:
            new_page = pg

            # 如果是听记链接
            if 'shanji.dingtalk.com' in pg.url:
                link_url = pg.url.replace('/permission/', '/transcribes/')
                await pg.close()  # 关闭新标签页
                break
```

**新标签页处理**：
- 点击链接会打开新标签页
- 监测新打开的页面
- 提取URL后立即关闭
- 避免页面堆积

#### 4.4 访问听记页面提取内容

```python
# 第347-460行
content_page = await context.new_page()
await content_page.goto(link_url, wait_until='domcontentloaded', timeout=60000)
await content_page.wait_for_timeout(5000)

# 检查权限
page_text = await content_page.evaluate('() => document.body.innerText')
if '暂无权限' in page_text or '申请权限' in page_text:
    return "无权限", link_url

# 提取内容
content = await content_page.evaluate('''
    () => {
        // 移除导航、控制按钮等
        const toRemove = ['nav', 'header', 'footer', ...];
        toRemove.forEach(selector => {
            document.querySelectorAll(selector).forEach(e => e.remove());
        });

        return document.body.innerText.trim();
    }
''')

# 清理内容
lines = content.split('\n')
cleaned_lines = []
skip_keywords = ['AI 听记首页', 'AI 问答', '申请编辑', ...]

for line in lines:
    if not line.strip():
        continue
    if any(keyword in line for keyword in skip_keywords):
        continue
    cleaned_lines.append(line)

content = '\n'.join(cleaned_lines)
```

**内容清洗**：
1. 移除导航、按钮等UI元素
2. 过滤广告、提示性文字
3. 过滤时间戳、播放控制等
4. 提取"主题:"到"待办"之间的核心内容

#### 4.5 提取AI纪要摘要

```python
# 第423-452行
# 查找"主题:"到"待办"之间的内容
summary_match = re.search(r'主题:.*?(?=待办|还不错|AI问答|$)', content, re.DOTALL)
if summary_match:
    summary = summary_match.group(0).strip()

# 如果没找到，查找"会议纪要"
if not summary:
    summary_match = re.search(r'(会议纪要|会议概要|会议总结)[\s:：]*(.*?)(?=\n\n|$)', content, re.DOTALL)

# 都没找到，取前500字
if not summary:
    summary = content[:500] + ("..." if len(content) > 500 else "")

return summary, link_url
```

### 阶段5: 返回主页面

```python
# 第639-643行
main_url = "https://alidocs.dingtalk.com/i/nodes/93NwLYZXWygvM0mMuk4O7vj7JkyEqBQm"
await page.goto(main_url, wait_until='domcontentloaded', timeout=30000)
await page.wait_for_timeout(2000)
```

**为什么要返回？**
- 确保下一次点击从同一个起点开始
- 重置页面状态
- 避免Frame结构混乱

### 阶段6: 生成报告

```python
# 第465-539行: analyze_with_ai()
# 使用Gemini分析所有成功提取的内容
prompt = f"""
请分析以下业务单元的早会内容...

一、各业务单元工作摘要
二、需要公司统筹解决的问题
三、横向对比与优秀实践
四、各业务单元改进建议
五、整体改进建议
"""

response = model.generate_content(prompt)
```

## 关键设计亮点

### 1. 坐标定位法

不依赖表格结构，使用**屏幕坐标**定位：
- 找到日期的Y坐标
- 在相同Y坐标（±20px）范围内找链接
- 鲁棒性强，适应表格变化

### 2. 多重降级策略

```
点击方式：JavaScript点击 → Playwright点击 → 滚动后再试
查找方式：直接查找 → 滚动后查找 → 多Frame遍历
```

### 3. 新标签页监控

```
点击前记录所有页面URL
↓
点击
↓
轮询检测新页面
↓
提取URL后立即关闭
↓
避免标签页堆积
```

### 4. 内容清洗

智能过滤：
- UI元素（导航、按钮）
- 广告文字（"升级权益"、"限免"）
- 控制元素（播放器、时间轴）
- 提取核心会议内容

## 可能的问题点

### 问题1: 为什么有些单元找不到链接？

**原因**：
1. 表格中确实没有该日期的数据
2. 日期格式不匹配（如"03-02"vs"2026-03-02"）
3. 链接不是`<a>`标签或者href为空
4. 坐标偏移超过20像素（表格行高很大）

### 问题2: 新增的27个单元为什么没有数据？

**可能原因**：
1. 这些单元使用不同的表格结构
2. 这些单元确实没有提交听记
3. 这些单元在不同的位置（不在Frame 1/2）
4. 需要额外的权限才能访问

## 总结

**工作原理核心**：
1. 通过CDP复用已登录的Chrome
2. 使用文本匹配找到业务单元名称并点击
3. 使用坐标定位找到日期和链接的关系
4. 打开新标签页提取听记内容
5. AI分析生成管理报告

**成功关键**：
- 坐标定位而非依赖DOM结构
- 多重降级确保稳定性
- 新标签页管理避免混乱
- 内容清洗提取核心信息
