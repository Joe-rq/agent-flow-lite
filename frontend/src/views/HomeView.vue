<script setup lang="ts">
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'

interface Feature {
  title: string
  description: string
  route: string
  icon: 'workflow' | 'knowledge' | 'chat'
}

const features: Feature[] = [
  {
    title: 'Workflow',
    description: 'Visual workflow editor with drag-and-drop nodes for building AI pipelines',
    route: '/workflow',
    icon: 'workflow',
  },
  {
    title: 'Knowledge Base',
    description: 'Manage documents and build RAG pipelines for semantic retrieval',
    route: '/knowledge',
    icon: 'knowledge',
  },
  {
    title: 'Chat',
    description: 'Interactive chat terminal with streaming responses and citation tracing',
    route: '/chat',
    icon: 'chat',
  },
]
</script>

<template>
  <main class="home">
    <section class="hero">
      <div class="hero__content">
        <h1 class="hero__title">Agent Flow</h1>
        <p class="hero__tagline">Build, manage, and deploy intelligent AI workflows</p>
        <div class="hero__actions">
          <Button variant="primary" size="lg" @click="$router.push('/workflow')">
            Create Workflow
          </Button>
          <Button variant="secondary" size="lg" @click="$router.push('/knowledge')">
            Upload Documents
          </Button>
        </div>
      </div>
    </section>

    <section class="features">
      <Card
        v-for="feature in features"
        :key="feature.route"
        class="feature-card"
        padding="lg"
        hover
        @click="$router.push(feature.route)"
      >
        <div class="feature-card__icon" :class="`feature-card__icon--${feature.icon}`">
          <svg v-if="feature.icon === 'workflow'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7" rx="1" />
            <rect x="14" y="3" width="7" height="7" rx="1" />
            <rect x="3" y="14" width="7" height="7" rx="1" />
            <rect x="14" y="14" width="7" height="7" rx="1" />
            <path d="M10 3v4M17 3v4M10 17v4M17 17v4" />
          </svg>
          <svg v-else-if="feature.icon === 'knowledge'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            <line x1="12" y1="6" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <svg v-else-if="feature.icon === 'chat'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        </div>
        <h3 class="feature-card__title">{{ feature.title }}</h3>
        <p class="feature-card__description">{{ feature.description }}</p>
      </Card>
    </section>
  </main>
</template>

<style scoped>
.home {
  min-height: 100%;
  padding: var(--space-3xl) var(--space-xl);
  display: flex;
  flex-direction: column;
  gap: var(--space-3xl);
}

.hero {
  text-align: center;
  padding: var(--space-3xl) 0;
}

.hero__content {
  max-width: 600px;
  margin: 0 auto;
}

.hero__title {
  font-size: var(--text-3xl);
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: var(--space-md);
  background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero__tagline {
  font-size: var(--text-lg);
  color: var(--text-secondary);
  margin-bottom: var(--space-xl);
}

.hero__actions {
  display: flex;
  gap: var(--space-md);
  justify-content: center;
  flex-wrap: wrap;
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-lg);
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.feature-card {
  cursor: pointer;
}

.feature-card__icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-lg);
}

.feature-card__icon svg {
  width: 24px;
  height: 24px;
}

.feature-card__icon--workflow {
  background: var(--accent-cyan-soft);
  color: var(--accent-cyan);
}

.feature-card__icon--knowledge {
  background: var(--accent-purple-soft);
  color: var(--accent-purple);
}

.feature-card__icon--chat {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.feature-card__title {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-sm);
}

.feature-card__description {
  font-size: var(--text-base);
  color: var(--text-secondary);
  line-height: 1.6;
}

@media (max-width: 640px) {
  .home {
    padding: var(--space-xl) var(--space-md);
  }

  .hero {
    padding: var(--space-xl) 0;
  }

  .hero__title {
    font-size: var(--text-2xl);
  }

  .hero__tagline {
    font-size: var(--text-base);
  }

  .hero__actions {
    flex-direction: column;
    align-items: stretch;
  }

  .features {
    grid-template-columns: 1fr;
  }
}
</style>
