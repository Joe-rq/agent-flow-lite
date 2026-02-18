<template>
  <div class="skills-view">
    <div class="page-header">
      <h1>技能管理</h1>
      <button class="btn-primary" @click="createNewSkill">
        + 新建技能
      </button>
    </div>

    <!-- 技能列表 -->
    <div class="skills-list">
      <div
        v-for="skill in skills"
        :key="skill.name"
        class="skill-card"
        @click="editSkill(skill.name)"
      >
        <div class="skill-card-header">
          <h3 class="skill-name">{{ skill.name }}</h3>
        </div>
        <p class="skill-description">{{ skill.description || '暂无描述' }}</p>
        <div class="skill-inputs" v-if="skill.inputs && skill.inputs.length > 0">
          <span class="inputs-label">输入参数:</span>
          <span
            v-for="input in skill.inputs.slice(0, 3)"
            :key="input.name"
            class="input-tag"
            :class="{ required: input.required }"
          >
            {{ input.name }}
          </span>
          <span v-if="skill.inputs.length > 3" class="input-tag more">
            +{{ skill.inputs.length - 3 }}
          </span>
        </div>
        <div class="skill-card-footer">
          <span class="skill-updated">更新于 {{ formatDate(skill.updatedAt) }}</span>
          <div class="skill-actions">
            <button
              class="btn-run"
              @click.stop="runner.openRunModal(skill)"
            >
              运行
            </button>
            <button
              class="btn-delete-skill"
              @click.stop="deleteSkill(skill.name)"
            >
              删除
            </button>
          </div>
        </div>
      </div>

      <div v-if="skills.length === 0" class="empty-state">
        <p>暂无技能</p>
        <button class="btn-primary" @click="createNewSkill">
          创建第一个技能
        </button>
      </div>
    </div>

    <!-- 运行技能对话框 -->
    <SkillRunDialog
      :showRunModal="runner.showRunModal.value"
      :runningSkill="runner.runningSkill.value"
      :runInputs="runner.runInputs.value"
      :runOutput="runner.runOutput.value"
      :isRunning="runner.isRunning.value"
      :currentThought="runner.currentThought.value"
      @close="runner.closeRunModal()"
      @run="runner.runSkill()"
      @update:run-inputs="runner.runInputs.value = $event"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { formatDate } from '@/utils/format'
import { API_BASE } from '@/utils/constants'
import { useSkillRunner } from '@/composables/skills/useSkillRunner'
import { useToast } from '@/composables/useToast'
import { useConfirmDialog } from '@/composables/useConfirmDialog'
import SkillRunDialog from '@/components/skills/SkillRunDialog.vue'
import type { Skill, SkillApiItem } from '@/types'

const router = useRouter()
const skills = ref<Skill[]>([])
const runner = useSkillRunner()
const { showToast } = useToast()
const { confirmDialog } = useConfirmDialog()

async function loadSkills() {
  try {
    const response = await axios.get(`${API_BASE}/skills`)
    const rawSkills: SkillApiItem[] = Array.isArray(response?.data)
      ? response.data
      : response?.data?.skills || response?.data?.items || []

    skills.value = rawSkills.map(skill => ({
      name: skill.name,
      description: skill.description,
      inputs: skill.inputs || [],
      updatedAt: skill.updated_at || skill.updatedAt || '',
    }))
  } catch (error) {
    console.error('加载技能列表失败:', error)
    showToast('加载技能列表失败')
  }
}

function createNewSkill() {
  router.push('/skills/new')
}

function editSkill(name: string) {
  router.push(`/skills/${name}`)
}

async function deleteSkill(name: string) {
  if (!(await confirmDialog(`确定要删除技能「${name}」吗？`))) return

  try {
    await axios.delete(`${API_BASE}/skills/${name}`)
    skills.value = skills.value.filter(s => s.name !== name)
  } catch (error) {
    console.error('删除技能失败:', error)
    const err = error as { response?: { data?: { detail?: string } } }
    showToast(err.response?.data?.detail || '删除技能失败')
  }
}

onMounted(() => {
  loadSkills()
})
</script>

<style scoped src="./SkillsView.css"></style>
