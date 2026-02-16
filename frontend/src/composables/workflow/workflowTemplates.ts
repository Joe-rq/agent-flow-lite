import type { ExportPayload } from './useWorkflowCrud'

export const kbQaTemplate: ExportPayload = {
  version: 1,
  workflow: {
    name: '知识库问答',
    description: '基于知识库的问答工作流模板，先检索相关知识再生成回答',
    graph_data: {
      nodes: [
        {
          id: 'start-1',
          type: 'start',
          position: { x: 100, y: 100 },
          label: '开始',
          data: {
            inputVariable: 'query'
          }
        },
        {
          id: 'knowledge-1',
          type: 'knowledge',
          position: { x: 100, y: 250 },
          label: '检索知识库',
          data: {
            knowledgeBaseId: ''
          }
        },
        {
          id: 'llm-1',
          type: 'llm',
          position: { x: 100, y: 400 },
          label: '生成回答',
          data: {
            systemPrompt: '你是一个基于知识库的问答助手。请根据提供的知识库上下文回答用户问题。\n\n用户问题：{{query}}\n\n注意：你收到的用户消息内容包含了从知识库检索到的相关内容，请基于这些内容生成回答。如果知识库中没有相关信息，请明确告知用户。',
            temperature: 0.7
          }
        },
        {
          id: 'end-1',
          type: 'end',
          position: { x: 100, y: 550 },
          label: '结束',
          data: {}
        }
      ],
      edges: [
        {
          id: 'edge-1',
          source: 'start-1',
          target: 'knowledge-1',
          sourceHandle: null,
          targetHandle: null
        },
        {
          id: 'edge-2',
          source: 'knowledge-1',
          target: 'llm-1',
          sourceHandle: null,
          targetHandle: null
        },
        {
          id: 'edge-3',
          source: 'llm-1',
          target: 'end-1',
          sourceHandle: null,
          targetHandle: null
        }
      ]
    }
  }
}

export const sopAssistantTemplate: ExportPayload = {
  version: 1,
  workflow: {
    name: 'SOP 助手',
    description: '标准作业程序助手，帮助用户按照既定流程执行任务',
    graph_data: {
      nodes: [
        {
          id: 'start-1',
          type: 'start',
          position: { x: 100, y: 100 },
          label: '开始',
          data: {
            inputVariable: 'task'
          }
        },
        {
          id: 'llm-1',
          type: 'llm',
          position: { x: 100, y: 300 },
          label: 'SOP 分析',
          data: {
            systemPrompt: `你是一个 SOP（标准作业程序）专家助手。

你的职责是：
1. 分析用户提供的任务
2. 按照标准流程逐步指导用户完成
3. 检查每个步骤的执行情况
4. 在必要时提供纠正建议

用户任务：{{task}}

请保持专业、清晰、有条理的沟通风格。`,
            temperature: 0.3
          }
        },
        {
          id: 'end-1',
          type: 'end',
          position: { x: 100, y: 500 },
          label: '结束',
          data: {}
        }
      ],
      edges: [
        {
          id: 'edge-1',
          source: 'start-1',
          target: 'llm-1',
          sourceHandle: null,
          targetHandle: null
        },
        {
          id: 'edge-2',
          source: 'llm-1',
          target: 'end-1',
          sourceHandle: null,
          targetHandle: null
        }
      ]
    }
  }
}

export type TemplateSlug = 'kb_qa' | 'sop_assistant'

export function getTemplateBySlug(slug: TemplateSlug): ExportPayload {
  switch (slug) {
    case 'kb_qa':
      return kbQaTemplate
    case 'sop_assistant':
      return sopAssistantTemplate
    default:
      throw new Error(`Unknown template slug: ${slug}`)
  }
}
