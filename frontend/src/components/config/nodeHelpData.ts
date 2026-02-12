/**
 * 节点配置的字段提示和完整示例数据
 */

// ── 字段级 placeholder / hint ──────────────────────────────────

export interface FieldHint {
  placeholder?: string
  hint?: string
}

export type FieldHints = Record<string, Record<string, FieldHint>>

export const fieldHints: FieldHints = {
  start: {
    inputVariable: {
      placeholder: '例如: user_query',
      hint: '定义工作流的输入变量名，下游节点通过 {{start.output}} 引用',
    },
  },
  llm: {
    systemPrompt: {
      placeholder:
        '你是一个专业的文本分析助手。\n请根据用户输入 {{start.output}} 进行分析，给出结构化的结论。',
      hint: '使用 {{节点ID.output}} 引用上游节点的输出作为上下文',
    },
  },
  knowledge: {
    knowledgeBaseId: {
      hint: '选择要检索的知识库，查询内容来自上游节点的输出',
    },
  },
  end: {
    outputVariable: {
      placeholder: '例如: result',
      hint: '定义输出变量名，通常引用最后一个处理节点的输出',
    },
  },
  condition: {
    expression: {
      placeholder: "{{llm-1.output}}.includes('通过')",
      hint: '支持 JavaScript 表达式。用 {{节点ID.output}} 引用上游输出，返回 true/false 决定分支走向',
    },
  },
  skill: {
    skillName: {
      hint: '选择技能后，输入参数将自动从上游节点映射',
    },
  },
}

// ── 节点完整示例 ──────────────────────────────────────────────

export interface NodeExample {
  title: string
  description: string
  fields: Array<{ label: string; value: string }>
  tips: string[]
}

export const nodeExamples: Record<string, NodeExample> = {
  start: {
    title: '开始节点',
    description: '工作流的入口，接收用户输入并传递给下游节点。',
    fields: [{ label: '输入变量', value: 'user_query' }],
    tips: [
      '下游节点通过 {{start.output}} 获取用户输入',
      '每个工作流只能有一个开始节点',
    ],
  },
  llm: {
    title: 'LLM 节点',
    description: '调用大语言模型处理文本，可加载技能或自定义提示词。',
    fields: [
      {
        label: '系统提示词',
        value:
          '你是一个翻译助手。请将以下内容翻译为英文：\n{{start.output}}',
      },
      { label: '温度参数', value: '0.3（翻译/分析建议低温，创意写作建议高温）' },
    ],
    tips: [
      '用 {{节点ID.output}} 引用任意上游节点的输出',
      '加载技能后提示词和温度由技能配置接管',
      '多个 LLM 节点可串联，后者引用前者输出',
    ],
  },
  knowledge: {
    title: '知识库节点',
    description: '从知识库中检索与上游输出相关的文档片段，供下游 LLM 使用。',
    fields: [{ label: '知识库', value: '选择已创建的知识库' }],
    tips: [
      '检索查询来自上游节点的输出文本',
      '通常放在 LLM 节点之前，为其提供参考资料',
      '下游通过 {{knowledge-1.output}} 获取检索结果',
    ],
  },
  end: {
    title: '结束节点',
    description: '工作流的出口，收集最终结果并输出。',
    fields: [{ label: '输出变量', value: 'result' }],
    tips: [
      '每个工作流只能有一个结束节点',
      '最终输出取自最后一个连入节点的结果',
    ],
  },
  condition: {
    title: '条件节点',
    description: '根据表达式结果决定走 true 或 false 分支。',
    fields: [
      {
        label: '条件表达式',
        value: "{{llm-1.output}}.includes('通过')",
      },
    ],
    tips: [
      '表达式为 JavaScript 风格，返回 true/false',
      '用 {{节点ID.output}} 引用上游输出',
      '支持 .includes() 判断是否包含子串',
      '支持 contains 关键字：{{id.output}} contains "关键词"',
      '支持比较运算：===、!==、>、< 等',
      '支持逻辑运算：&&、||',
    ],
  },
  skill: {
    title: '技能节点',
    description: '调用已注册的技能，自动映射上游节点输出作为技能输入。',
    fields: [{ label: '技能', value: '从下拉列表选择' }],
    tips: [
      '技能的输入参数会自动从上游节点映射',
      '也可手动指定每个参数的来源节点',
      '下游通过 {{skill-1.output}} 获取技能执行结果',
    ],
  },
}
