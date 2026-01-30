<script setup lang="ts">
import { computed, ref } from 'vue';
import { useAppStore } from '@/stores/app';
import { Save, Copy, Trash2, Download, Upload } from 'lucide-vue-next';
import Button from '@/components/ui/button/Button.vue';
import Input from '@/components/ui/input/Input.vue';
import JsonTable from '@/components/DictionaryEditor/JsonTable.vue';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';

const store = useAppStore();
const activeCategory = ref("names");
const newDictName = ref("");
const showCreateModal = ref(false);
const fileInputRef = ref<HTMLInputElement | null>(null);

const categories = [
    { id: 'names', label: 'Important Names', desc: 'Main characters and places' },
    { id: 'honorifics', label: 'Honorifics', desc: 'Japanese honorific mappings' },
    { id: 'full-names', label: 'Remaining Names', desc: 'Full names of other characters' },
    { id: 'last-names', label: 'Last Names', desc: 'Last names only' },
    { id: 'single-names', label: 'Single Names', desc: 'First names or single parts' },
    { id: 'name-like', label: 'Name-like', desc: 'Terms treated as names' },
    { id: 'specials', label: 'Specials', desc: 'Non-name replacements' },
    { id: 'basic', label: 'Basic', desc: 'General punctuation/terms' }
];

const categoryData = computed({
    get: () => {
        if (!store.replacementTable) return {};
        // Ensure the category exists in the object
        return store.replacementTable[activeCategory.value] || {};
    },
    set: (val) => {
        if (!store.replacementTable) store.replacementTable = {};
        store.replacementTable[activeCategory.value] = val;
        store.dirty = true;
    }
});

const handleSave = async () => {
    await store.saveCurrentDictionary();
};

const handleCreate = async () => {
    if (!newDictName.value) return;
    await store.createWithCurrentContent(newDictName.value);
    showCreateModal.value = false;
    newDictName.value = "";
};

const handleDelete = async () => {
    if (!store.currentDictionary || store.currentDictionary.is_default) return;
    if (confirm(`Are you sure you want to delete "${store.currentDictionary.name}"?`)) {
        await store.deleteDictionary(store.currentDictionary.id);
    }
}

const handleDownload = () => {
    if (!store.replacementTable) return;

    const json = JSON.stringify(store.replacementTable, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `${store.currentDictionary?.name || 'dictionary'}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
};

const handleUpload = () => {
    fileInputRef.value?.click();
};

const handleFileChange = (event: Event) => {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];

    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const content = e.target?.result as string;
            const parsed = JSON.parse(content);
            store.replacementTable = parsed;
            store.dirty = true;
        } catch (error) {
            alert('Invalid JSON file. Please select a valid dictionary JSON file.');
            console.error('JSON parse error:', error);
        }
    };
    reader.readAsText(file);

    // Reset input so the same file can be selected again
    target.value = '';
};

// const handleSelectChange = (event: Event) => {
//     console.log("Selected dictionary id: ", event.target);
//     store.selectDictionary((event.target as any).value.id);
// }

</script>

<template>
    <div class="h-[calc(100vh-8rem)] flex flex-col gap-4">
        <div>{{ store.currentDictionary?.name }}</div>
        <!-- Hidden file input -->
        <input ref="fileInputRef" type="file" accept=".json" class="hidden" @change="handleFileChange" />

        <!-- Toolbar -->
        <div class="flex items-center justify-between p-4 border shadow-sm bg-card rounded-xl">
            <div class="flex items-center gap-4">
                <div class="flex flex-col">
                    <label class="text-[10px] uppercase font-bold text-muted-foreground tracking-wider mb-1">Active
                        Dictionary</label>
                    <Select v-model="store.currentDictionary">
                        <SelectTrigger>
                            <SelectValue placeholder="Select a dictionary" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem v-for="dict in store.dictionaries" :key="dict.id" :value="dict">
                                {{ dict.name }} {{ dict.is_default ? '(Read-Only)' : '' }}
                            </SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                <div class="w-px h-8 mx-2 bg-border"></div>

                <Button size="sm" variant="outline" @click="showCreateModal = true" title="Save as New">
                    <Copy class="w-4 h-4 mr-2" />
                    Clone / New
                </Button>

                <Button size="sm" variant="outline" @click="handleDownload" title="Download as JSON">
                    <Download class="w-4 h-4 mr-2" />
                    Export
                </Button>

                <Button size="sm" variant="outline" @click="handleUpload" title="Import from JSON">
                    <Upload class="w-4 h-4 mr-2" />
                    Import
                </Button>

                <Button size="sm" variant="destructive"
                    :disabled="!store.currentDictionary || store.currentDictionary.is_default" @click="handleDelete"
                    title="Delete Dictionary">
                    <Trash2 class="w-4 h-4" />
                </Button>
            </div>

            <div class="flex items-center gap-2">
                <span v-if="store.dirty" class="mr-2 text-xs font-medium text-yellow-500 animate-pulse">
                    Unsaved Changes
                </span>
                <Button @click="handleSave" :disabled="!store.dirty || (store.currentDictionary?.is_default ?? true)">
                    <Save class="w-4 h-4 mr-2" />
                    Save Changes
                </Button>
            </div>
        </div>

        <!-- Editor Area -->
        <div class="grid flex-1 min-h-0 grid-cols-12 gap-6">

            <!-- Sidebar Navigation -->
            <div class="flex flex-col col-span-3 overflow-hidden border shadow-sm bg-card rounded-xl">
                <div class="p-4 border-b bg-muted/20">
                    <h3 class="text-sm font-semibold">Categories</h3>
                </div>
                <div class="flex-1 p-2 space-y-1 overflow-y-auto">
                    <button v-for="cat in categories" :key="cat.id" @click="activeCategory = cat.id" :class="[
                        'w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors flex flex-col gap-0.5',
                        activeCategory === cat.id ? 'bg-primary/10 text-primary font-medium' : 'hover:bg-muted text-muted-foreground'
                    ]">
                        <span>{{ cat.label }}</span>
                        <span class="text-[10px] opacity-70 truncate">{{ cat.desc }}</span>
                    </button>
                </div>
            </div>

            <!-- Main Table -->
            <div class="h-full min-h-0 col-span-9">
                <JsonTable :title="categories.find(c => c.id === activeCategory)?.label || ''"
                    :description="categories.find(c => c.id === activeCategory)?.desc" v-model:data="categoryData" />
            </div>
        </div>

        <!-- Simple Create Modal -->
        <div v-if="showCreateModal"
            class="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
            <div
                class="w-full max-w-md p-6 space-y-4 duration-200 border shadow-lg bg-card rounded-xl animate-in fade-in zoom-in-95">
                <div>
                    <h3 class="text-lg font-semibold">Create New Dictionary</h3>
                    <p class="text-sm text-muted-foreground">Clone current settings into a new dictionary.</p>
                </div>
                <div class="space-y-2">
                    <label class="text-sm font-medium">Name</label>
                    <Input v-model="newDictName" placeholder="My Custom Dictionary" />
                </div>
                <div class="flex justify-end gap-2 pt-2">
                    <Button variant="ghost" @click="showCreateModal = false">Cancel</Button>
                    <Button @click="handleCreate" :disabled="!newDictName">Create</Button>
                </div>
            </div>
        </div>

    </div>
</template>