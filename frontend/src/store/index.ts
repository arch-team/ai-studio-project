/**
 * Zustand Store Configuration
 *
 * Task: T019 - 配置 Zustand store
 * 创建 authStore, trainingJobsStore, datasetsStore
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

// ============================================================================
// Auth Store
// ============================================================================

export interface User {
  id: number;
  username: string;
  email: string;
  displayName?: string;
  role: 'admin' | 'project_manager' | 'engineer' | 'viewer';
  iamIdentityId?: string;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  setUser: (user: User) => void;
  setToken: (token: string) => void;
  login: (user: User, token: string) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      setUser: (user) => set({ user, isAuthenticated: true }),
      setToken: (token) => set({ accessToken: token }),
      login: (user, token) =>
        set({
          user,
          accessToken: token,
          isAuthenticated: true,
          error: null,
        }),
      logout: () =>
        set({
          user: null,
          accessToken: null,
          isAuthenticated: false,
        }),
      setLoading: (isLoading) => set({ isLoading }),
      setError: (error) => set({ error }),
      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// ============================================================================
// Training Jobs Store
// ============================================================================

export interface TrainingJob {
  id: string;
  jobName: string;
  status: 'submitted' | 'running' | 'paused' | 'preempted' | 'completed' | 'failed';
  instanceType: string;
  nodeCount: number;
  progress?: number;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
}

interface TrainingJobsState {
  jobs: TrainingJob[];
  selectedJob: TrainingJob | null;
  filters: {
    status?: string;
    search?: string;
  };
  pagination: {
    page: number;
    pageSize: number;
    total: number;
  };
  isLoading: boolean;

  // Actions
  setJobs: (jobs: TrainingJob[]) => void;
  addJob: (job: TrainingJob) => void;
  updateJob: (id: string, updates: Partial<TrainingJob>) => void;
  removeJob: (id: string) => void;
  selectJob: (job: TrainingJob | null) => void;
  setFilters: (filters: TrainingJobsState['filters']) => void;
  setPagination: (pagination: Partial<TrainingJobsState['pagination']>) => void;
  setLoading: (loading: boolean) => void;
  clearJobs: () => void;
}

export const useTrainingJobsStore = create<TrainingJobsState>((set) => ({
  jobs: [],
  selectedJob: null,
  filters: {},
  pagination: {
    page: 1,
    pageSize: 20,
    total: 0,
  },
  isLoading: false,

  setJobs: (jobs) => set({ jobs }),
  addJob: (job) => set((state) => ({ jobs: [...state.jobs, job] })),
  updateJob: (id, updates) =>
    set((state) => ({
      jobs: state.jobs.map((j) => (j.id === id ? { ...j, ...updates } : j)),
    })),
  removeJob: (id) =>
    set((state) => ({
      jobs: state.jobs.filter((j) => j.id !== id),
    })),
  selectJob: (job) => set({ selectedJob: job }),
  setFilters: (filters) => set({ filters }),
  setPagination: (pagination) =>
    set((state) => ({
      pagination: { ...state.pagination, ...pagination },
    })),
  setLoading: (isLoading) => set({ isLoading }),
  clearJobs: () => set({ jobs: [], selectedJob: null }),
}));

// ============================================================================
// Datasets Store
// ============================================================================

export interface Dataset {
  id: string;
  name: string;
  description?: string;
  s3Uri: string;
  sizeBytes: number;
  format: string;
  status: 'uploading' | 'ready' | 'syncing' | 'error';
  createdAt: string;
  updatedAt: string;
}

interface DatasetsState {
  datasets: Dataset[];
  selectedDataset: Dataset | null;
  filters: {
    status?: string;
    search?: string;
  };
  pagination: {
    page: number;
    pageSize: number;
    total: number;
  };
  isLoading: boolean;

  // Actions
  setDatasets: (datasets: Dataset[]) => void;
  addDataset: (dataset: Dataset) => void;
  updateDataset: (id: string, updates: Partial<Dataset>) => void;
  removeDataset: (id: string) => void;
  selectDataset: (dataset: Dataset | null) => void;
  setFilters: (filters: DatasetsState['filters']) => void;
  setPagination: (pagination: Partial<DatasetsState['pagination']>) => void;
  setLoading: (loading: boolean) => void;
  clearDatasets: () => void;
}

export const useDatasetsStore = create<DatasetsState>((set) => ({
  datasets: [],
  selectedDataset: null,
  filters: {},
  pagination: {
    page: 1,
    pageSize: 20,
    total: 0,
  },
  isLoading: false,

  setDatasets: (datasets) => set({ datasets }),
  addDataset: (dataset) =>
    set((state) => ({ datasets: [...state.datasets, dataset] })),
  updateDataset: (id, updates) =>
    set((state) => ({
      datasets: state.datasets.map((d) =>
        d.id === id ? { ...d, ...updates } : d
      ),
    })),
  removeDataset: (id) =>
    set((state) => ({
      datasets: state.datasets.filter((d) => d.id !== id),
    })),
  selectDataset: (dataset) => set({ selectedDataset: dataset }),
  setFilters: (filters) => set({ filters }),
  setPagination: (pagination) =>
    set((state) => ({
      pagination: { ...state.pagination, ...pagination },
    })),
  setLoading: (isLoading) => set({ isLoading }),
  clearDatasets: () => set({ datasets: [], selectedDataset: null }),
}));

// ============================================================================
// UI Store (global UI state)
// ============================================================================

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  notifications: Array<{
    id: string;
    type: 'info' | 'success' | 'warning' | 'error';
    message: string;
    timestamp: number;
  }>;

  // Actions
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  addNotification: (notification: Omit<UIState['notifications'][0], 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: 'light',
      notifications: [],

      toggleSidebar: () =>
        set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setTheme: (theme) => set({ theme }),
      addNotification: (notification) =>
        set((state) => ({
          notifications: [
            ...state.notifications,
            {
              ...notification,
              id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              timestamp: Date.now(),
            },
          ],
        })),
      removeNotification: (id) =>
        set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
        })),
      clearNotifications: () => set({ notifications: [] }),
    }),
    {
      name: 'ui-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        sidebarOpen: state.sidebarOpen,
        theme: state.theme,
      }),
    }
  )
);

// Legacy export for backwards compatibility
export const useUserStore = useAuthStore;
