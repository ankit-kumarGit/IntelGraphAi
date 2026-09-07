const BASE_URL = '/api';

export async function apiRequest(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const headers = { ...options.headers };
  
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`API Error [${response.status}]: ${errorBody}`);
  }

  return response.json();
}

export const api = {
  // System & Overview
  getHealth: () => apiRequest('/health'),
  getOverview: (role = 'Maintenance Engineer') => apiRequest(`/overview?role=${encodeURIComponent(role)}`),
  getHierarchy: () => apiRequest('/hierarchy'),

  // Assets
  getAssets: () => apiRequest('/assets'),
  getAsset: (tag) => apiRequest(`/assets/${tag}`),
  createAsset: (data) => apiRequest('/assets', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  getKnowledgeMap: (tag) => apiRequest(`/assets/${tag}/knowledge-map`),
  getMaintenance: (tag) => apiRequest(`/assets/${tag}/maintenance`),
  getTelemetry: (tag) => apiRequest(`/assets/${tag}/telemetry`),
  getCompliance: (tag) => apiRequest(`/assets/${tag}/compliance`),
  getNotes: (tag) => apiRequest(`/assets/${tag}/notes`),
  addNote: (tag, formData) => apiRequest(`/assets/${tag}/notes`, {
    method: 'POST',
    body: formData,
  }),

  // Action Center
  getActions: () => apiRequest('/actions'),

  // Documents
  getDocuments: (params = {}) => {
    const query = new URLSearchParams();
    if (params.asset_tag) query.append('asset_tag', params.asset_tag);
    if (params.category) query.append('category', params.category);
    if (params.governance_status) query.append('governance_status', params.governance_status);
    return apiRequest(`/documents?${query.toString()}`);
  },
  getDocument: (docId) => apiRequest(`/documents/${docId}`),
  getDocumentChunks: (docId) => apiRequest(`/documents/${docId}/chunks`),
  uploadDocument: (formData) => apiRequest('/documents/upload', {
    method: 'POST',
    body: formData,
  }),
  confirmExtraction: (formData) => apiRequest('/documents/confirm-extraction', {
    method: 'POST',
    body: formData,
  }),
  updateGovernance: (docId, formData) => apiRequest(`/documents/${docId}/governance`, {
    method: 'PATCH',
    body: formData,
  }),

  // RCA & Cross-Asset
  getCrossAssetPatterns: () => apiRequest('/cross-asset/patterns'),
  runRCA: (assetTag, problem) => {
    const form = new FormData();
    form.append('asset_tag', assetTag);
    form.append('problem', problem || 'High Vibration & Bearing Seizure');
    return apiRequest('/rca/analyze', {
      method: 'POST',
      body: form,
    });
  },

  // AI Assistant Chat
  chat: (query, assetTag, role = 'Maintenance Engineer', trustedOnly = true) => apiRequest('/chat', {
    method: 'POST',
    body: JSON.stringify({
      query,
      asset_tag: assetTag || null,
      user_role: role,
      trusted_sources_only: trustedOnly,
    }),
  }),

  // Benchmarks
  runBenchmarks: () => apiRequest('/benchmarks/run'),

  // Entity Resolution & P&ID
  resolveTag: (rawInput) => {
    const form = new FormData();
    form.append('raw_input', rawInput);
    return apiRequest('/entity-resolution/resolve', {
      method: 'POST',
      body: form,
    });
  },
  extractPIDTags: (text, drawingTitle) => {
    const form = new FormData();
    form.append('text', text);
    form.append('drawing_title', drawingTitle || 'P&ID Flowsheet');
    return apiRequest('/pid/extract-tags', {
      method: 'POST',
      body: form,
    });
  },

  // Audit Logs
  getAuditLogs: (targetId) => apiRequest(`/audit-logs${targetId ? `?target_id=${targetId}` : ''}`),
  reseed: () => apiRequest('/seed', { method: 'POST' }),
};
