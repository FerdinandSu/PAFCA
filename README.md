# PAFCA：门禁申请代理

基于Github Action的每日自动门禁申请，开箱即用。并提供邮件/微信提醒功能

感谢 @billchenchina 提供的统一身份认证插件[hitutil](https://github.com/billchenchina/hitutil)
                          及[原始版本](https://github.com/billchenchina/cxsq)。

[手动疫情上报系统入口](https://xg.hit.edu.cn/zhxy-xgzs/xg_mobile/xs/yqxx)

## 使用方法

- fork仓库
- 设置仓库的action secret，添加用户名hit_username、密码hit_password和可选的通知用Secrets
- 开启Action（详细步骤见后文）
- 每天早上8:00（UTC 00:00)可自动定时运行。申请**第二天**的门禁。你可以根据后文内容，设置邮件或微信提醒

设置仓库的Secrets：

| Name          | Value                                |
| ------------- | ------------------------------------ |
| HIT_USERNAME      | 统一身份认证账号 （学号）        |
| HIT_PASSWORD      | 统一身份认证密码                 |
| API_KEY       | 可选。server酱推送的sckey, 或发送电子邮件的密码/Key      |
| MAIL_TO       | 可选。电子邮件信息，格式"服务器[:端口[U]]:用户名(邮箱)"                   |

[![添加Action Secret的步骤](https://z3.ax1x.com/2021/04/27/g9Q1s0.png)](https://imgtu.com/i/g9Q1s0)

Fork的仓库会默认关闭action的执行，需要在仓库设置里打开：

[![启用Action的步骤1](https://z3.ax1x.com/2021/04/27/g9QMzn.png)](https://imgtu.com/i/g9QMzn)
[![启用Action的步骤2](https://z3.ax1x.com/2021/04/27/g9QlMq.png)](https://imgtu.com/i/g9QlMq)

以上步骤都完工后可以手动运行一次工作流，验证是否可以正常工作

[![手动运行](https://z3.ax1x.com/2021/04/27/g9QKRs.png)](https://imgtu.com/i/g9QKRs)

## 上报情况提醒

为了防止脚本突然挂了等情况发生，可设置电子邮件或微信提醒。

### 电子邮件提醒

1. 设定Secrets的`MAIL_TO`字段，格式`服务器[:端口[U]]:用户名(邮箱)`，服务器域名和地址可参考[这篇博客](https://blog.csdn.net/zhangge3663/article/details/104293945/)。如果不设置端口，则尝试使用默认。如果加'U'则不使用TLS。
2. 设定Secrets的`API_KEY`为你的邮箱账户密码，或是SMTP对应的API_KEY。

### 微信提醒

微信提醒基于[Server酱](http://sc.ftqq.com/)，但是**貌似这个服务对免费用户有限额**，所以为什么不用电邮提醒呢？

在Server酱中弄到API_KEY后填写到Secrets的`API_KEY`即可。

## 如果脚本挂了，或者你想修改一下上报地点什么的

`post_data.jsonc`里边是上报数据包的原始数据，修改之即可。
