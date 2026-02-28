<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
    historicalContent: Record<string, any>;
    currentContent: Record<string, any>;
    versionNumber: number;
}>();

type DiffStatus = 'added' | 'removed' | 'changed' | 'unchanged';

interface DiffEntry {
    key: string;
    oldValue?: any;
    newValue?: any;
    status: DiffStatus;
}

interface CategoryDiff {
    category: string;
    entries: DiffEntry[];
    hasChanges: boolean;
    added: number;
    removed: number;
    changed: number;
}

function formatValue(val: any): string {
    if (Array.isArray(val)) return val.join(', ');
    return String(val);
}

const diff = computed<CategoryDiff[]>(() => {
    const hist = props.historicalContent ?? {};
    const curr = props.currentContent ?? {};
    const allCategories = new Set([...Object.keys(hist), ...Object.keys(curr)]);

    return Array.from(allCategories).map(category => {
        const histCat = (hist[category] && typeof hist[category] === 'object') ? hist[category] : {};
        const currCat = (curr[category] && typeof curr[category] === 'object') ? curr[category] : {};
        const allKeys = new Set([...Object.keys(histCat), ...Object.keys(currCat)]);

        const entries: DiffEntry[] = Array.from(allKeys).map(key => {
            const inHist = key in histCat;
            const inCurr = key in currCat;
            if (!inHist) return { key, newValue: currCat[key], status: 'added' as DiffStatus };
            if (!inCurr) return { key, oldValue: histCat[key], status: 'removed' as DiffStatus };
            const sameValue = JSON.stringify(histCat[key]) === JSON.stringify(currCat[key]);
            if (!sameValue) return { key, oldValue: histCat[key], newValue: currCat[key], status: 'changed' as DiffStatus };
            return { key, oldValue: histCat[key], newValue: currCat[key], status: 'unchanged' as DiffStatus };
        });

        const changed = entries.filter(e => e.status === 'changed').length;
        const added = entries.filter(e => e.status === 'added').length;
        const removed = entries.filter(e => e.status === 'removed').length;

        return {
            category,
            entries,
            hasChanges: added + removed + changed > 0,
            added,
            removed,
            changed,
        };
    });
});

const summary = computed(() => ({
    totalAdded: diff.value.reduce((s, c) => s + c.added, 0),
    totalRemoved: diff.value.reduce((s, c) => s + c.removed, 0),
    totalChanged: diff.value.reduce((s, c) => s + c.changed, 0),
    changedCategories: diff.value.filter(c => c.hasChanges).length,
}));

const hasAnyChanges = computed(() =>
    summary.value.totalAdded + summary.value.totalRemoved + summary.value.totalChanged > 0
);
</script>

<template>
    <div class="h-full flex flex-col overflow-hidden rounded-xl border bg-card shadow-xs">
        <!-- Header -->
        <div class="px-5 py-3 border-b bg-muted/20 flex items-center gap-3 shrink-0">
            <span class="text-sm font-semibold">Version {{ versionNumber }} vs Current</span>
            <div class="flex items-center gap-2 text-xs ml-auto">
                <span v-if="summary.totalAdded > 0"
                    class="px-2 py-0.5 rounded-full bg-green-500/15 text-green-600 dark:text-green-400 font-medium">
                    +{{ summary.totalAdded }} added
                </span>
                <span v-if="summary.totalRemoved > 0"
                    class="px-2 py-0.5 rounded-full bg-red-500/15 text-red-600 dark:text-red-400 font-medium">
                    −{{ summary.totalRemoved }} removed
                </span>
                <span v-if="summary.totalChanged > 0"
                    class="px-2 py-0.5 rounded-full bg-yellow-500/15 text-yellow-600 dark:text-yellow-400 font-medium">
                    {{ summary.totalChanged }} changed
                </span>
            </div>
        </div>

        <!-- Diff body -->
        <div class="flex-1 overflow-y-auto p-4 space-y-4">
            <div v-if="!hasAnyChanges"
                class="flex items-center justify-center h-full text-sm text-muted-foreground">
                No differences — this version is identical to the current content.
            </div>

            <template v-else>
                <div v-for="cat in diff" :key="cat.category" v-show="cat.hasChanges">
                    <!-- Category header -->
                    <div class="flex items-center gap-2 mb-2">
                        <span class="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                            {{ cat.category }}
                        </span>
                        <div class="flex-1 h-px bg-border" />
                        <span v-if="cat.added" class="text-[10px] text-green-600 dark:text-green-400">+{{ cat.added }}</span>
                        <span v-if="cat.removed" class="text-[10px] text-red-600 dark:text-red-400">−{{ cat.removed }}</span>
                        <span v-if="cat.changed" class="text-[10px] text-yellow-600 dark:text-yellow-400">~{{ cat.changed }}</span>
                    </div>

                    <!-- Changed entries -->
                    <div class="rounded-lg overflow-hidden border divide-y divide-border/60 text-xs font-mono">
                        <template v-for="entry in cat.entries" :key="entry.key">
                            <!-- Added -->
                            <div v-if="entry.status === 'added'"
                                class="flex items-start px-3 py-1.5 bg-green-500/10">
                                <span class="text-green-600 dark:text-green-400 mr-2 shrink-0 select-none">+</span>
                                <span class="font-medium text-foreground mr-2 shrink-0">{{ entry.key }}</span>
                                <span class="text-green-700 dark:text-green-300 break-all">{{ formatValue(entry.newValue) }}</span>
                            </div>
                            <!-- Removed -->
                            <div v-else-if="entry.status === 'removed'"
                                class="flex items-start px-3 py-1.5 bg-red-500/10">
                                <span class="text-red-600 dark:text-red-400 mr-2 shrink-0 select-none">−</span>
                                <span class="font-medium text-foreground mr-2 shrink-0">{{ entry.key }}</span>
                                <span class="text-red-700 dark:text-red-300 break-all line-through">{{ formatValue(entry.oldValue) }}</span>
                            </div>
                            <!-- Changed -->
                            <div v-else-if="entry.status === 'changed'"
                                class="flex flex-col px-3 py-1.5 bg-yellow-500/10 gap-0.5">
                                <div class="flex items-start">
                                    <span class="text-red-500 mr-2 shrink-0 select-none">−</span>
                                    <span class="font-medium text-foreground mr-2 shrink-0">{{ entry.key }}</span>
                                    <span class="text-red-700 dark:text-red-300 break-all line-through">{{ formatValue(entry.oldValue) }}</span>
                                </div>
                                <div class="flex items-start">
                                    <span class="text-green-500 mr-2 shrink-0 select-none">+</span>
                                    <span class="font-medium text-foreground mr-2 shrink-0">{{ entry.key }}</span>
                                    <span class="text-green-700 dark:text-green-300 break-all">{{ formatValue(entry.newValue) }}</span>
                                </div>
                            </div>
                        </template>
                    </div>
                </div>
            </template>
        </div>
    </div>
</template>
