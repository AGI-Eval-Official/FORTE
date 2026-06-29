# 垂直行业专属字段扩展（Industry Extensions）

本文件定义各垂直行业在 M5 模式下的专属字段，在 M1/M2 通用字段基础上叠加使用。

---

## 教育行业

**识别信号：** 数据中出现学科、课程、学员、报名、学习时长、考试、成绩等字段

### 学员属性
| 标准字段 | 常见别名 | 说明 |
|---------|---------|------|
| student_type | 学员类型 | K12学生/成人学员/职场人/考研/考证 |
| grade_level | 年级/学段 | 小学/初中/高中/大学/成人 |
| subject_preference | 偏好学科 | 数学/语文/英语/编程等 |
| learning_goal | 学习目标 | 提分/兴趣/升学/职业发展/证书 |
| study_hours_per_week | 周学习时长 | 小时 |
| course_completion_rate | 课程完成率 | 0-1 |
| exam_score_trend | 成绩趋势 | 上升/稳定/下降 |
| parent_involvement | 家长参与度 | 高/中/低（K12场景） |
| decision_maker_edu | 决策人 | 学生本人/家长/单位 |
| budget_edu | 教育预算 | 年均投入金额 |
| learning_style | 学习方式偏好 | 直播/录播/1对1/小班/线下 |
| pain_point_edu | 教育痛点 | 效果不明显/时间不够/价格贵/师资差 |

---

## 医疗健康行业

**识别信号：** 数据中出现诊断、科室、就诊、病症、健康指标、药品、保险等字段

### 患者/用户属性
| 标准字段 | 常见别名 | 说明 |
|---------|---------|------|
| health_concern | 健康关注点 | 慢病管理/减重/心理健康/母婴/运动康复 |
| diagnosis | 诊断/病症 | 如高血压/糖尿病/焦虑症 |
| visit_frequency | 就诊频次 | 月均次数 |
| department | 科室偏好 | 内科/外科/皮肤科等 |
| insurance_type | 保险类型 | 医保/商业险/自费 |
| health_app_usage | 健康App使用 | 是否使用及频率 |
| chronic_disease | 慢性病标签 | 是/否 |
| health_literacy | 健康素养 | 高/中/低 |
| doctor_trust | 医生信任度 | 高/中/低 |
| telemedicine_adoption | 互联网医疗接受度 | 高/中/低 |
| medication_adherence | 用药依从性 | 高/中/低 |

---

## 汽车行业

**识别信号：** 数据中出现车型、购车、试驾、保养、里程、新能源等字段

### 车主/潜在购车者属性
| 标准字段 | 常见别名 | 说明 |
|---------|---------|------|
| car_ownership | 是否有车 | 有车/无车/换购 |
| car_type_preference | 偏好车型 | SUV/轿车/MPV/皮卡/新能源 |
| fuel_type | 能源类型偏好 | 燃油/纯电/混动/插混 |
| budget_car | 购车预算 | 万元区间 |
| purchase_intent | 购车意向 | 近期/半年内/一年内/观望 |
| test_drive_count | 试驾次数 | |
| mileage_per_year | 年均行驶里程 | 公里 |
| usage_scenario | 用车场景 | 通勤/家用/商务/越野 |
| brand_loyalty | 品牌忠诚度 | 高/中/低 |
| after_sales_concern | 售后关注点 | 保养/维修/保险/充电 |
| decision_factor_car | 购车决策因素 | 价格/品牌/续航/外观/空间/安全 |

---

## 房地产行业

**识别信号：** 数据中出现房型、面积、楼盘、看房、置业、租房等字段

### 购房/租房用户属性
| 标准字段 | 常见别名 | 说明 |
|---------|---------|------|
| property_purpose | 置业目的 | 自住/投资/改善/首套/换房 |
| property_type | 房产类型偏好 | 住宅/公寓/别墅/商铺/写字楼 |
| area_preference | 面积需求 | 平方米区间 |
| budget_property | 购房预算 | 万元区间 |
| location_preference | 区域偏好 | 学区/地铁/商圈/郊区 |
| viewing_count | 看房次数 | |
| purchase_timeline | 购房时间线 | 3个月内/半年/一年/观望 |
| family_structure | 家庭结构 | 单身/二人/三口/三代同堂 |
| mortgage_status | 贷款情况 | 全款/贷款/公积金 |
| concern_property | 置业关注点 | 价格/学区/交通/配套/品质 |

---

## 美妆个护行业

**识别信号：** 数据中出现肤质、成分、护肤、彩妆、美容、个护等字段

