# 数据模式字段定义（Data Schema）

本文件定义10大数据模式的标准字段，用于将用户提供的原始数据映射到统一维度。

---

## M1 通用基础数据模式

适用场景：中小商家、基础运营、行政岗位

### 基础属性字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| user_id | 用户ID、UID、客户编号 | string | 唯一标识 |
| age | 年龄、age | int | 实际年龄或年龄段 |
| age_group | 年龄段、年龄区间 | string | 如"25-34岁" |
| gender | 性别、sex | string | 男/女/未知 |
| city | 城市、所在城市 | string | |
| region | 地区、省份、大区 | string | |
| city_tier | 城市等级、城市线级 | string | 一线/新一线/二线/三线及以下 |
| register_date | 注册时间、注册日期、首次登录 | date | |
| register_days | 注册天数、账龄 | int | 距今天数 |
| device | 设备类型、终端 | string | iOS/Android/PC/小程序 |
| channel | 来源渠道、获客渠道 | string | 自然流量/付费/社交/转介绍 |

### 消费行为字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| total_amount | 累计消费金额、总消费、GMV | float | |
| avg_order_value | 客单价、平均订单金额、AOV | float | |
| order_count | 订单数、购买次数、消费次数 | int | |
| last_order_date | 最近消费时间、最近下单、Recency | date | |
| recency_days | 距上次消费天数、R值 | int | |
| purchase_frequency | 购买频次、消费频率、F值 | float | 月均/年均 |
| category_preference | 偏好品类、常购品类 | string | |
| coupon_usage_rate | 优惠券使用率、券敏感度 | float | |
| refund_rate | 退款率、退货率 | float | |

### 行为数据字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| page_views | 页面浏览量、PV | int | |
| session_count | 访问次数、会话数 | int | |
| avg_session_duration | 平均停留时长、人均时长 | float | 秒/分钟 |
| last_active_date | 最近活跃时间、最近登录 | date | |
| active_days_30d | 近30天活跃天数 | int | |
| cart_add_rate | 加购率 | float | |
| wishlist_count | 收藏数 | int | |

---

## M2 精细化运营数据模式

包含 M1 全部字段，额外增加：

### 兴趣与偏好字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| interest_tags | 兴趣标签、偏好标签、用户标签 | array | 如["美妆","健身","母婴"] |
| content_preference | 内容偏好、感兴趣内容 | string | |
| brand_preference | 品牌偏好、偏好品牌 | array | |
| price_sensitivity | 价格敏感度、价格区间偏好 | string | 高/中/低 |
| promotion_response | 促销响应率、活动参与率 | float | |

### 生命周期字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| lifecycle_stage | 生命周期阶段、用户阶段 | string | 新用户/成长期/成熟期/沉睡/流失 |
| rfm_label | RFM标签、用户价值标签 | string | 高价值/潜力/一般/流失风险 |
| churn_risk | 流失风险、流失概率 | string/float | 高/中/低 或 0-1 |
| retention_days | 留存天数 | int | |
| cohort | 用户队列、入组时间 | string | 如"2024Q1" |

### 体验与满意度字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| nps_score | NPS分数、净推荐值 | int | -100 到 100 |
| satisfaction_score | 满意度评分、CSAT | float | 1-5 或 1-10 |
| complaint_count | 投诉次数 | int | |
| review_count | 评价数、评论数 | int | |
| avg_review_score | 平均评分 | float | |

### 互动行为字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| activity_participation | 活动参与次数、活动参与率 | int/float | |
| referral_count | 推荐人数、邀请人数 | int | |
| community_posts | 社区发帖数 | int | |
| customer_service_contacts | 客服联系次数 | int | |

---

## M3 ToB专属数据模式

### 企业属性字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| company_name | 企业名称、公司名 | string | |
| company_size | 企业规模、员工人数 | string | 1-50/51-200/201-1000/1000+ |
| industry | 行业、所属行业 | string | |
| company_type | 企业类型 | string | 国企/民企/外企/上市公司/初创 |
| annual_revenue | 年营收、营业额 | string/float | |
| founded_year | 成立年份 | int | |
| location | 总部城市、注册地 | string | |
| listed | 是否上市 | bool | |

### 采购与合作字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| contract_value | 合同金额、采购金额 | float | |
| contract_count | 合同数量、采购次数 | int | |
| avg_contract_value | 平均合同金额 | float | |
| last_purchase_date | 最近采购时间 | date | |
| purchase_cycle | 采购周期、续约周期 | string | 月/季/年 |
| product_modules | 购买模块、使用产品 | array | |
| contract_stage | 合同阶段、商机阶段 | string | 线索/意向/谈判/签约/续约/流失 |
| renewal_rate | 续约率 | float | |

