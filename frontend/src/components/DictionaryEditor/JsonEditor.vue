<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { Search, AlertCircle } from 'lucide-vue-next';
import Input from '@/components/ui/input/Input.vue';

interface Props {
  data: Record<string, any>;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  (e: 'update:data', payload: Record<string, any>): void
}>();

const jsonText = ref('');
const searchText = ref('');
const parseError = ref('');
const highlightedJson = ref('');

// Helper functions defined first
const escapeRegExp = (str: string) => {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
};

const updateHighlightedJson = () => {
  if (!searchText.value.trim()) {
    highlightedJson.value = jsonText.value;
    return;
  }

  const search = searchText.value;
  const regex = new RegExp(`(${escapeRegExp(search)})`, 'gi');
  highlightedJson.value = jsonText.value.replace(regex, '<mark class="bg-yellow-300 dark:bg-yellow-600">$1</mark>');
};

const validateJson = () => {
  try {
    const parsed = JSON.parse(jsonText.value);
    parseError.value = '';
    emit('update:data', parsed);
  } catch (e: any) {
    parseError.value = e.message;
  }
};

// Count matches
const matchCount = computed(() => {
  if (!searchText.value.trim()) return 0;
  const regex = new RegExp(escapeRegExp(searchText.value), 'gi');
  const matches = jsonText.value.match(regex);
  return matches ? matches.length : 0;
});

// Watchers that use the above functions
// Initialize JSON text from props
watch(() => props.data, (newVal) => {
  jsonText.value = JSON.stringify(newVal, null, 2);
  updateHighlightedJson();
}, { immediate: true, deep: true });

// Watch for search text changes
watch(searchText, () => {
  updateHighlightedJson();
});

// Watch for JSON text changes to validate
watch(jsonText, () => {
  validateJson();
  updateHighlightedJson();
});

</script>

<template>
  <div class="flex flex-col h-full bg-card rounded-xl border shadow-sm overflow-hidden">
    <!-- Header with search -->
    <div class="p-4 border-b bg-muted/20">
      <div class="flex items-center gap-3">
        <div class="relative flex-1">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input 
            v-model="searchText" 
            placeholder="Search in JSON..." 
            class="pl-9"
          />
        </div>
        <div v-if="matchCount > 0" class="text-sm text-muted-foreground whitespace-nowrap">
          {{ matchCount }} match{{ matchCount !== 1 ? 'es' : '' }}
        </div>
      </div>
      
      <!-- Error message -->
      <div v-if="parseError" class="mt-3 flex items-start gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
        <AlertCircle class="h-4 w-4 text-destructive mt-0.5 flex-shrink-0" />
        <div class="flex-1">
          <p class="text-sm font-medium text-destructive">Invalid JSON</p>
          <p class="text-xs text-destructive/80 mt-1">{{ parseError }}</p>
        </div>
      </div>
    </div>

    <!-- JSON Editor -->
    <div class="flex-1 overflow-auto p-0 relative">
      <textarea
        v-model="jsonText"
        class="w-full h-full p-4 font-mono text-sm bg-transparent border-0 outline-none resize-none"
        :class="{ 'text-destructive': parseError }"
        spellcheck="false"
      />
      
      <!-- Highlighted overlay (for search highlighting) -->
      <div 
        v-if="searchText.trim() && !parseError"
        class="absolute inset-0 p-4 font-mono text-sm pointer-events-none whitespace-pre-wrap break-words overflow-auto"
        style="color: transparent;"
        v-html="highlightedJson"
      />
    </div>

    <!-- Footer info -->
    <div class="px-4 py-2 border-t bg-muted/10 text-xs text-muted-foreground flex items-center justify-between">
      <div>Direct JSON editing - Changes auto-save when valid</div>
      <div v-if="!parseError" class="text-green-600 dark:text-green-400">✓ Valid JSON</div>
    </div>
  </div>
</template>

<style scoped>
textarea {
  tab-size: 2;
  -moz-tab-size: 2;
}

:deep(mark) {
  background-color: rgb(253 224 71);
  border-radius: 0.125rem;
  padding-left: 0.125rem;
  padding-right: 0.125rem;
}

:deep(.dark mark) {
  background-color: rgb(202 138 4);
}
</style>

