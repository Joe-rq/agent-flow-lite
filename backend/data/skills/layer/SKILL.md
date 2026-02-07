---
description: 为用户提供初步的法律问题分析和合规性提示，不构成正式法律意见。
name: layer
user_id: '1'
---

input_schema:
  - name: case_type
    type: string
    description: 案件类型，例如 劳动纠纷 合同纠纷 婚姻家庭
  - name: case_description
    type: string
    description: 用户对案件事实的描述
  - name: user_goal
    type: string
    description: 用户希望达到的目的，例如 维权 起草协议 风险评估

output_schema:
  - name: legal_analysis
    type: string
    description: 基于已知事实的初步法律分析
  - name: possible_actions
    type: list[string]
    description: 可行的下一步行动建议
  - name: risk_reminder
    type: string
    description: 主要法律风险与注意事项
  - name: disclaimer
    type: string
    description: 法律免责声明

execution_steps:
  - step: 理解案件类型与事实
  - step: 识别核心法律关系与争议点
  - step: 给出通用法律分析与方向性建议
  - step: 提醒证据保存与时效风险
  - step: 输出免责声明

example_output:
  legal_analysis: >
    根据你提供的信息，该情况可能涉及劳动合同解除的合法性问题。
    用人单位在未提前通知且无正当理由的情况下解除合同，
    可能存在违法解除的风险。
  possible_actions:
    - 收集并保存劳动合同与工资记录
    - 核实解除理由是否符合法律规定
    - 咨询当地劳动仲裁机构
  risk_reminder: >
    劳动仲裁通常存在申请时效限制，请注意时间节点。
  disclaimer: >
    本回复仅为一般性法律信息，不构成正式法律意见，
    具体情况建议咨询执业律师。