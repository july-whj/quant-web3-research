<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vitepress'

const route = useRoute()
const progress = ref(0)

function updateProgress() {
  const scrollable = document.documentElement.scrollHeight - window.innerHeight
  progress.value = scrollable > 0
    ? Math.min(100, Math.max(0, (window.scrollY / scrollable) * 100))
    : 0
}

onMounted(() => {
  updateProgress()
  window.addEventListener('scroll', updateProgress, { passive: true })
  window.addEventListener('resize', updateProgress)
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', updateProgress)
  window.removeEventListener('resize', updateProgress)
})

watch(
  () => route.path,
  async () => {
    await nextTick()
    updateProgress()
  },
)
</script>

<template>
  <div aria-hidden="true" class="reading-progress">
    <span :style="{ width: `${progress}%` }" />
  </div>
</template>
