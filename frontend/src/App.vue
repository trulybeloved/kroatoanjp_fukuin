<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useAppStore } from './stores/app';
import { Book, FileText, Github, Moon, Sun, Languages } from 'lucide-vue-next';
import Button from './components/ui/button/Button.vue';
import Processor from './components/Processor.vue';
import DictionaryEditor from './components/DictionaryEditor.vue';

const store = useAppStore();
const isDark = ref(true);

onMounted(async () => {
  // Set default dark mode
  document.documentElement.classList.add('dark');
  await store.fetchDictionaries();
});

const toggleDark = () => {
  isDark.value = !isDark.value;
  if (isDark.value) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
};
</script>

<template>
  <div class="min-h-screen bg-background text-foreground flex flex-col font-sans transition-colors duration-300">
    <!-- Header with Glassmorphism -->
    <header class="sticky top-0 z-50 w-full border-b bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60">
      <div class="container flex h-14 max-w-screen-2xl items-center justify-between px-4 sm:px-8">
        <div class="flex items-center gap-2">
          <Languages class="h-6 w-6 text-primary animate-pulse" />
          <span class="font-bold text-lg tracking-tight">Fukuin Preprocessor</span>
        </div>

        <nav class="flex items-center gap-1">
          <Button 
            variant="ghost" 
            size="sm" 
            :class="{ 'bg-accent': store.activeTab === 'processor' }"
            @click="store.activeTab = 'processor'"
          >
            <FileText class="mr-2 h-4 w-4" />
            Processor
          </Button>
          <Button 
            variant="ghost" 
            size="sm" 
            :class="{ 'bg-accent': store.activeTab === 'dictionary' }"
            @click="store.activeTab = 'dictionary'"
          >
            <Book class="mr-2 h-4 w-4" />
            Dictionary
          </Button>
        </nav>

        <div class="flex items-center gap-2">
          <div class="hidden sm:block text-xs text-muted-foreground mr-2">
            v1.0.0
          </div>
          <Button variant="ghost" size="icon" @click="toggleDark">
            <Moon v-if="isDark" class="h-5 w-5 transition-transform hover:rotate-12" />
            <Sun v-else class="h-5 w-5 transition-transform hover:rotate-90" />
            <span class="sr-only">Toggle theme</span>
          </Button>
          <a href="https://github.com/kroatoanjp/fukuin" target="_blank" rel="noreferrer">
             <Button variant="ghost" size="icon">
                <Github class="h-5 w-5" />
                <span class="sr-only">GitHub</span>
             </Button>
          </a>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="flex-1 container max-w-screen-2xl py-6 px-4 sm:px-8">
      <transition 
         enter-active-class="transition duration-200 ease-out"
         enter-from-class="opacity-0 translate-y-1"
         enter-to-class="opacity-100 translate-y-0"
         leave-active-class="transition duration-150 ease-in"
         leave-from-class="opacity-100 translate-y-0"
         leave-to-class="opacity-0 translate-y-1"
         mode="out-in"
      >
        <Processor v-if="store.activeTab === 'processor'" />
        <DictionaryEditor v-else />
      </transition>
    </main>
  </div>
</template>

<style scoped>
/* Custom Scrollbar for a premium feel */
::-webkit-scrollbar {
  width: 8px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: hsl(var(--muted-foreground) / 0.3);
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: hsl(var(--muted-foreground) / 0.5);
}
</style>
