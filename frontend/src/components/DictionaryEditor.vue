<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useAppStore } from '@/stores/app';
import { Save, Copy, Trash2, Download, Upload, Table2, FileJson, Star, History, RotateCcw } from 'lucide-vue-next';
import Button from '@/components/ui/button/Button.vue';
import Input from '@/components/ui/input/Input.vue';
import JsonTable from '@/components/DictionaryEditor/JsonTable.vue';
import JsonEditor from '@/components/DictionaryEditor/JsonEditor.vue';
import HistoryDiff from '@/components/DictionaryEditor/HistoryDiff.vue';
import { api, type DictionaryHistoryEntry } from '@/services/api';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';

const store = useAppStore();
const activeCategory = ref('names');
const viewMode = ref<'table' | 'json' | 'history'>('json');
const newDictName = ref('');
const showCreateModal = ref(false);
const fileInputRef = ref<HTMLInputElement | null>(null);

// History state
const historyEntries = ref<DictionaryHistoryEntry[]>([]);
const selectedHistoryId = ref<number | null>(null);
const selectedHistoryContent = ref<any>(null);
const isLoadingHistory = ref(false);
const isLoadingVersion = ref(false);

const selectedEntry = computed(() =>
    historyEntries.value.find(e => e.id === selectedHistoryId.value) ?? null
);

function formatHistoryDate(isoString: string): string {
    const d = new Date(isoString);
    return d.toLocaleString(undefined, {
        month: 'short', day: 'numeric', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
    });
}

async function fetchHistory() {
    if (!store.currentDictionary) return;
    isLoadingHistory.value = true;
    selectedHistoryId.value = null;
    selectedHistoryContent.value = null;
    try {
        const res = await api.getDictionaryHistory(store.currentDictionary.id);
        historyEntries.value = res.data;
        if (historyEntries.value.length > 0) {
            await selectHistoryVersion(historyEntries.value[0].id);
        }
    } catch (e) {
        console.error('Failed to fetch history', e);
    } finally {
        isLoadingHistory.value = false;
    }
}

async function selectHistoryVersion(versionId: number) {
    if (!store.currentDictionary) return;
    isLoadingVersion.value = true;
    try {
        const res = await api.getDictionaryHistoryVersion(store.currentDictionary.id, versionId);
        selectedHistoryId.value = versionId;
        selectedHistoryContent.value = JSON.parse(res.data.content);
    } catch (e) {
        console.error('Failed to load history version', e);
    } finally {
        isLoadingVersion.value = false;
    }
}

