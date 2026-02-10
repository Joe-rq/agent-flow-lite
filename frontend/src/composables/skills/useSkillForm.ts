import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { API_BASE } from '@/utils/constants'
import type { SkillInput } from '@/types'

export function useSkillForm() {
  const route = useRoute()
  const router = useRouter()
  const skillNameParam = computed(() => route.params.name as string | undefined)
  const isNew = computed(() => !skillNameParam.value || skillNameParam.value === 'new')

  const skillName = ref('')
  const skillDescription = ref('')
  const skillInputs = ref<SkillInput[]>([])
  const skillPrompt = ref<string>('')
  const isSaving = ref(false)
  const showPreview = ref(true)
  const nameError = ref('')
  const promptError = ref('')

  const generatedMarkdown = computed(() => {
    const inputsYaml = skillInputs.value
      .filter((i) => i.name.trim())
      .map((i) => {
        let line = `  - name: ${i.name.trim()}`
        if (i.description) line += `\n    description: ${i.description}`
        if (i.required) line += '\n    required: true'
        if (i.default) line += `\n    default: ${i.default}`
        return line
      })
      .join('\n')

    let yaml = '---\n'
    yaml += `name: ${skillName.value || 'unnamed'}\n`
    if (skillDescription.value) yaml += `description: ${skillDescription.value}\n`
    if (inputsYaml) yaml += `inputs:\n${inputsYaml}\n`
    yaml += '---\n\n'
    yaml += skillPrompt.value || ''

    return yaml
  })

  const detectedVariables = computed(() => {
    const regex = /\{\{(\w+)\}\}/g
    const matches = new Set<string>()
    let match
    while ((match = regex.exec(skillPrompt.value)) !== null) {
      const variable = match[1]
      if (variable) {
        matches.add(variable)
      }
    }
    return Array.from(matches)
  })

  function isVariableDeclared(variable: string): boolean {
    return skillInputs.value.some((input) => input.name === variable)
  }

  function validateName() {
    nameError.value = ''
    const name = skillName.value.trim()
    if (!name) return

    if (!/^[a-z0-9-]+$/.test(name)) {
      nameError.value = '只能包含小写字母、数字、连字符'
      return
    }
    if (name.startsWith('-') || name.endsWith('-')) {
      nameError.value = '不能以连字符开头或结尾'
      return
    }
    if (name.includes('--')) {
      nameError.value = '不能有连续连字符'
      return
    }
  }

  function addInput() {
    skillInputs.value.push({
      name: '',
      description: '',
      required: false,
      default: '',
    })
  }

  function removeInput(index: number) {
    skillInputs.value.splice(index, 1)
  }

  function togglePreview() {
    showPreview.value = !showPreview.value
  }

  function goBack() {
    router.push('/skills')
  }

  async function loadSkill(name: string) {
    try {
      const response = await axios.get(`${API_BASE}/skills/${name}`)
      const skill = response.data

      skillName.value = skill.name || ''
      skillDescription.value = skill.description || ''
      skillInputs.value =
        skill.inputs?.map((i: any) => ({
          name: i.name || '',
          description: i.description || '',
          required: i.required || false,
          default: i.default || '',
        })) || []
      skillPrompt.value = skill.prompt || ''
    } catch (error) {
      console.error('加载技能失败:', error)
      alert('加载技能失败')
      router.push('/skills')
    }
  }

  async function saveSkill() {
    validateName()
    if (nameError.value) return

    if (!skillName.value.trim()) {
      nameError.value = '请输入技能名称'
      return
    }
    if (!skillPrompt.value.trim()) {
      promptError.value = '请输入提示词内容'
      return
    }

    isSaving.value = true
    promptError.value = ''

    try {
      const payload = {
        name: skillName.value.trim(),
        description: skillDescription.value.trim() || undefined,
        inputs: skillInputs.value
          .filter((i) => i.name.trim())
          .map((i) => ({
            name: i.name.trim(),
            description: i.description?.trim() || undefined,
            required: i.required || undefined,
            default: i.default?.trim() || undefined,
          })),
        prompt: skillPrompt.value,
        content: generatedMarkdown.value,
      }

      if (isNew.value) {
        await axios.post(`${API_BASE}/skills`, payload)
      } else {
        await axios.put(`${API_BASE}/skills/${skillNameParam.value}`, payload)
      }

      router.push('/skills')
    } catch (error: any) {
      console.error('保存技能失败:', error)
      promptError.value = error.response?.data?.detail || '保存失败，请重试'
    } finally {
      isSaving.value = false
    }
  }

  return {
    isNew,
    skillNameParam,
    skillName,
    skillDescription,
    skillInputs,
    skillPrompt,
    isSaving,
    showPreview,
    nameError,
    promptError,
    generatedMarkdown,
    detectedVariables,
    isVariableDeclared,
    validateName,
    addInput,
    removeInput,
    togglePreview,
    goBack,
    loadSkill,
    saveSkill,
  }
}
