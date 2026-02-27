<script setup lang="ts">
import { computed } from 'vue';
import { useDark } from '@vueuse/core';
import JsonEditorVue from 'json-editor-vue';

interface Props {
    data: Record<string, any>;
}

const props = defineProps<Props>();
const emit = defineEmits<{
    (e: 'update:data', payload: Record<string, any>): void;
}>();

const isDark = useDark();

const model = computed({
    get: () => props.data,
    set: (val) => emit('update:data', val),
});
</script>

<template>
    <div class="h-full rounded-xl border shadow-xs overflow-hidden" :class="{ 'jse-theme-dark': isDark }">
        <JsonEditorVue v-model="model" class="h-full" />
    </div>
</template>
