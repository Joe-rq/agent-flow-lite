import { ref, type Ref } from 'vue'
import axios from 'axios'

interface SkillItem {
  name: string
  description: string
}

export function useSkillAutocomplete(inputRef: Ref<HTMLInputElement | null>) {
  const skills = ref<SkillItem[]>([])
  const inputMessage = ref('')
  const showSuggestions = ref(false)
  const filteredSkills = ref<SkillItem[]>([])
  const selectedSuggestionIndex = ref(0)

  async function loadSkills() {
    try {
      const response = await axios.get('/api/v1/skills')
      const items = response.data.skills || []
      skills.value = items.map((s: { name: string; description?: string }) => ({
        name: s.name,
        description: s.description || '',
      }))
    } catch (error) {
      console.error('\u52A0\u8F7D\u6280\u80FD\u5217\u8868\u5931\u8D25:', error)
      skills.value = []
    }
  }

  function onInputChange() {
    const text = inputMessage.value
    const atIndex = text.lastIndexOf('@')

    if (atIndex === -1) {
      showSuggestions.value = false
      return
    }

    const afterAt = text.slice(atIndex + 1)
    if (afterAt.includes(' ')) {
      showSuggestions.value = false
      return
    }

    const query = afterAt.toLowerCase()
    filteredSkills.value = skills.value.filter((skill) => skill.name.toLowerCase().includes(query))

    if (filteredSkills.value.length > 0) {
      showSuggestions.value = true
      selectedSuggestionIndex.value = 0
    } else {
      showSuggestions.value = false
    }
  }

  function onSuggestionDown() {
    if (!showSuggestions.value) return
    selectedSuggestionIndex.value =
      (selectedSuggestionIndex.value + 1) % filteredSkills.value.length
  }

  function onSuggestionUp() {
    if (!showSuggestions.value) return
    selectedSuggestionIndex.value =
      (selectedSuggestionIndex.value - 1 + filteredSkills.value.length) %
      filteredSkills.value.length
  }

  function closeSuggestions() {
    showSuggestions.value = false
  }

  function selectSuggestion(skill: SkillItem) {
    const text = inputMessage.value
    const atIndex = text.lastIndexOf('@')
    inputMessage.value = text.slice(0, atIndex) + '@' + skill.name + ' '
    showSuggestions.value = false
    inputRef.value?.focus()
  }

  return {
    skills,
    inputMessage,
    showSuggestions,
    filteredSkills,
    selectedSuggestionIndex,
    loadSkills,
    onInputChange,
    onSuggestionDown,
    onSuggestionUp,
    closeSuggestions,
    selectSuggestion,
  }
}
