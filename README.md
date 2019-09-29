# NAS 相关代码
## Email_RSS_Download
#### 背景
黑群, 不想洗白, 也不想把NAS直接暴露在公网上, 主要考虑安全, 防黑客. 但同时, 又想要把一些浏览到的资源使用Download Station下载到NAS中. 此前只能把资源收藏, 回家再下载.
#### 功能
使用人发送特定标题的邮件到邮箱, 内容为下载链接, 过段时间NAS的Download Station会自动下载
#### 实现
- Python读取邮件内容, 并将关键信息存储至MySQL表中
- PHP读取MySQL表中数据, 将资源生成RSS源
- 使用Download Station中自带的RSS订阅自动下载功能, 定时刷新PHP生成的RSS源, 实现自动下载
#### 配置步骤
- NAS中安装MySQL, PHP, Nginx/Apache
- MySQL创建schema, 导入表mail_rss.sql
- 将rss文件夹放置在Nginx Root path, 如web
#### 代码参考自
- https://blog.minirplus.com/6111/
- https://blog.csdn.net/sweeper_freedoman/article/details/88607210
- https://www.code-learner.com/python-use-pop3-to-read-email-example/

## IP_Email_Updater
#### 功能
系统发送家中路由器新获取到的IP到邮箱中