function handleExportVersion() {
    if (!selectedHistoryContent.value || !selectedEntry.value) return;
    const blob = new Blob([JSON.stringify(selectedHistoryContent.value, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${store.currentDictionary?.name ?? 'dictionary'}_v${selectedEntry.value.version_number}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function handleRestoreVersion() {
    if (!selectedHistoryContent.value) return;
    store.replacementTable = JSON.parse(JSON.stringify(selectedHistoryContent.value));
    store.dirty = true;
    viewMode.value = 'json';
}

// Fetch history when switching to history mode or changing dictionary
watch(viewMode, (mode) => {
    if (mode === 'history') fetchHistory();
});
watch(() => store.currentDictionary?.id, () => {
    if (viewMode.value === 'history') fetchHistory();
});

const categories = [
    { id: 'names', label: 'Important Names', desc: 'Main characters and places' },
    { id: 'honorifics', label: 'Honorifics', desc: 'Japanese honorific mappings' },
    { id: 'full-names', label: 'Remaining Names', desc: 'Full names of other characters' },
    { id: 'last-names', label: 'Last Names', desc: 'Last names only' },
    { id: 'single-names', label: 'Single Names', desc: 'First names or single parts' },
    { id: 'name-like', label: 'Name-like', desc: 'Terms treated as names' },
    { id: 'specials', label: 'Specials', desc: 'Non-name replacements' },
    { id: 'basic', label: 'Basic', desc: 'General punctuation/terms' },
];

// Use a string ID so the Select can match values by reference-free equality
const selectedDictId = computed(() =>
    store.currentDictionary ? String(store.currentDictionary.id) : ''
);

const categoryData = computed({
    get: () => store.replacementTable?.[activeCategory.value] ?? {},
    set: (val) => {
        if (!store.replacementTable) store.replacementTable = {};
        store.replacementTable[activeCategory.value] = val;
        store.dirty = true;
    },
});

const fullReplacementTable = computed({
    get: () => store.replacementTable ?? {},
    set: (val) => {
        store.replacementTable = val;
        store.dirty = true;
    },
});

const handleDictionaryChange = async (value: unknown) => {
    const id = Number(value);
    if (!isNaN(id) && id > 0) {
        await store.selectDictionary(id);
    }
};

const handleSave = async () => {
    await store.saveCurrentDictionary();
};

const handleCreate = async () => {
    const name = newDictName.value.trim();
    if (!name) return;
    await store.createWithCurrentContent(name);
    showCreateModal.value = false;
    newDictName.value = '';
};

const handleSetDefault = async () => {
    if (!store.currentDictionary || store.currentDictionary.is_default) return;
    await store.setDefaultDictionary(store.currentDictionary.id);
};

const handleDelete = async () => {
    if (!store.currentDictionary || store.currentDictionary.is_default) return;
    if (confirm(`Are you sure you want to delete "${store.currentDictionary.name}"?`)) {
        await store.deleteDictionary(store.currentDictionary.id);
    }
};

const handleDownload = () => {
    if (!store.replacementTable) return;
    const blob = new Blob([JSON.stringify(store.replacementTable, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${store.currentDictionary?.name ?? 'dictionary'}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
};

const handleFileChange = (event: Event) => {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            store.replacementTable = JSON.parse(e.target?.result as string);
            store.dirty = true;
        } catch (err) {
            alert('Invalid JSON file. Please select a valid dictionary JSON file.');
            console.error('JSON parse error:', err);
        }
    };
    reader.readAsText(file);
    target.value = '';
};
</script>

<template>
    <div class="h-[calc(100vh-8rem)] flex flex-col gap-4">
        <input ref="fileInputRef" type="file" accept=".json" class="hidden" @change="handleFileChange" />

        <!-- Toolbar -->
        <div class="flex items-center justify-between p-4 border shadow-xs bg-card rounded-xl">
            <div class="flex items-center gap-4">
                <div class="flex flex-col">
                    <label class="text-[10px] uppercase font-bold text-muted-foreground tracking-wider mb-1">
                        Active Dictionary
                    </label>
                    <Select :model-value="selectedDictId" @update:model-value="handleDictionaryChange">
                        <SelectTrigger>
                            <SelectValue placeholder="Select a dictionary" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem v-for="dict in store.dictionaries" :key="dict.id" :value="String(dict.id)">
                                {{ dict.name }}{{ dict.is_default ? ' (Default)' : '' }}
                            </SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                <div class="w-px h-8 mx-2 bg-border" />

                <Button size="sm" variant="outline"
                    :disabled="!store.currentDictionary || store.currentDictionary.is_default"
                    @click="handleSetDefault">
                    <Star class="w-4 h-4 mr-2" />
                    Set as Default
                </Button>

                <Button size="sm" variant="outline" @click="showCreateModal = true">
                    <Copy class="w-4 h-4 mr-2" />
                    Clone / New
                </Button>

                <Button size="sm" variant="outline" @click="handleDownload">
                    <Download class="w-4 h-4 mr-2" />
                    Export
                </Button>

                <Button size="sm" variant="outline" @click="fileInputRef?.click()">
                    <Upload class="w-4 h-4 mr-2" />
                    Import
                </Button>

                <Button size="sm" variant="destructive"
                    :disabled="!store.currentDictionary || store.currentDictionary.is_default" @click="handleDelete">
                    <Trash2 class="w-4 h-4" />
                </Button>
            </div>

            <div class="flex items-center gap-2">
                <span v-if="store.dirty" class="mr-2 text-xs font-medium text-yellow-500 animate-pulse">
                    Unsaved Changes
                </span>
                <Button @click="handleSave" :disabled="!store.dirty">
                    <Save class="w-4 h-4 mr-2" />
                    Save Changes
                </Button>
            </div>
        </div>

        <!-- Editor Area -->
        <div class="grid flex-1 min-h-0 grid-cols-12 gap-6">

            <!-- Sidebar -->
            <div class="flex flex-col col-span-3 overflow-hidden border shadow-xs bg-card rounded-xl">
                <div class="p-4 border-b bg-muted/20">
                    <h3 class="text-sm font-semibold mb-3">View Mode</h3>
                    <div class="flex gap-1">
                        <Button size="sm" :variant="viewMode === 'table' ? 'default' : 'outline'" class="flex-1 gap-1.5"
                            @click="viewMode = 'table'">
                            <Table2 class="h-4 w-4" /> Table
                        </Button>
                        <Button size="sm" :variant="viewMode === 'json' ? 'default' : 'outline'" class="flex-1 gap-1.5"
                            @click="viewMode = 'json'">
                            <FileJson class="h-4 w-4" /> JSON
                        </Button>
                        <Button size="sm" :variant="viewMode === 'history' ? 'default' : 'outline'" class="flex-1 gap-1.5"
                            @click="viewMode = 'history'">
                            <History class="h-4 w-4" /> History
                        </Button>
                    </div>
                </div>

                <!-- Category list (table mode) -->
                <template v-if="viewMode === 'table'">
                    <div class="p-4 border-b bg-muted/20">
                        <h3 class="text-sm font-semibold">Categories</h3>
                    </div>
                    <div class="flex-1 p-2 space-y-1 overflow-y-auto">
                        <button v-for="cat in categories" :key="cat.id" @click="activeCategory = cat.id" :class="[
                            'w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors flex flex-col gap-0.5',
                            activeCategory === cat.id
                                ? 'bg-primary/10 text-primary font-medium'
                                : 'hover:bg-muted text-muted-foreground',
                        ]">
                            <span>{{ cat.label }}</span>
                            <span class="text-[10px] opacity-70 truncate">{{ cat.desc }}</span>
                        </button>
                    </div>
                </template>

                <!-- JSON mode info -->
                <template v-else-if="viewMode === 'json'">
                    <div class="flex-1 p-4 text-sm text-muted-foreground">
                        <p class="mb-2">Viewing entire dictionary as JSON.</p>
                        <p class="text-xs">Edit directly — changes are validated in real-time.</p>
                    </div>
                </template>

                <!-- History version list -->
                <template v-else>
                    <div class="p-4 border-b bg-muted/20 shrink-0">
                        <h3 class="text-sm font-semibold">Saved Versions</h3>
                        <p class="text-[10px] text-muted-foreground mt-0.5">Up to 500 versions kept</p>
                    </div>
                    <div class="flex-1 overflow-y-auto">
                        <div v-if="isLoadingHistory" class="flex items-center justify-center h-20 text-xs text-muted-foreground">
                            Loading…
                        </div>
                        <div v-else-if="historyEntries.length === 0" class="p-4 text-xs text-muted-foreground">
                            No history yet. Save the dictionary to create a version.
                        </div>
                        <div v-else class="p-2 space-y-1">
                            <button
                                v-for="entry in historyEntries"
                                :key="entry.id"
                                @click="selectHistoryVersion(entry.id)"
                                :class="[
                                    'w-full text-left px-3 py-2 rounded-lg text-xs transition-colors flex flex-col gap-0.5',
                                    selectedHistoryId === entry.id
                                        ? 'bg-primary/10 text-primary font-medium'
                                        : 'hover:bg-muted text-muted-foreground',
                                ]"
                            >
                                <span class="font-semibold">v{{ entry.version_number }}</span>
                                <span class="text-[10px] opacity-80">{{ formatHistoryDate(entry.created_at) }}</span>
                            </button>
                        </div>
                    </div>
                </template>
            </div>

            <!-- Main Content -->
            <div class="h-full min-h-0 col-span-9">
                <!--
                    :key="activeCategory" remounts the table on each category switch,
                    which cleanly resets all local state (search, edit form, etc.)
                    without needing extra watchers.
                -->
                <JsonTable v-if="viewMode === 'table'" :key="activeCategory"
                    :title="categories.find(c => c.id === activeCategory)?.label ?? ''"
                    :description="categories.find(c => c.id === activeCategory)?.desc" v-model:data="categoryData" />
                <JsonEditor v-else-if="viewMode === 'json'" v-model:data="fullReplacementTable" />
                <div v-else class="h-full flex flex-col gap-3">
                    <div v-if="isLoadingVersion || isLoadingHistory" class="flex items-center justify-center h-full text-sm text-muted-foreground">
                        Loading version…
                    </div>
                    <template v-else-if="selectedHistoryContent && selectedEntry">
                        <div class="flex items-center gap-2 shrink-0">
                            <Button size="sm" variant="outline" @click="handleExportVersion">
                                <Download class="w-4 h-4 mr-2" />
                                Export v{{ selectedEntry.version_number }}
                            </Button>
                            <Button size="sm" variant="outline" @click="handleRestoreVersion">
                                <RotateCcw class="w-4 h-4 mr-2" />
                                Restore v{{ selectedEntry.version_number }}
                            </Button>
                        </div>
                        <HistoryDiff
                            class="flex-1 min-h-0"
                            :historical-content="selectedHistoryContent"
                            :current-content="store.replacementTable"
                            :version-number="selectedEntry.version_number"
                        />
                    </template>
                    <div v-else class="flex items-center justify-center h-full text-sm text-muted-foreground">
                        Select a version from the list to compare.
                    </div>
                </div>
            </div>
        </div>

        <!-- Create Dictionary Dialog -->
        <Dialog v-model:open="showCreateModal">
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Create New Dictionary</DialogTitle>
                    <DialogDescription>Clone current settings into a new dictionary.</DialogDescription>
                </DialogHeader>
                <div class="space-y-2 py-2">
                    <label class="text-sm font-medium">Name</label>
                    <Input v-model="newDictName" placeholder="My Custom Dictionary" @keydown.enter="handleCreate" />
                </div>
                <DialogFooter>
                    <Button variant="ghost" @click="showCreateModal = false">Cancel</Button>
                    <Button @click="handleCreate" :disabled="!newDictName.trim()">Create</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    </div>
</template>
