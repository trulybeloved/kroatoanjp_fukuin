import axios from 'axios';

const API_URL = 'http://192.168.2.125:8000'; // Adjust if needed

export interface Dictionary {
    id: number;
    name: string;
    is_default: boolean;
    content: string; // JSON string
    created_at: string;
    updated_at: string;
}

export interface DictionaryHistoryEntry {
    id: number;
    dictionary_id: number;
    version_number: number;
    created_at: string;
}

export interface DictionaryHistoryDetail extends DictionaryHistoryEntry {
    content: string;
}

export interface ReplacementDetail {
    category: string;
    original: string;
    replacement: string;
    count: number;
}

export interface PreprocessResponse {
    text: string;
    total_replacements: number;
    replacements: ReplacementDetail[];
}

export interface PreprocessRequest {
    text: string;
    replacement_table: any;
    tokenizer?: string;
    tag_potential_proper_nouns?: boolean;
    use_user_dict?: boolean;
    user_dic_path?: string;
    use_single_kanji_filter?: boolean;
    verbose?: boolean;
}

export const api = {
    async health() {
        return axios.get(`${API_URL}/health`);
    },

    async preprocessNLP(data: PreprocessRequest) {
        return axios.post<PreprocessResponse>(`${API_URL}/preprocess/nlp`, data);
    },

    async preprocessBasic(data: PreprocessRequest) {
        return axios.post<PreprocessResponse>(`${API_URL}/preprocess/basic`, data);
    },

    // Dictionary CRUD
    async getDictionaries() {
        return axios.get<Dictionary[]>(`${API_URL}/dictionaries`);
    },

    async getDictionary(id: number) {
        return axios.get<Dictionary>(`${API_URL}/dictionaries/${id}`);
    },

    async createDictionary(name: string, content: string) {
        return axios.post<Dictionary>(`${API_URL}/dictionaries`, { name, content });
    },

    async updateDictionary(id: number, name?: string, content?: string) {
        return axios.put<Dictionary>(`${API_URL}/dictionaries/${id}`, { name, content });
    },

    async deleteDictionary(id: number) {
        return axios.delete(`${API_URL}/dictionaries/${id}`);
    },

    async setDefaultDictionary(id: number) {
        return axios.put<Dictionary>(`${API_URL}/dictionaries/${id}/set-default`);
    },

    async getDictionaryHistory(id: number) {
        return axios.get<DictionaryHistoryEntry[]>(`${API_URL}/dictionaries/${id}/history`);
    },

    async getDictionaryHistoryVersion(dictId: number, versionId: number) {
        return axios.get<DictionaryHistoryDetail>(`${API_URL}/dictionaries/${dictId}/history/${versionId}`);
    }
};