### 美妆用户属性
| 标准字段 | 常见别名 | 说明 |
|---------|---------|------|
| skin_type | 肤质 | 干性/油性/混合/敏感/中性 |
| skin_concern | 肌肤问题 | 痘痘/暗沉/干燥/毛孔/抗老 |
| beauty_category | 美妆品类偏好 | 护肤/彩妆/香水/个护/美发 |
| ingredient_awareness | 成分意识 | 高（看成分表）/中/低 |
| brand_tier | 品牌偏好层级 | 大众/轻奢/高端/国货/小众 |
| purchase_channel | 购买渠道 | 电商/专柜/直播/社群 |
| kol_influence | KOL影响度 | 高/中/低 |
| repurchase_driver | 复购驱动因素 | 效果/成分/价格/包装/品牌 |
| beauty_routine | 护肤步骤数 | 简单（1-3步）/标准（4-6步）/复杂（7步+） |

---

## 金融行业

**识别信号：** 数据中出现资产、理财、贷款、保险、投资、风险偏好等字段

### 金融用户属性
| 标准字段 | 常见别名 | 说明 |
|---------|---------|------|
| asset_level | 资产规模 | 万元区间 |
| risk_preference | 风险偏好 | 保守/稳健/积极/激进 |
| investment_type | 投资品类 | 存款/基金/股票/债券/保险/房产 |
| financial_goal | 理财目标 | 保值/增值/养老/子女教育/购房 |
| loan_status | 贷款情况 | 无贷款/房贷/车贷/消费贷/经营贷 |
| insurance_coverage | 保险配置 | 无/基础/完善 |
| financial_literacy | 金融素养 | 高/中/低 |
| digital_banking_usage | 数字银行使用 | 高频/低频/不使用 |

---

## 餐饮行业

**识别信号：** 数据中出现餐厅、外卖、堂食、菜品、口味、到店等字段

### 餐饮用户属性
| 标准字段 | 常见别名 | 说明 |
|---------|---------|------|
| dining_scenario | 用餐场景 | 外卖/堂食/自提/团餐 |
| cuisine_preference | 菜系偏好 | 川湘/粤菜/日料/西餐/快餐等 |
| meal_frequency | 外出就餐频次 | 周均次数 |
| avg_spend_per_meal | 人均消费 | 元 |
| group_size | 用餐人数 | 1人/2人/3-5人/6人+ |
| dietary_restriction | 饮食限制 | 素食/清真/无麸质/低卡 |
| delivery_platform | 外卖平台偏好 | 美团/饿了么/自营 |
| review_behavior | 评价行为 | 高频评价/偶尔/从不 |

---

## 旅游行业

**识别信号：** 数据中出现目的地、出行、酒店、机票、景区、旅游等字段

### 旅游用户属性
| 标准字段 | 常见别名 | 说明 |
|---------|---------|------|
| travel_frequency | 出行频次 | 年均次数 |
| travel_type | 旅行类型 | 休闲/商务/亲子/蜜月/探险/文化 |
| destination_preference | 目的地偏好 | 国内/出境/周边/热门/小众 |
| travel_budget | 旅行预算 | 人均元/次 |
| booking_lead_time | 提前预订时间 | 天数 |
| accommodation_preference | 住宿偏好 | 经济/舒适/豪华/民宿/露营 |
| travel_companion | 出行同伴 | 独行/情侣/家庭/朋友/团队 |
| travel_pain_point | 旅行痛点 | 攻略复杂/价格贵/人多/服务差 |

---

## 游戏行业

**识别信号：** 数据中出现游戏、充值、段位、玩法、在线时长等字段

### 游戏用户属性
| 标准字段 | 常见别名 | 说明 |
|---------|---------|------|
| game_genre | 游戏类型偏好 | MOBA/RPG/FPS/策略/休闲/卡牌 |
| play_frequency | 游戏频次 | 日均时长/周均天数 |
| player_level | 玩家等级/段位 | |
| recharge_amount | 充值金额 | 月均/累计 |
| recharge_frequency | 充值频次 | |
| social_play | 社交游戏行为 | 组队/公会/直播 |
| device_gaming | 游戏设备 | 手机/PC/主机 |
| churn_signal | 流失信号 | 登录减少/充值停止/社交退出 |

---

## 零售行业

**识别信号：** 数据中出现门店、到店、会员卡、积分、线下等字段

### 零售用户属性
| 标准字段 | 常见别名 | 说明 |
|---------|---------|------|
| store_visit_frequency | 到店频次 | 月均次数 |
| omnichannel_behavior | 全渠道行为 | 纯线上/纯线下/O2O |
| membership_level | 会员等级 | 普通/银卡/金卡/钻石 |
| points_balance | 积分余额 | |
| category_breadth | 品类广度 | 单品类/多品类 |
| basket_size | 购物篮大小 | 件数/金额 |
| promotion_channel | 促销触达渠道 | 短信/App推送/门店/社群 |
