# 吉林大学商学与管理学院 · 企业管理学硕机会雷达

一个专为吉林大学商学与管理学院 **企业管理专业学术型硕士** 建立的公开通知可视化网页。支持奖学金、学科竞赛、科研项目、学术活动、评奖评优和培养发展六类筛选；附截止倒计时、资格提示、来源状态与原文链接。

## 你的网页地址
完成 GitHub Pages 设置后：https://ricardoleirez70228-gif.github.io/jlu-opportunity-radar/

当前仓库：https://github.com/ricardoleirez70228-gif/jlu-opportunity-radar

## 首次上线：只需在 GitHub 网页操作
1. 打开 [仓库 Settings → Pages](https://github.com/ricardoleirez70228-gif/jlu-opportunity-radar/settings/pages)。
2. **Build and deployment** 下面选 `Deploy from a branch`，Branch 选 `main`，Folder 选 `/(root)`，点击 **Save**。
3. 打开 [Actions](https://github.com/ricardoleirez70228-gif/jlu-opportunity-radar/actions)。如需启用 Actions，按提示启用。
4. 进入 **每日更新吉林大学通知** 工作流，点击 **Run workflow** 手动进行首次抓取。初始数据为空，首次扫描成功后页面才有学校通知。
5. 打开 [Settings → Actions → General](https://github.com/ricardoleirez70228-gif/jlu-opportunity-radar/settings/actions) 确认 **Workflow permissions** 可使用 `Read and write permissions`（代码也声明了 `contents: write`）。否则机器人无法将扫描结果提交到 `data/notices.json`。

## 每天自动运行
`.github/workflows/daily.yml` 使用 `cron: '0 1 * * *'`，即每天北京时间09:00计划执行。GitHub 官方定时运行可能延迟，长时间不活跃的公开仓库计划任务可能被暂停。网页显示的是最近一次**成功保存**的结果，并不代表随时实时更新。

## 可选：自动邮件通知
在 Settings → Secrets and variables → Actions 配置 `SMTP_HOST`、`SMTP_USER`、`SMTP_PASSWORD`（邮箱的 SMTP 授权码）、`NOTICE_TO`，可选 `SMTP_PORT`（默认465）和 `NOTICE_FROM`。只在发现新增通知时尝试发送邮件。不要将口令写进公开仓库。

## 运行细节与限制
- 抓取范围：商学与管理学院的公开研究生通知、综合通知与学院首页，具体在 `sources.json`。
- 首次扫描前通知数量为0，**不会显示伪造的历史通知**。
- 学校 OA 登录后的资料不包含在内；不绕过登录、不抓取私密通知、不存放密码。
- 适用资格是规则提示，**需核实**不等于一定有资格；截止日期为启发式提取，原文为准。
- 由于校园网站 HTML 结构可能变化，部分通知可能漏抓或误分类；首次运行需检查 GitHub Actions 日志和网页“采集状态”。
- 若 GitHub Actions 显示 GitHub Pages 发布失败或数据不更新，需要查看工作流错误信息。
- 网页与代码完全公开，不要向仓库上传个人申请信息、学号或内部材料。

## 本地运行
```bash
pip install -r requirements.txt
python collector.py
python -m http.server 8000
```
然后在浏览器打开 http://localhost:8000。
