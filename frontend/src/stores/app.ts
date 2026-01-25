import { defineStore } from 'pinia';
import { api, type Dictionary, type PreprocessRequest } from '@/services/api';

export const useAppStore = defineStore('app', {
    state: () => ({
        dictionaries: [] as Dictionary[],
        currentDictionary: null as Dictionary | null,
        replacementTable: {} as any, // The parsed JSON content
        inputText: '',
        outputText: '',
        isProcessing: false,
        isLoadingDictionaries: false,
        tokenizer: 'spacy',
        singleKanjiFilter: false,
        activeTab: 'processor', // 'processor' | 'dictionary'
        dirty: false, // If replacementTable is modified vs database
    }),

    actions: {
        async fetchDictionaries() {
            this.isLoadingDictionaries = true;
            try {
                const response = await api.getDictionaries();
                this.dictionaries = response.data;
                // Select default if none selected or if current is invalid
                if (!this.currentDictionary && this.dictionaries.length > 0) {
                    const defaultDict = this.dictionaries.find(d => d.is_default);
                    if (defaultDict) {
                        await this.selectDictionary(defaultDict.id);
                    } else {
                        await this.selectDictionary(this.dictionaries[0].id);
                    }
                }
            } catch (e) {
                console.error("Failed to fetch dictionaries", e);
            } finally {
                this.isLoadingDictionaries = false;
            }
        },

        async selectDictionary(id: number) {
            try {
                const response = await api.getDictionary(id);
                this.currentDictionary = response.data;
                this.replacementTable = JSON.parse(this.currentDictionary.content);
                this.dirty = false;
            } catch (e) {
                console.error("Failed to select dictionary", e);
            }
        },

        async saveCurrentDictionary() {
            if (!this.currentDictionary) return;
            try {
                const contentStr = JSON.stringify(this.replacementTable, null, 2);
                await api.updateDictionary(this.currentDictionary.id, this.currentDictionary.name, contentStr);
                // Refresh
                await this.selectDictionary(this.currentDictionary.id);
                this.dirty = false;
            } catch (e) {
                console.error("Failed to save dictionary", e);
                throw e;
            }
        },

        async deleteDictionary(id: number) {
            try {
                await api.deleteDictionary(id);
                this.dictionaries = this.dictionaries.filter(d => d.id !== id);
                if (this.currentDictionary?.id === id) {
                    this.currentDictionary = null;
                    if (this.dictionaries.length > 0) {
                        await this.selectDictionary(this.dictionaries[0].id);
                    }
                }
            } catch (e) {
                console.error("Failed to delete dictionary", e);
                throw e;
            }
        },

        async createWithCurrentContent(name: string) {
            try {
                const contentStr = JSON.stringify(this.replacementTable, null, 2);
                const response = await api.createDictionary(name, contentStr);
                this.dictionaries.push(response.data);
                await this.selectDictionary(response.data.id);
                return response.data;
            } catch (e) {
                console.error("Failed to create dictionary", e);
                throw e;
            }
        },

        async processText() {
            this.isProcessing = true;
            try {
                const payload: PreprocessRequest = {
                    text: this.inputText,
                    replacement_table: this.replacementTable,
                    tokenizer: this.tokenizer,
                    use_single_kanji_filter: this.singleKanjiFilter,
                    verbose: false // Can expose if needed
                };
                const response = await api.preprocessNLP(payload);
                this.outputText = response.data.text;
                // Could also store total_replacements
            } catch (e) {
                console.error("Processing failed", e);
                this.outputText = "Error processing text. Check console.";
            } finally {
                this.isProcessing = false;
            }
        }
    }
});
