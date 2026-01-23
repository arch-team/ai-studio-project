/**
 * Space API client functions.
 */

import type {
  SpaceDetail,
  SpaceListResponse,
  SpaceFilters,
  CreateSpaceRequest,
  UpdateSpaceRequest,
} from '../types';

const API_BASE = '/api/v1';

/**
 * Fetch paginated list of spaces.
 */
export async function fetchSpaces(
  filters: SpaceFilters = {}
): Promise<SpaceListResponse> {
  const params = new URLSearchParams();

  if (filters.space_type) params.append('space_type', filters.space_type);
  if (filters.status) params.append('status', filters.status);
  if (filters.owner_id) params.append('owner_id', String(filters.owner_id));
  if (filters.page) params.append('page', String(filters.page));
  if (filters.page_size) params.append('page_size', String(filters.page_size));
  if (filters.sort_by) params.append('sort_by', filters.sort_by);
  if (filters.sort_order) params.append('sort_order', filters.sort_order);

  const response = await fetch(`${API_BASE}/spaces?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch spaces: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch a single space by ID.
 */
export async function fetchSpace(id: number): Promise<SpaceDetail> {
  const response = await fetch(`${API_BASE}/spaces/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch space: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Create a new space.
 */
export async function createSpace(
  data: CreateSpaceRequest
): Promise<SpaceDetail> {
  const response = await fetch(`${API_BASE}/spaces`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to create space: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Update an existing space.
 */
export async function updateSpace(
  id: number,
  data: UpdateSpaceRequest
): Promise<SpaceDetail> {
  const response = await fetch(`${API_BASE}/spaces/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to update space: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Delete a space.
 */
export async function deleteSpace(id: number): Promise<void> {
  const response = await fetch(`${API_BASE}/spaces/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete space: ${response.statusText}`);
  }
}

/**
 * Start a stopped space.
 */
export async function startSpace(id: number): Promise<SpaceDetail> {
  const response = await fetch(`${API_BASE}/spaces/${id}/start`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error(`Failed to start space: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Stop a running space.
 */
export async function stopSpace(id: number): Promise<SpaceDetail> {
  const response = await fetch(`${API_BASE}/spaces/${id}/stop`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error(`Failed to stop space: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Open space URL (redirect to JupyterLab/VS Code).
 */
export async function openSpace(id: number): Promise<{ url: string }> {
  const response = await fetch(`${API_BASE}/spaces/${id}/open`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error(`Failed to open space: ${response.statusText}`);
  }
  return response.json();
}
