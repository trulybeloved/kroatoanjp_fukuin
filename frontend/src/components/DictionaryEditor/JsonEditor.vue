<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { Search, AlertCircle } from 'lucide-vue-next';
import Input from '@/components/ui/input/Input.vue';

interface Props {
    data: Record<string, any>;
}

const props = defineProps<Props>();
const emit = defineEmits<{
    (e: 'update:data', payload: Record<string, any>): void;
}>();

const jsonText = ref('');
const searchText = ref('');
const parseError = ref('');

const escapeRegExp = (str: string) =>
    str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const highlightedJson = computed(() => {
    if (!searchText.value.trim()) return jsonText.value;
    const regex = new RegExp(`(${escapeRegExp(searchText.value)})`, 'gi');
    return jsonText.value.replace(regex, '<mark>$1</mark>');
});

const matchCount = computed(() => {
    if (!searchText.value.trim()) return 0;
    const regex = new RegExp(escapeRegExp(searchText.value), 'gi');
    return jsonText.value.match(regex)?.length ?? 0;
});

// Sync jsonText when the prop changes (e.g. switching dictionaries).
// The string comparison prevents a feedback loop: when the user edits and we
// emit, the parent updates the prop back to the same content, which would
// re-set the textarea and disrupt the user. Skipping equal content breaks it.
watch(
    () => props.data,
    (newVal) => {
        const formatted = JSON.stringify(newVal, null, 2);
        if (formatted !== jsonText.value) {
            jsonText.value = formatted;
        }
    },
    { immediate: true, deep: true },
);

// Validate and emit on every user keystroke
watch(jsonText, (text) => {
    try {
        const parsed = JSON.parse(text);
        parseError.value = '';
        emit('update:data', parsed);
    } catch (e: any) {
        parseError.value = e.message;
    }
});
</script>

<template>
    <div class="flex flex-col h-full bg-card rounded-xl border shadow-xs overflow-hidden">
        <!-- Header -->
        <div class="p-4 border-b bg-muted/20">
            <div class="flex items-center gap-3">
                <div class="relative flex-1">
                    <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input v-model="searchText" placeholder="Search in JSON..." class="pl-9" />
                </div>
                <span v-if="matchCount > 0" class="text-sm text-muted-foreground whitespace-nowrap">
                    {{ matchCount }} match{{ matchCount !== 1 ? 'es' : '' }}
                </span>
            </div>

            <div
                v-if="parseError"
                class="mt-3 flex items-start gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded-lg"
            >
                <AlertCircle class="h-4 w-4 text-destructive mt-0.5 shrink-0" />
                <div>
                    <p class="text-sm font-medium text-destructive">Invalid JSON</p>
                    <p class="text-xs text-destructive/80 mt-1">{{ parseError }}</p>
                </div>
            </div>
        </div>

        <!-- Editor + search highlight overlay -->
        <div class="flex-1 overflow-auto relative">
            <textarea
                v-model="jsonText"
                class="absolute inset-0 w-full h-full p-4 font-mono text-sm bg-transparent border-0 outline-hidden resize-none z-10 caret-foreground"
                :class="{ 'text-destructive': parseError }"
                spellcheck="false"
            />
            <!-- Transparent overlay renders the highlighted HTML behind the caret -->
            <div
                v-if="searchText.trim() && !parseError"
                class="absolute inset-0 p-4 font-mono text-sm pointer-events-none whitespace-pre-wrap wrap-break-word overflow-auto"
                style="color: transparent;"
                v-html="highlightedJson"
            />
        </div>

        <!-- Footer -->
        <div class="px-4 py-2 border-t bg-muted/10 text-xs text-muted-foreground flex items-center justify-between">
            <span>Direct JSON editing — changes auto-apply when valid</span>
            <span v-if="!parseError" class="text-green-600 dark:text-green-400">✓ Valid JSON</span>
        </div>
    </div>
</template>

<style scoped>
textarea {
    tab-size: 2;
    -moz-tab-size: 2;
    color: inherit;
}

:deep(mark) {
    background-color: rgb(253 224 71);
    border-radius: 0.125rem;
    padding: 0 0.125rem;
}

.dark :deep(mark) {
    background-color: rgb(202 138 4);
}
</style>
