<script setup lang="ts">
import { useAppStore } from '@/stores/app';
import { Play, Copy, Check, RotateCw } from 'lucide-vue-next';
import Button from './ui/button/Button.vue';
import { useClipboard } from '@vueuse/core';

const store = useAppStore();
const { copy, copied } = useClipboard();

const handleProcess = async () => {
    await store.processText();
};

const handleCopy = () => {
    copy(store.outputText);
};
</script>

<template>
  <div class="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-8rem)]">
    
    <!-- Sidebar / Configuration -->
    <div class="lg:col-span-1 space-y-6 flex flex-col h-full bg-card rounded-xl border p-5 shadow-sm overflow-y-auto custom-scrollbar">
        <div>
            <h2 class="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">Configuration</h2>
            
            <div class="space-y-4">
                <div class="space-y-2">
                    <label class="text-sm font-medium">Dictionary</label>
                    <select 
                        v-model="store.currentDictionary" 
                        class="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        @change="store.selectDictionary(($event.target as any).value.id)"
                    >
                        <option 
                            v-for="dict in store.dictionaries" 
                            :key="dict.id" 
                            :value="dict"
                        >
                            {{ dict.name }} {{ dict.is_default ? '(Default)' : ''}}
                        </option>
                    </select>
                    <p class="text-xs text-muted-foreground" v-if="store.currentDictionary">
                        Loaded: {{ store.currentDictionary.name }}
                    </p>
                </div>

                <div class="space-y-2">
                    <label class="text-sm font-medium">Tokenizer</label>
                    <select 
                        v-model="store.tokenizer" 
                        class="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                        <option value="spacy">spaCy (Recommended)</option>
                        <option value="sudachi">Sudachi</option>
                        <option value="fugashi">Fugashi</option>
                    </select>
                </div>
            </div>
        </div>

        <div class="pt-4 border-t">
            <h2 class="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">Options</h2>
             <div class="space-y-4">
                 <div class="flex items-center justify-between">
                     <label class="text-sm">Single Kanji Filter</label>
                     <input type="checkbox" v-model="store.singleKanjiFilter" class="h-4 w-4 rounded border-Primary text-primary focus:ring-primary/40 accent-primary" />
                 </div>
                 <div class="text-xs text-muted-foreground">
                    Skips replacement for single character names unless they have an honorific.
                 </div>
             </div>
        </div>

        <div class="mt-auto pt-4">
             <Button class="w-full gap-2 text-base shadow-lg shadow-primary/20 hover:shadow-primary/40 transition-all" size="lg" @click="handleProcess" :disabled="store.isProcessing">
                <RotateCw v-if="store.isProcessing" class="h-5 w-5 animate-spin" />
                <Play v-else class="h-5 w-5 fill-current" />
                <span v-if="store.isProcessing">Processing...</span>
                <span v-else>Run Process</span>
             </Button>
        </div>
    </div>

    <!-- Main IO Area -->
    <div class="lg:col-span-3 grid grid-rows-2 gap-4 h-full">
        <!-- Input -->
        <div class="bg-card rounded-xl border shadow-sm flex flex-col overflow-hidden group focus-within:ring-2 focus-within:ring-primary/20 transition-all">
            <div class="p-3 border-b bg-muted/40 flex justify-between items-center">
                 <span class="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Input Text</span>
                 <span class="text-xs text-muted-foreground" v-if="store.inputText.length > 0">{{ store.inputText.length }} chars</span>
            </div>
            <textarea 
                v-model="store.inputText"
                class="flex-1 w-full bg-transparent p-4 resize-none focus:outline-none font-mono text-sm leading-relaxed"
                placeholder="Paste Japanese text here..."
            ></textarea>
        </div>

        <!-- Output -->
        <div class="bg-card rounded-xl border shadow-sm flex flex-col overflow-hidden group relative">
             <div class="p-3 border-b bg-muted/40 flex justify-between items-center bg-primary/5">
                 <span class="text-xs font-semibold uppercase tracking-wider text-primary">Output Result</span>
                 <Button variant="ghost" size="sm" class="h-6 w-6 p-0 hover:bg-primary/10 hover:text-primary" @click="handleCopy" :title="copied ? 'Copied' : 'Copy'">
                     <Check v-if="copied" class="h-3.5 w-3.5 text-green-500" />
                     <Copy v-else class="h-3.5 w-3.5" />
                 </Button>
            </div>
            <textarea 
                v-model="store.outputText"
                readonly
                class="flex-1 w-full bg-transparent p-4 resize-none focus:outline-none font-mono text-sm leading-relaxed text-muted-foreground"
                placeholder="Result will appear here..."
            ></textarea>
            
            <div v-if="store.outputText && !store.isProcessing" class="absolute bottom-4 right-4 text-xs bg-background/80 backdrop-blur px-2 py-1 rounded border shadow-sm text-green-600 font-medium animate-accordion-down">
                Processing Complete
            </div>
        </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
    width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
   background-color: hsl(var(--border));
   border-radius: 20px;
}
</style>
