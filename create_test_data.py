# create_test_data.py
import os

# 创建 test_data 目录
os.makedirs("test_data", exist_ok=True)

print("📝 开始创建测试数据...")

# HR测试文档
hr_content = """员工手册 - 人力资源政策

1. 年假政策
   - 入职满1年：5天带薪年假
   - 入职满3年：10天带薪年假
   - 入职满5年：15天带薪年假
   - 未休年假可按日工资300%折算

2. 病假政策
   - 每月1天全薪病假
   - 需提供三甲医院证明
   - 连续病假超过3天需HR审批

3. 产假/陪产假
   - 女性员工：98天基础产假 + 30天奖励假
   - 男性员工：15天陪产假

4. 加班政策
   - 工作日加班：1.5倍工资
   - 周末加班：2倍工资
   - 法定节假日：3倍工资
   - 每月加班不超过36小时

5. 薪酬结构
   - 基本工资：岗位工资的70%
   - 绩效奖金：0-30%浮动
   - 餐补：500元/月
   - 交通补贴：300元/月
"""

with open("test_data/hr_policy.txt", "w", encoding="utf-8") as f:
    f.write(hr_content)
print("✅ 创建: test_data/hr_policy.txt")

# 财务测试文档
finance_content = """财务报销制度

差旅报销标准：
1. 交通费用
   - 高铁：二等座
   - 飞机：经济舱
   - 出租车：实报实销

2. 住宿标准
   - 一线城市：800元/晚
   - 二线城市：500元/晚
   - 其他城市：400元/晚

3. 餐补标准
   - 早餐：50元
   - 午餐：80元
   - 晚餐：80元

4. 采购流程
   - 5000元以下：部门经理审批
   - 5000-50000元：财务总监审批
   - 50000元以上：CEO审批

5. 发票要求
   - 增值税专用发票
   - 普通发票
   - 电子发票需打印
"""

with open("test_data/finance_policy.txt", "w", encoding="utf-8") as f:
    f.write(finance_content)
print("✅ 创建: test_data/finance_policy.txt")

# 法务测试文档
legal_content = """合同管理规范

1. 保密协议
   - 保密期限：合同终止后3年
   - 违约金：50-200万
   - 争议解决：甲方所在地法院

2. 劳动合同
   - 试用期：3-6个月
   - 竞业限制：6-12个月
   - 解约条件：提前30天通知
   - 经济补偿：N+1

3. 采购合同
   - 付款条款：30%预付款
   - 质保期：12个月
   - 违约责任：0.05%/天

4. 租赁合同
   - 租期：3-5年
   - 押金：2个月租金
   - 免租期：1-3个月
"""

with open("test_data/legal_policy.txt", "w", encoding="utf-8") as f:
    f.write(legal_content)
print("✅ 创建: test_data/legal_policy.txt")

print("\n🎉 所有测试数据创建完成！")
print("文件位置: ./test_data/")
print("文件列表:")
for f in os.listdir("test_data"):
    print(f"  - {f}")