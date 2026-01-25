<script setup lang="ts">
import { ref, watch } from 'vue';
import { Trash2, Plus, Edit2, Check, X } from 'lucide-vue-next';
import Button from '../ui/button/Button.vue';
import Input from '../ui/input/Input.vue';

interface Props {
  data: Record<string, string | string[]>;
  title: string;
  description?: string;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  (e: 'update:data', payload: Record<string, string | string[]>): void
}>();

const editingKey = ref<string | null>(null);
const editKeyOriginal = ref<string>("");
const editKeyInput = ref<string>("");

const editValueInput = ref<string>("");
const editValueIsArray = ref(false);

const localData = ref({ ...props.data });

watch(() => props.data, (newVal) => {
    localData.value = { ...newVal };
}, { deep: true });

const deleteItem = (key: string) => {
    delete localData.value[key];
    emit('update:data', localData.value);
};

// Start adding a new item
const startAdd = () => {
    editingKey.value = "__NEW__";
    editKeyOriginal.value = "";
    editKeyInput.value = "";
    editValueInput.value = "";
    editValueIsArray.value = false;
};

// Start editing existing item
const startEdit = (key: string) => {
    editingKey.value = key;
    editKeyOriginal.value = key;
    editKeyInput.value = key;
    
    const val = localData.value[key];
    if (Array.isArray(val)) {
        editValueInput.value = val.join(" ");
        editValueIsArray.value = true;
    } else {
        editValueInput.value = val;
        editValueIsArray.value = false;
    }
};

const cancelEdit = () => {
    editingKey.value = null;
};

const saveEdit = () => {
    // Validate
    if (!editKeyInput.value.trim()) return;
    
    // If key changed, delete old
    if (editKeyOriginal.value && editKeyOriginal.value !== editKeyInput.value) {
        delete localData.value[editKeyOriginal.value];
    }

    // Process val
    let finalVal: string | string[] = editValueInput.value;
    if (editValueIsArray.value) {
        // split by space
        finalVal = editValueInput.value.split(/\s+/).filter(s => s);
    }

    localData.value[editKeyInput.value] = finalVal;
    editingKey.value = null;
    emit('update:data', localData.value);
};

</script>

<template>
  <div class="flex flex-col h-full bg-card rounded-xl border shadow-sm overflow-hidden">
    <div class="p-4 border-b bg-muted/20 flex justify-between items-center">
        <div>
            <h3 class="font-semibold text-lg">{{ title }}</h3>
            <p v-if="description" class="text-xs text-muted-foreground">{{ description }}</p>
        </div>
        <Button size="sm" @click="startAdd" class="gap-1">
            <Plus class="h-4 w-4" /> Add Entry
        </Button>
    </div>

    <!-- Edit Form Overlay or Inline -->
    <div v-if="editingKey" class="p-4 bg-primary/5 border-b grid grid-cols-12 gap-3 items-end animate-accordion-down">
        <div class="col-span-4">
             <label class="text-xs font-semibold mb-1 block">Key (English)</label>
             <Input v-model="editKeyInput" placeholder="Ex: Natsuki Subaru" />
        </div>
        <div class="col-span-5">
             <label class="text-xs font-semibold mb-1 block">Value (Japanese)</label>
             <Input v-model="editValueInput" placeholder="Ex: 菜月 昴" />
        </div>
        <div class="col-span-3 flex items-center gap-2 pb-0.5">
             <div class="flex items-center gap-2 mr-auto" title="Split value by spaces into array">
                <input type="checkbox" v-model="editValueIsArray" class="h-4 w-4 rounded border-primary text-primary focus:ring-primary/40 accent-primary" id="isArray" />
                <label for="isArray" class="text-xs cursor-pointer select-none">Multi-part</label>
             </div>
             <Button size="icon" variant="ghost" class="h-9 w-9 text-destructive hover:bg-destructive/10" @click="cancelEdit">
                <X class="h-4 w-4" />
             </Button>
             <Button size="icon" class="h-9 w-9" @click="saveEdit">
                <Check class="h-4 w-4" />
             </Button>
        </div>
    </div>

    <div class="flex-1 overflow-auto p-0">
        <table class="w-full text-sm text-left">
            <thead class="text-xs text-muted-foreground uppercase bg-muted/40 sticky top-0 backdrop-blur-sm">
                <tr>
                    <th class="px-4 py-3 font-medium w-[40%]">English Name / Key</th>
                    <th class="px-4 py-3 font-medium">Japanese Value</th>
                    <th class="px-4 py-3 font-medium w-20 text-right">Actions</th>
                </tr>
            </thead>
            <tbody class="divide-y">
               <tr v-for="(val, key) in localData" :key="key" class="hover:bg-muted/30 group transition-colors">
                   <td class="px-4 py-3 font-medium">{{ key }}</td>
                   <td class="px-4 py-3 font-mono text-muted-foreground">
                        <span v-if="Array.isArray(val)" class="flex gap-1 flex-wrap">
                            <span v-for="part in val" :key="part" class="bg-primary/10 text-primary px-1.5 py-0.5 rounded text-xs border border-primary/20">
                                {{ part }}
                            </span>
                        </span>
                        <span v-else>{{ val }}</span>
                   </td>
                   <td class="px-4 py-3 text-right">
                       <div class="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                           <Button size="icon" variant="ghost" class="h-7 w-7" @click="startEdit(String(key))">
                               <Edit2 class="h-3.5 w-3.5" />
                           </Button>
                           <Button size="icon" variant="ghost" class="h-7 w-7 text-destructive hover:bg-destructive/10" @click="deleteItem(String(key))">
                               <Trash2 class="h-3.5 w-3.5" />
                           </Button>
                       </div>
                   </td>
               </tr>
               <tr v-if="Object.keys(localData).length === 0">
                   <td colspan="3" class="px-4 py-8 text-center text-muted-foreground">
                       No entries found. Click "Add Entry" to create one.
                   </td>
               </tr>
            </tbody>
        </table>
    </div>
  </div>
</template>
