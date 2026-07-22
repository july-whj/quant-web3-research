<script setup lang="ts">
import DefaultTheme from 'vitepress/theme'

import ReadingProgress from './ReadingProgress.vue'

const { Layout } = DefaultTheme
</script>

<template>
  <ReadingProgress />
  <Layout />
</template>
