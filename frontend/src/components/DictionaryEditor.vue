<script setup lang="ts"> 
import { computed, ref } from 'vue';
import { useAppStore } from '@/stores/app';
import { Save, Copy, Trash2 } from 'lucide-vue-next';
import Button from './ui/button/Button.vue';
import Input from './ui/input/Input.vue';
import JsonTable from './DictionaryEditor/JsonTable.vue';

const store = useAppStore();
const activeCategory = ref("names");
const newDictName = ref("");
const showCreateModal = ref(false);

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
    if(!store.currentDictionary || store.currentDictionary.is_default) return;
    if(confirm(`Are you sure you want to delete "${store.currentDictionary.name}"?`)) {
        await store.deleteDictionary(store.currentDictionary.id);
    }
}

// Watch active category to reset scroll or something if needed
</script>

<template>
  <div class="h-[calc(100vh-8rem)] flex flex-col gap-4">
      
      <!-- Toolbar -->
      <div class="flex items-center justify-between bg-card p-4 rounded-xl border shadow-sm">
          <div class="flex items-center gap-4">
                <div class="flex flex-col">
                    <label class="text-[10px] uppercase font-bold text-muted-foreground tracking-wider mb-1">Active Dictionary</label>
                    <select 
                        v-model="store.currentDictionary" 
                        class="h-9 w-64 rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        @change="store.selectDictionary(($event.target as any).value.id)"
                    >
                        <option 
                            v-for="dict in store.dictionaries" 
                            :key="dict.id" 
                            :value="dict"
                        >
                            {{ dict.name }} {{ dict.is_default ? '(Read-Only)' : ''}}
                        </option>
                    </select>
                </div>
                
                <div class="h-8 w-px bg-border mx-2"></div>

                <Button size="sm" variant="outline" @click="showCreateModal = true" title="Save as New">
                    <Copy class="h-4 w-4 mr-2" />
                    Clone / New
                </Button>
                
                <Button 
                    size="sm" 
                    variant="destructive" 
                    :disabled="!store.currentDictionary || store.currentDictionary.is_default"
                    @click="handleDelete"
                    title="Delete Dictionary"
                >
                    <Trash2 class="h-4 w-4" />
                </Button>
          </div>

          <div class="flex items-center gap-2">
              <span v-if="store.dirty" class="text-xs text-yellow-500 font-medium mr-2 animate-pulse">
                  Unsaved Changes
              </span>
              <Button @click="handleSave" :disabled="!store.dirty || (store.currentDictionary?.is_default ?? true)">
                  <Save class="h-4 w-4 mr-2" />
                  Save Changes
              </Button>
          </div>
      </div>

      <!-- Editor Area -->
      <div class="flex-1 grid grid-cols-12 gap-6 min-h-0">
          
          <!-- Sidebar Navigation -->
          <div class="col-span-3 bg-card rounded-xl border shadow-sm overflow-hidden flex flex-col">
              <div class="p-4 border-b bg-muted/20">
                  <h3 class="font-semibold text-sm">Categories</h3>
              </div>
              <div class="flex-1 overflow-y-auto p-2 space-y-1">
                  <button
                    v-for="cat in categories"
                    :key="cat.id"
                    @click="activeCategory = cat.id"
                    :class="[
                        'w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors flex flex-col gap-0.5',
                        activeCategory === cat.id ? 'bg-primary/10 text-primary font-medium' : 'hover:bg-muted text-muted-foreground'
                    ]"
                  >
                        <span>{{ cat.label }}</span>
                        <span class="text-[10px] opacity-70 truncate">{{ cat.desc }}</span>
                  </button>
              </div>
          </div>

          <!-- Main Table -->
          <div class="col-span-9 h-full min-h-0">
              <JsonTable 
                :title="categories.find(c => c.id === activeCategory)?.label || ''"
                :description="categories.find(c => c.id === activeCategory)?.desc"
                v-model:data="categoryData"
              />
          </div>
      </div>

      <!-- Simple Create Modal -->
      <div v-if="showCreateModal" class="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <div class="bg-card w-full max-w-md p-6 rounded-xl border shadow-lg space-y-4 animate-in fade-in zoom-in-95 duration-200">
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
