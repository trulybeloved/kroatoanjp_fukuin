<script setup lang="ts">
import { computed, ref } from 'vue';
import { useAppStore } from '@/stores/app';
import { Save, Copy, Trash2, Download, Upload, Table2, FileJson } from 'lucide-vue-next';
import Button from '@/components/ui/button/Button.vue';
import Input from '@/components/ui/input/Input.vue';
import JsonTable from '@/components/DictionaryEditor/JsonTable.vue';
import JsonEditor from '@/components/DictionaryEditor/JsonEditor.vue';
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
const viewMode = ref<'table' | 'json'>('table');
const newDictName = ref('');
const showCreateModal = ref(false);
const fileInputRef = ref<HTMLInputElement | null>(null);

const categories = [
    { id: 'names',       label: 'Important Names',  desc: 'Main characters and places' },
    { id: 'honorifics',  label: 'Honorifics',        desc: 'Japanese honorific mappings' },
    { id: 'full-names',  label: 'Remaining Names',   desc: 'Full names of other characters' },
    { id: 'last-names',  label: 'Last Names',        desc: 'Last names only' },
    { id: 'single-names',label: 'Single Names',      desc: 'First names or single parts' },
    { id: 'name-like',   label: 'Name-like',         desc: 'Terms treated as names' },
    { id: 'specials',    label: 'Specials',          desc: 'Non-name replacements' },
    { id: 'basic',       label: 'Basic',             desc: 'General punctuation/terms' },
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
                            <SelectItem
                                v-for="dict in store.dictionaries"
                                :key="dict.id"
                                :value="String(dict.id)"
                            >
                                {{ dict.name }}{{ dict.is_default ? ' (Read-Only)' : '' }}
                            </SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                <div class="w-px h-8 mx-2 bg-border" />

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

                <Button
                    size="sm"
                    variant="destructive"
                    :disabled="!store.currentDictionary || store.currentDictionary.is_default"
                    @click="handleDelete"
                >
                    <Trash2 class="w-4 h-4" />
                </Button>
            </div>

            <div class="flex items-center gap-2">
                <span v-if="store.dirty" class="mr-2 text-xs font-medium text-yellow-500 animate-pulse">
                    Unsaved Changes
                </span>
                <Button
                    @click="handleSave"
                    :disabled="!store.dirty || (store.currentDictionary?.is_default ?? true)"
                >
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
                    <div class="flex gap-2">
                        <Button
                            size="sm"
                            :variant="viewMode === 'table' ? 'default' : 'outline'"
                            class="flex-1 gap-2"
                            @click="viewMode = 'table'"
                        >
                            <Table2 class="h-4 w-4" /> Table
                        </Button>
                        <Button
                            size="sm"
                            :variant="viewMode === 'json' ? 'default' : 'outline'"
                            class="flex-1 gap-2"
                            @click="viewMode = 'json'"
                        >
                            <FileJson class="h-4 w-4" /> JSON
                        </Button>
                    </div>
                </div>

                <template v-if="viewMode === 'table'">
                    <div class="p-4 border-b bg-muted/20">
                        <h3 class="text-sm font-semibold">Categories</h3>
                    </div>
                    <div class="flex-1 p-2 space-y-1 overflow-y-auto">
                        <button
                            v-for="cat in categories"
                            :key="cat.id"
                            @click="activeCategory = cat.id"
                            :class="[
                                'w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors flex flex-col gap-0.5',
                                activeCategory === cat.id
                                    ? 'bg-primary/10 text-primary font-medium'
                                    : 'hover:bg-muted text-muted-foreground',
                            ]"
                        >
                            <span>{{ cat.label }}</span>
                            <span class="text-[10px] opacity-70 truncate">{{ cat.desc }}</span>
                        </button>
                    </div>
                </template>

                <template v-else>
                    <div class="flex-1 p-4 text-sm text-muted-foreground">
                        <p class="mb-2">Viewing entire dictionary as JSON.</p>
                        <p class="text-xs">Edit directly — changes are validated in real-time.</p>
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
                <JsonTable
                    v-if="viewMode === 'table'"
                    :key="activeCategory"
                    :title="categories.find(c => c.id === activeCategory)?.label ?? ''"
                    :description="categories.find(c => c.id === activeCategory)?.desc"
                    v-model:data="categoryData"
                />
                <JsonEditor
                    v-else
                    v-model:data="fullReplacementTable"
                />
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
                    <Input
                        v-model="newDictName"
                        placeholder="My Custom Dictionary"
                        @keydown.enter="handleCreate"
                    />
                </div>
                <DialogFooter>
                    <Button variant="ghost" @click="showCreateModal = false">Cancel</Button>
                    <Button @click="handleCreate" :disabled="!newDictName.trim()">Create</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    </div>
</template>