### 组织架构字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| decision_maker | 决策人、拍板人 | string | 职位/角色 |
| influencer | 影响人、推荐人 | string | |
| end_user | 使用者、执行人 | string | |
| contact_department | 对接部门 | string | |
| contact_level | 对接层级 | string | C级/VP/总监/经理/专员 |

### 业务诉求字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| pain_points | 痛点、业务问题 | array | |
| business_goals | 业务目标、采购目的 | array | |
| current_solution | 现有方案、竞品使用 | string | |
| budget_range | 预算范围 | string | |
| decision_timeline | 决策周期、采购时间线 | string | |

---

## M4 内容流量数据模式

### 内容消费字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| content_type_preference | 内容类型偏好 | array | 视频/图文/直播/音频 |
| avg_watch_duration | 平均观看时长 | float | 秒/分钟 |
| completion_rate | 完播率、完读率 | float | 0-1 |
| content_category | 内容品类偏好 | array | |
| active_time_slot | 活跃时段 | string | 早/午/晚/深夜 |
| platform | 平台来源 | string | 抖音/微信/微博/B站等 |

### 互动行为字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| like_rate | 点赞率 | float | |
| comment_rate | 评论率 | float | |
| share_rate | 分享率、转发率 | float | |
| save_rate | 收藏率 | float | |
| follow_count | 关注数 | int | |
| unfollow_rate | 取关率 | float | |

### 创作与传播字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| is_creator | 是否创作者 | bool | |
| post_count | 发帖数、发布内容数 | int | |
| follower_count | 粉丝数 | int | |
| avg_content_reach | 平均触达量 | float | |
| viral_coefficient | 传播系数、K因子 | float | |
| monetization_type | 变现方式 | string | 广告/带货/打赏/付费内容 |

---

## M5 垂直行业数据模式

M5 在 M1/M2 基础上扩展行业专属字段。详细字段定义见 `industry-extensions.md`。

**支持行业：** 教育、医疗健康、汽车、房地产、美妆个护、金融、餐饮、旅游、游戏、零售

---

## M6 产品体验数据模式

### 功能使用字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| feature_usage | 功能使用记录、功能点击 | object | {功能名: 使用次数} |
| core_feature_adoption | 核心功能采用率 | float | |
| feature_depth | 功能使用深度 | string | 浅层/中层/深度用户 |
| onboarding_completion | 新手引导完成率 | float | |
| user_journey | 用户路径、操作流程 | array | |

### 体验异常字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| error_count | 报错次数、异常次数 | int | |
| crash_count | 崩溃次数 | int | |
| error_types | 错误类型 | array | |
| drop_off_point | 流失节点、退出页面 | string | |
| task_completion_rate | 任务完成率 | float | |
| support_ticket_count | 工单数、客服咨询次数 | int | |

### 需求意向字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| feature_requests | 功能需求、需求反馈 | array | |
| feature_votes | 需求投票数 | int | |
| upgrade_intent | 升级意向 | string | 高/中/低 |
| willingness_to_pay | 付费意愿 | string/float | |
| usability_score | 易用性评分 | float | 1-5 |
| usefulness_score | 有用性评分 | float | 1-5 |

---

## M7 社交关系数据模式

### 社交网络字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| friend_count | 好友数、关注数、粉丝数 | int | |
| mutual_friend_count | 共同好友数 | int | |
| social_graph_density | 关系链密度 | float | 0-1，衡量关系网络紧密程度 |
| network_centrality | 网络中心度 | string | 核心节点/普通节点/边缘节点 |
| social_influence_score | 社交影响力评分 | float | |
| contact_frequency | 联系频率 | string | 高频/中频/低频 |

### 社群与私域字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| group_count | 加入群组数、社群数 | int | |
| group_activity_rate | 群活跃率、社群参与度 | float | |
| group_role | 群角色 | string | 群主/管理员/活跃成员/潜水 |
| private_domain_source | 私域来源 | string | 公众号/小程序/企微/社群 |
| wechat_interaction_count | 微信互动次数 | int | |
| mini_program_visits | 小程序访问次数 | int | |
| follow_official_account | 是否关注公众号 | bool | |

### 裂变与传播字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| invite_count | 邀请人数、拉新人数 | int | |
| invite_success_rate | 邀请成功率 | float | |
| referral_gmv | 推荐带来的GMV | float | |
| share_count | 分享次数 | int | |
| viral_path | 裂变路径 | string | 直接邀请/群裂变/朋友圈 |
| k_factor | K因子、病毒系数 | float | 每个用户平均带来的新用户数 |

---

## M8 线下门店数据模式

### 到店行为字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| store_visit_count | 到店次数、进店次数 | int | |
| store_visit_frequency | 到店频次 | string | 月均次数 |
| last_visit_date | 最近到店时间 | date | |
| avg_dwell_time | 平均停留时长 | float | 分钟 |
| peak_visit_time | 高峰到店时段 | string | 早/午/晚/周末 |
| visit_day_of_week | 偏好到店星期 | string | |

