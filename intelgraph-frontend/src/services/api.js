const BASE_URL = '/api';

export async function apiRequest(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const headers = { ...options.headers };
  
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const token = localStorage.getItem('intelgraph_token');
  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = '';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || JSON.stringify(errJson);
    } catch {
      errorDetail = await response.text();
    }
    throw new Error(`API Error [${response.status}]: ${errorDetail}`);
  }

  return response.json();
}

export const api = {
  // System & Overview
  getHealth: () => apiRequest('/health'),
  getOverview: (role = 'Maintenance Engineer') => apiRequest(`/overview?role=${encodeURIComponent(role)}`),
  getHierarchy: () => apiRequest('/hierarchy'),

  // Assets & Machines
  getAssets: (includeArchived = false, status = null) => {
    const params = new URLSearchParams();
    if (includeArchived) params.append('include_archived', 'true');
    if (status) params.append('status', status);
    return apiRequest(`/assets?${params.toString()}`);
  },
  getAsset: (tag) => apiRequest(`/assets/${tag}`),
  createAsset: (data) => apiRequest('/assets', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  updateMachine: (tag, data) => apiRequest(`/machines/${tag}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  getDeletionPreview: (tag) => apiRequest(`/machines/${tag}/deletion-preview`),
  archiveMachine: (tag, reason = '') => apiRequest(`/machines/${tag}/archive`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  }),
  restoreMachine: (tag, reason = '') => apiRequest(`/machines/${tag}/restore`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  }),
  deleteMachine: (tag, exactTagConfirm) => {
    return apiRequest(`/machines/${tag}?exact_tag_confirm=${encodeURIComponent(exactTagConfirm)}`, {
      method: 'DELETE',
      body: JSON.stringify({ exact_tag_confirm: exactTagConfirm }),
    });
  },
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
  inspectDocument: (formData) => apiRequest('/documents/inspect', {
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
  chat: (query, assetTag, role = 'Maintenance Engineer', trustedOnly = true, conversationHistory = [], scopeFilter = 'Auto', contextAssetTag = null) => apiRequest('/chat', {
    method: 'POST',
    body: JSON.stringify({
      query,
      asset_tag: assetTag || null,
      context_asset_tag: contextAssetTag || null,  // non-authoritative context for pronoun resolution
      user_role: role,
      trusted_sources_only: trustedOnly,
      conversation_history: conversationHistory,
      scope_filter: scopeFilter,
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
  createAuditLog: (payload) => apiRequest('/audit-logs', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  reseed: () => apiRequest('/seed', { method: 'POST' }),

  // Enterprise Authentication & Impersonation
  login: (email, password) => apiRequest('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  }),
  getMe: (token) => apiRequest(`/auth/me${token ? `?token=${encodeURIComponent(token)}` : ''}`),
  getTenantCurrent: (tenantId) => apiRequest(`/tenant/current${tenantId ? `?tenant_id=${encodeURIComponent(tenantId)}` : ''}`),
  getPersonas: () => apiRequest('/auth/personas'),
  startImpersonation: (adminToken, targetUserId, reason, durationMinutes = 30) => apiRequest(`/auth/impersonate?admin_token=${encodeURIComponent(adminToken)}`, {
    method: 'POST',
    body: JSON.stringify({
      target_user_id: targetUserId,
      reason,
      duration_minutes: durationMinutes
    }),
  }),
  endImpersonation: (token) => apiRequest(`/auth/impersonate/end?token=${encodeURIComponent(token)}`, {
    method: 'POST',
  }),

  uploadArchive: (formData) => apiRequest('/documents/upload-archive', {
    method: 'POST',
    body: formData,
  }),

  // Action Center Status with Server-Side RBAC Enforcement
  updateActionStatus: (actionId, status, userRole) => apiRequest(`/actions/${actionId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status, user_role: userRole }),
  }),
  exportActionToCmms: (actionId, targetSystem = 'SAP_PM', notes = '') => apiRequest(`/actions/${actionId}/export-cmms?target_system=${encodeURIComponent(targetSystem)}&notes=${encodeURIComponent(notes)}`, {
    method: 'POST',
  }),

  // Regulatory Compliance Audit Evidence Package
  generateCompliancePackage: (assetTag, regulatoryBody, generatedBy) => apiRequest('/compliance/generate-package', {
    method: 'POST',
    body: JSON.stringify({
      asset_tag: assetTag || 'P-101',
      regulatory_body: regulatoryBody || 'API 610 / ISO 10816-3',
      generated_by: generatedBy || 'Corporate Compliance Auditor',
    }),
  }),

  // Admin Console & System Diagnostics
  getAdminHealth: () => apiRequest('/admin/system-health'),
  getAdminUsers: () => apiRequest('/admin/users'),
  getAdminConnectors: () => apiRequest('/admin/connectors'),
  getAIObservability: (limit = 50) => apiRequest(`/admin/ai-observability?limit=${limit}`),
  syncConnector: (connectorId) => apiRequest(`/admin/connectors/${connectorId}/sync`, {
    method: 'POST',
  }),

  // Dynamic Neo4j Graph Subgraph
  getGraphSubgraph: (centerTag, depth = 2, filterType = 'all') => {
    const params = new URLSearchParams();
    if (centerTag) params.append('center_tag', centerTag);
    params.append('depth', depth);
    params.append('filter_type', filterType);
    return apiRequest(`/graph/subgraph?${params.toString()}`);
  },

  // Document OCR Pipeline
  processOCR: (formData) => apiRequest('/documents/ocr-process', {
    method: 'POST',
    body: formData,
  }),
};