### 地理与门店字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| preferred_store | 常去门店、偏好门店 | string | 门店编号/名称 |
| store_distance | 距门店距离 | float | 公里 |
| geo_fence_trigger | 地理围栏触发 | bool | 是否进入围栏区域 |
| multi_store_visits | 多门店访问 | bool | 是否跨门店消费 |
| home_location | 居住地 | string | |
| work_location | 工作地 | string | |

### 线下消费字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| offline_total_amount | 线下累计消费 | float | |
| offline_avg_order | 线下客单价 | float | |
| offline_category | 线下消费品类 | string | |
| coupon_redemption_rate | 优惠券核销率 | float | |
| scan_code_count | 扫码次数 | int | 扫码点餐/扫码支付 |
| membership_card_usage | 会员卡使用率 | float | |

### O2O融合字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| online_to_offline_rate | 线上引流到店率 | float | |
| offline_to_online_rate | 到店后线上转化率 | float | |
| omnichannel_behavior | 全渠道行为类型 | string | 纯线下/纯线上/O2O融合 |
| app_checkin_count | App签到次数 | int | |

---

## M9 订阅会员数据模式

### 订阅状态字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| subscription_plan | 订阅计划、套餐名称 | string | 基础版/专业版/企业版 |
| subscription_tier | 会员等级、订阅层级 | string | |
| subscription_start_date | 订阅开始时间 | date | |
| subscription_duration | 订阅时长 | int | 月数 |
| billing_cycle | 计费周期 | string | 月付/季付/年付 |
| subscription_price | 订阅价格 | float | |
| trial_status | 试用状态 | string | 试用中/已转付费/已流失 |
| auto_renew | 是否自动续费 | bool | |

### 权益使用字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| benefit_usage_rate | 权益使用率 | float | 已使用权益/总权益 |
| core_benefit_adoption | 核心权益采用率 | float | |
| unused_benefits | 未使用权益 | array | |
| seat_utilization | 席位使用率 | float | 企业版适用 |
| api_call_volume | API调用量 | int | SaaS适用 |
| storage_usage | 存储使用量 | float | |
| feature_unlock_count | 解锁功能数 | int | |

### 续费与流失字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| renewal_date | 续费日期、到期时间 | date | |
| renewal_count | 续费次数 | int | |
| churn_date | 取消时间、流失时间 | date | |
| cancellation_reason | 取消原因 | string | |
| downgrade_count | 降级次数 | int | |
| upgrade_count | 升级次数 | int | |
| ltv | 生命周期价值、LTV | float | |
| mrr | 月经常性收入、MRR | float | |
| expansion_revenue | 扩展收入 | float | 升级/增购带来的额外收入 |

---

## M10 用户反馈舆情数据模式

### 评论与评价字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| review_text | 评论内容、评价文本 | string | |
| review_score | 评分、星级 | float | 1-5 |
| review_date | 评论时间 | date | |
| review_platform | 评论来源平台 | string | App Store/微博/大众点评等 |
| review_length | 评论字数 | int | |
| helpful_votes | 有用数、点赞数 | int | |

### 情感分析字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| sentiment_label | 情感标签、情感倾向 | string | 正面/中性/负面 |
| sentiment_score | 情感得分 | float | -1 到 1 |
| emotion_type | 情绪类型 | string | 满意/愤怒/失望/惊喜/困惑 |
| topic_tags | 话题标签、主题分类 | array | 如["物流","客服","质量"] |
| keyword_frequency | 关键词频率 | object | {关键词: 出现次数} |
| pain_point_category | 痛点分类 | string | 产品/服务/价格/物流/体验 |

### 投诉与工单字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| ticket_count | 工单数、投诉次数 | int | |
| ticket_type | 工单类型、投诉类型 | string | 退款/质量/物流/功能/账号 |
| ticket_resolution_time | 解决时长 | float | 小时 |
| ticket_resolution_rate | 解决率 | float | |
| repeat_complaint_rate | 重复投诉率 | float | |
| escalation_rate | 升级率 | float | 投诉升级到更高层级的比例 |
| csat_after_service | 售后满意度 | float | 1-5 |

### 舆情监测字段

| 标准字段 | 常见别名 | 类型 | 说明 |
|---------|---------|------|------|
| mention_count | 提及次数、曝光量 | int | |
| mention_trend | 提及趋势 | string | 上升/稳定/下降 |
| crisis_signal | 危机信号 | bool | 是否出现舆情风险词 |
| competitor_mention | 竞品提及 | array | 同时提及的竞品名称 |
| nps_verbatim | NPS开放评论 | string | NPS调研中的文字反馈 |
