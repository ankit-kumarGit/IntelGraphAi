import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { 
  ReactFlow, 
  Background, 
  Controls, 
  MiniMap, 
  useNodesState, 
  useEdgesState,
  MarkerType,
  Handle,
  Position
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { 
  Layers, 
  Cpu, 
  FileText, 
  Wrench, 
  Activity, 
  AlertTriangle, 
  ShieldCheck, 
  Info, 
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Folder,
  FolderOpen,
  Eye,
  CheckCircle2,
  Filter
} from 'lucide-react';
import EvidenceDrawer from '../common/EvidenceDrawer';

// -------------------------------------------------------------
// CUSTOM NODE RENDERERS
// -------------------------------------------------------------

// 1. Central Asset Node
function CentralAssetNode({ data, selected }) {
  return (
    <div className={`px-5 py-4 rounded-2xl bg-gradient-to-br from-slate-900 via-brand-950/40 to-slate-900 border-2 transition-all shadow-2xl min-w-[220px] ${
      selected ? 'border-brand-400 ring-4 ring-brand-500/20 shadow-brand-500/20' : 'border-brand-500/60 shadow-brand-900/30'
    }`}>
      <Handle type="target" position={Position.Top} className="!bg-brand-400 !w-2.5 !h-2.5" />
      <Handle type="source" position={Position.Top} className="!bg-brand-400 !w-2.5 !h-2.5" />
      <Handle type="target" position={Position.Bottom} className="!bg-brand-400 !w-2.5 !h-2.5" />
      <Handle type="source" position={Position.Bottom} className="!bg-brand-400 !w-2.5 !h-2.5" />
      <Handle type="target" position={Position.Left} className="!bg-brand-400 !w-2.5 !h-2.5" />
      <Handle type="source" position={Position.Left} className="!bg-brand-400 !w-2.5 !h-2.5" />
      <Handle type="target" position={Position.Right} className="!bg-brand-400 !w-2.5 !h-2.5" />
      <Handle type="source" position={Position.Right} className="!bg-brand-400 !w-2.5 !h-2.5" />

      <div className="flex items-center justify-between gap-2 border-b border-brand-500/30 pb-1.5 mb-1.5">
        <span className="font-mono text-xs font-bold text-brand-400 bg-brand-500/10 px-2 py-0.5 rounded">
          {data.tag || 'ASSET'}
        </span>
        <span className="flex items-center gap-1 text-[10px] text-emerald-400 font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
          {data.status || 'Operational'}
        </span>
      </div>

      <div className="font-bold text-sm text-white leading-snug">
        {data.label}
      </div>
      <div className="text-[11px] text-slate-400 mt-1">
        {data.details || 'Central Machine Brain'}
      </div>
    </div>
  );
}

// 2. High-Level Knowledge Module Hub Node (Collapsed by Default)
function ModuleHubNode({ data, selected }) {
  const isExpanded = data.isExpanded;
  const type = data.moduleType;

  const typeConfig = {
    component: {
      border: 'border-cyan-500/50',
      badge: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30',
      iconColor: 'text-cyan-400',
      label: 'Components Module'
    },
    document: {
      border: 'border-purple-500/50',
      badge: 'bg-purple-500/15 text-purple-300 border-purple-500/30',
      iconColor: 'text-purple-400',
      label: 'Documents & SOPs'
    },
    maintenance: {
      border: 'border-blue-500/50',
      badge: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
      iconColor: 'text-blue-400',
      label: 'Maintenance Records'
    },
    inspection: {
      border: 'border-emerald-500/50',
      badge: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
      iconColor: 'text-emerald-400',
      label: 'Inspection Surveys'
    },
    failure: {
      border: 'border-red-500/60',
      badge: 'bg-red-500/20 text-red-300 border-red-500/40',
      iconColor: 'text-red-400',
      label: 'Failure History'
    }
  };

  const cfg = typeConfig[type] || {
    border: 'border-slate-700',
    badge: 'bg-slate-800 text-slate-300',
    iconColor: 'text-brand-400',
    label: 'Knowledge Module'
  };

  return (
    <div className={`p-4 rounded-2xl bg-slate-900 border ${cfg.border} shadow-xl min-w-[200px] transition-all cursor-pointer ${
      selected ? 'ring-2 ring-white shadow-2xl scale-105' : 'hover:border-slate-400'
    }`}>
      <Handle type="target" position={Position.Top} className="!bg-slate-400 !w-2 !h-2" />
      <Handle type="source" position={Position.Top} className="!bg-slate-400 !w-2 !h-2" />
      <Handle type="target" position={Position.Bottom} className="!bg-slate-400 !w-2 !h-2" />
      <Handle type="source" position={Position.Bottom} className="!bg-slate-400 !w-2 !h-2" />
      <Handle type="target" position={Position.Left} className="!bg-slate-400 !w-2 !h-2" />
      <Handle type="source" position={Position.Left} className="!bg-slate-400 !w-2 !h-2" />
      <Handle type="target" position={Position.Right} className="!bg-slate-400 !w-2 !h-2" />
      <Handle type="source" position={Position.Right} className="!bg-slate-400 !w-2 !h-2" />

      <div className="flex items-center justify-between gap-2 border-b border-slate-800 pb-1.5 mb-1.5">
        <span className={`text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded border font-semibold ${cfg.badge}`}>
          MODULE
        </span>
        <span className="text-[10px] font-mono text-slate-400">
          {data.count} items
        </span>
      </div>

      <div className="font-bold text-xs text-white">
        {data.label || cfg.label}
      </div>

      <div className="text-[11px] text-slate-400 mt-0.5">
        {data.description}
      </div>

      <div className="pt-2 mt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px]">
        <span className="text-slate-400 font-mono">
          {isExpanded ? 'Expanded' : 'Collapsed'}
        </span>
        <span className={`font-semibold flex items-center gap-1 ${cfg.iconColor}`}>
          {isExpanded ? (
            <><span>Collapse</span><ChevronUp className="w-3 h-3" /></>
          ) : (
            <><span>Expand ({data.count})</span><ChevronDown className="w-3 h-3" /></>
          )}
        </span>
      </div>
    </div>
  );
}

// 3. Detail Entity Node (Visible when module expanded or module tab focused)
function EntityCustomNode({ data, selected }) {
  const typeStyles = {
    component: {
      border: 'border-cyan-500/50',
      bg: 'bg-slate-900/95',
      badge: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30',
      text: 'text-cyan-200',
      dot: 'bg-cyan-400'
    },
    document: {
      border: 'border-purple-500/50',
      bg: 'bg-slate-900/95',
      badge: 'bg-purple-500/15 text-purple-300 border-purple-500/30',
      text: 'text-purple-200',
      dot: 'bg-purple-400'
    },
    procedure: {
      border: 'border-purple-500/50',
      bg: 'bg-slate-900/95',
      badge: 'bg-purple-500/15 text-purple-300 border-purple-500/30',
      text: 'text-purple-200',
      dot: 'bg-purple-400'
    },
    maintenance: {
      border: 'border-blue-500/50',
      bg: 'bg-slate-900/95',
      badge: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
      text: 'text-blue-200',
      dot: 'bg-blue-400'
    },
    inspection: {
      border: 'border-emerald-500/50',
      bg: 'bg-slate-900/95',
      badge: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
      text: 'text-emerald-200',
      dot: 'bg-emerald-400'
    },
    failure: {
      border: 'border-red-500/60',
      bg: 'bg-slate-900/95',
      badge: 'bg-red-500/20 text-red-300 border-red-500/40',
      text: 'text-red-200',
      dot: 'bg-red-400'
    }
  };

  const style = typeStyles[data.type] || {
    border: 'border-slate-700',
    bg: 'bg-slate-900/95',
    badge: 'bg-slate-800 text-slate-300 border-slate-700',
    text: 'text-white',
    dot: 'bg-slate-400'
  };

  return (
    <div className={`p-3 rounded-xl ${style.bg} ${style.border} border transition-all shadow-md min-w-[170px] max-w-[200px] ${
      selected ? 'ring-2 ring-white shadow-xl scale-105' : 'hover:border-slate-500'
    }`}>
      <Handle type="target" position={Position.Top} className="!bg-slate-400 !w-2 !h-2" />
      <Handle type="source" position={Position.Top} className="!bg-slate-400 !w-2 !h-2" />
      <Handle type="target" position={Position.Bottom} className="!bg-slate-400 !w-2 !h-2" />
      <Handle type="source" position={Position.Bottom} className="!bg-slate-400 !w-2 !h-2" />
      <Handle type="target" position={Position.Left} className="!bg-slate-400 !w-2 !h-2" />
      <Handle type="source" position={Position.Left} className="!bg-slate-400 !w-2 !h-2" />
      <Handle type="target" position={Position.Right} className="!bg-slate-400 !w-2 !h-2" />
      <Handle type="source" position={Position.Right} className="!bg-slate-400 !w-2 !h-2" />

      <div className="flex items-center justify-between gap-1 mb-1">
        <span className={`text-[9px] font-mono uppercase tracking-wider px-1.5 py-0.5 rounded border font-semibold ${style.badge}`}>
          {data.type}
        </span>
        <span className={`w-1.5 h-1.5 rounded-full ${style.dot}`}></span>
      </div>

      <div className={`font-bold text-xs truncate ${style.text}`}>
        {data.label}
      </div>

      <div className="text-[10px] text-slate-400 truncate mt-0.5 font-mono">
        {data.details}
      </div>
    </div>
  );
}

const nodeTypes = {
  centralAsset: CentralAssetNode,
  moduleHub: ModuleHubNode,
  entity: EntityCustomNode
};

// -------------------------------------------------------------
// MAIN KNOWLEDGE GRAPH CANVAS COMPONENT (WITH SEPARATE MODULES & NOT EXPANDED BY DEFAULT)
// -------------------------------------------------------------

export default function GraphCanvas({ 
  rawNodes = [], 
  rawLinks = [], 
  assetTag = 'P-101',
  onOpenDocViewer 
}) {
  // Selected Module Filter: 'all' (Modular Hubs View) or specific separated module
  const [selectedModule, setSelectedModule] = useState('all'); // 'all' | 'component' | 'document' | 'maintenance' | 'inspection' | 'failure'
  
  // By default, modules are COLLAPSED (not expanded!)
  const [expandedModules, setExpandedModules] = useState({
    component: false,
    document: false,
    maintenance: false,
    inspection: false,
    failure: false
  });

  const [selectedNodeData, setSelectedNodeData] = useState(null);
  const [evidenceDrawerOpen, setEvidenceDrawerOpen] = useState(false);

  // Group raw nodes by module type
  const modulesData = useMemo(() => {
    const compNodes = rawNodes.filter(n => n.type === 'component');
    const docNodes = rawNodes.filter(n => n.type === 'document' || n.type === 'procedure');
    const maintNodes = rawNodes.filter(n => n.type === 'maintenance');
    const inspNodes = rawNodes.filter(n => n.type === 'inspection');
    const failNodes = rawNodes.filter(n => n.type === 'failure');

    return {
      component: compNodes,
      document: docNodes,
      maintenance: maintNodes,
      inspection: inspNodes,
      failure: failNodes
    };
  }, [rawNodes]);

  // Toggle expansion of a specific module
  const handleToggleModule = (moduleKey) => {
    setExpandedModules(prev => ({
      ...prev,
      [moduleKey]: !prev[moduleKey]
    }));
  };

  // Construct Nodes & Edges dynamically based on selectedModule and expandedModules
  const { calculatedNodes, calculatedEdges } = useMemo(() => {
    const nodes = [];
    const edges = [];
    const centerX = 460;
    const centerY = 320;

    // 1. Central Asset Node always present
    const assetNode = rawNodes.find(n => n.type === 'asset' || n.id === `asset_${assetTag}`) || {
      id: `asset_${assetTag}`,
      label: assetTag === 'P-101' ? 'Centrifugal Water Injection Pump' : assetTag,
      type: 'asset',
      status: 'Operational',
      details: 'Central Machine Brain'
    };

    nodes.push({
      id: `asset_${assetTag}`,
      type: 'centralAsset',
      position: { x: centerX, y: centerY },
      data: {
        ...assetNode,
        tag: assetTag
      }
    });

    // 2. SEPARATED MODULES LOGIC
    if (selectedModule !== 'all') {
      // USER IS VIEWING A SINGLE SEPARATE MODULE ONLY!
      // This provides pristine clarity and zero clutter.
      const items = modulesData[selectedModule] || [];
      const count = items.length;

      items.forEach((item, idx) => {
        // Arrange items radially around the asset with generous whitespace
        let x = centerX;
        let y = centerY;

        if (selectedModule === 'component') {
          x = 180 + (idx * 160);
          y = centerY + 180;
        } else if (selectedModule === 'document') {
          x = 160 + (idx * 150);
          y = centerY - 190;
        } else if (selectedModule === 'maintenance') {
          x = centerX + 300;
          y = centerY - 60 + (idx * 140);
        } else if (selectedModule === 'inspection') {
          x = centerX - 300;
          y = centerY - 60 + (idx * 140);
        } else if (selectedModule === 'failure') {
          x = centerX;
          y = centerY + 200;
        }

        nodes.push({
          id: item.id,
          type: 'entity',
          position: { x, y },
          data: {
            ...item,
            tag: item.metadata?.work_order_number || item.metadata?.inspection_id || item.label
          }
        });
      });

      // Filter links relevant strictly to this module and central asset
      rawLinks.forEach((l, idx) => {
        const sourceExists = nodes.some(n => n.id === l.source);
        const targetExists = nodes.some(n => n.id === l.target);

        if (sourceExists && targetExists) {
          const isCritical = l.relationship === 'failed_component' || l.relationship === 'replaced_component';
          edges.push({
            id: `edge-${l.source}-${l.target}-${idx}`,
            source: l.source,
            target: l.target,
            label: l.relationship.replace(/_/g, ' '),
            labelStyle: { fill: isCritical ? '#f87171' : '#94a3b8', fontSize: 10, fontFamily: 'monospace', fontWeight: 600 },
            labelBgStyle: { fill: '#0f172a', fillOpacity: 0.9 },
            labelBgPadding: [4, 2],
            labelBgBorderRadius: 4,
            style: { stroke: isCritical ? '#ef4444' : '#38bdf8', strokeWidth: 1.5 },
            markerEnd: { type: MarkerType.ArrowClosed, color: isCritical ? '#ef4444' : '#38bdf8' }
          });
        }
      });

    } else {
      // DEFAULT VIEW: MODULAR HUBS AROUND THE ASSET (NOT EXPANDED BY DEFAULT!)
      const moduleConfigs = [
        { key: 'document', label: 'Documents & SOPs', count: modulesData.document.length, desc: 'OEM Manuals, SOPs & Specs', pos: { x: centerX - 10, y: centerY - 200 }, rel: 'governed by' },
        { key: 'component', label: 'Components Module', count: modulesData.component.length, desc: 'Bearings, Seals, Impeller & Shaft', pos: { x: centerX - 10, y: centerY + 200 }, rel: 'contains' },
        { key: 'maintenance', label: 'Maintenance Module', count: modulesData.maintenance.length, desc: 'Work Orders & Overhaul Records', pos: { x: centerX + 340, y: centerY - 20 }, rel: 'maintained by' },
        { key: 'inspection', label: 'Inspection Module', count: modulesData.inspection.length, desc: 'Condition Monitoring & Vibration', pos: { x: centerX - 340, y: centerY - 20 }, rel: 'observes' },
        { key: 'failure', label: 'Failure Analysis', count: modulesData.failure.length, desc: 'Root Cause & Incident Reports', pos: { x: centerX + 300, y: centerY + 180 }, rel: 'experienced' }
      ];

      moduleConfigs.forEach((m) => {
        const isExp = expandedModules[m.key];
        const hubId = `hub_${m.key}`;

        // Module Hub Node
        nodes.push({
          id: hubId,
          type: 'moduleHub',
          position: m.pos,
          data: {
            id: hubId,
            moduleType: m.key,
            label: m.label,
            count: m.count,
            description: m.desc,
            isExpanded: isExp
          }
        });

        // Edge between Asset and Module Hub
        edges.push({
          id: `e-asset-${hubId}`,
          source: `asset_${assetTag}`,
          target: hubId,
          label: m.rel,
          labelStyle: { fill: '#94a3b8', fontSize: 10, fontFamily: 'monospace', fontWeight: 600 },
          labelBgStyle: { fill: '#0f172a', fillOpacity: 0.9 },
          labelBgPadding: [4, 2],
          labelBgBorderRadius: 4,
          style: { stroke: '#0284c7', strokeWidth: 1.5 },
          markerEnd: { type: MarkerType.ArrowClosed, color: '#0284c7' }
        });

        // IF USER EXPLICITLY EXPANDED THIS MODULE:
        if (isExp) {
          const subItems = modulesData[m.key] || [];
          subItems.forEach((sub, sIdx) => {
            let sx = m.pos.x;
            let sy = m.pos.y;

            if (m.key === 'document') {
              sx = m.pos.x - 240 + (sIdx * 150);
              sy = m.pos.y - 140;
            } else if (m.key === 'component') {
              sx = m.pos.x - 240 + (sIdx * 150);
              sy = m.pos.y + 140;
            } else if (m.key === 'maintenance') {
              sx = m.pos.x + 220;
              sy = m.pos.y - 40 + (sIdx * 110);
            } else if (m.key === 'inspection') {
              sx = m.pos.x - 220;
              sy = m.pos.y - 40 + (sIdx * 110);
            } else if (m.key === 'failure') {
              sx = m.pos.x + 180;
              sy = m.pos.y + 100;
            }

            nodes.push({
              id: sub.id,
              type: 'entity',
              position: { x: sx, y: sy },
              data: {
                ...sub,
                tag: sub.metadata?.work_order_number || sub.metadata?.inspection_id || sub.label
              }
            });

            // Edge from Module Hub to Sub-Entity
            edges.push({
              id: `e-${hubId}-${sub.id}`,
              source: hubId,
              target: sub.id,
              style: { stroke: '#64748b', strokeWidth: 1.2, strokeDasharray: '3,3' },
              markerEnd: { type: MarkerType.ArrowClosed, color: '#64748b', width: 10, height: 10 }
            });
          });
        }
      });
    }

    return { calculatedNodes: nodes, calculatedEdges: edges };
  }, [rawNodes, rawLinks, assetTag, selectedModule, expandedModules, modulesData]);

  const [nodes, setNodes, onNodesChange] = useNodesState(calculatedNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(calculatedEdges);

  useEffect(() => {
    setNodes(calculatedNodes);
    setEdges(calculatedEdges);
    if (calculatedNodes.length > 0 && !selectedNodeData) {
      setSelectedNodeData(calculatedNodes[0].data);
    }
  }, [calculatedNodes, calculatedEdges]);

  // Click on Node: if it's a module hub, toggle expansion; otherwise inspect
  const onNodeClick = useCallback((event, node) => {
    if (node.type === 'moduleHub') {
      handleToggleModule(node.data.moduleType);
      setSelectedNodeData({
        label: node.data.label,
        type: node.data.moduleType,
        details: `${node.data.count} industrial records verified in this module category.`,
        metadata: {
          category: node.data.label,
          total_records: node.data.count,
          status: 'Grounded Records'
        }
      });
    } else {
      setSelectedNodeData(node.data);
    }
  }, []);

  // Collapse / Expand all toggle
  const allCollapsed = Object.values(expandedModules).every(v => !v);
  const handleToggleExpandAll = () => {
    const nextState = allCollapsed;
    setExpandedModules({
      component: nextState,
      document: nextState,
      maintenance: nextState,
      inspection: nextState,
      failure: nextState
    });
  };

  return (
    <div className="space-y-4">
      {/* 1. SEPARATE MODULES TOOLBAR */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-2xl bg-slate-900 border border-slate-800 text-xs shadow-md">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-brand-400" />
          <span className="font-bold text-white tracking-tight">Separate Knowledge Modules:</span>
        </div>

        {/* Module Switcher Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto py-0.5">
          {[
            { id: 'all', label: 'All Modules (Modular View)' },
            { id: 'component', label: 'Components' },
            { id: 'document', label: 'Documents & SOPs' },
            { id: 'maintenance', label: 'Maintenance' },
            { id: 'inspection', label: 'Inspections' },
            { id: 'failure', label: 'Failures' },
          ].map((tab) => {
            const isActive = selectedModule === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => {
                  setSelectedModule(tab.id);
                  if (tab.id !== 'all') {
                    // When focusing a single module, inspect its first item
                    const first = modulesData[tab.id]?.[0];
                    if (first) setSelectedNodeData(first);
                  }
                }}
                className={`px-3 py-1.5 rounded-xl font-semibold transition-all whitespace-nowrap text-xs ${
                  isActive
                    ? 'bg-brand-500 text-white shadow-sm shadow-brand-500/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Expand / Collapse Toggle for Modular Mode */}
        {selectedModule === 'all' && (
          <button
            onClick={handleToggleExpandAll}
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-750 text-slate-300 hover:text-white border border-slate-700/80 font-mono text-[11px] font-medium transition-all flex items-center gap-1.5"
          >
            {allCollapsed ? <Folder className="w-3.5 h-3.5 text-brand-400" /> : <FolderOpen className="w-3.5 h-3.5 text-purple-400" />}
            <span>{allCollapsed ? 'Expand All' : 'Collapse All (Default)'}</span>
          </button>
        )}
      </div>

      {/* 2. MAIN GRAPH CANVAS (NOT EXPANDED BY DEFAULT & SEPARATE MODULES) */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Canvas */}
        <div className="lg:col-span-3 h-[560px] rounded-2xl bg-slate-950 border border-slate-800 relative overflow-hidden shadow-inner">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            minZoom={0.2}
            maxZoom={1.5}
            attributionPosition="bottom-left"
          >
            <Background color="#1e293b" gap={24} size={1} />
            <Controls className="!bg-slate-900 !border-slate-800 !text-white [&>button]:!bg-slate-900 [&>button]:!border-slate-800 [&>button]:!fill-white [&>button:hover]:!bg-slate-800" />
            <MiniMap 
              className="!bg-slate-900 !border-slate-800 !rounded-lg overflow-hidden" 
              nodeColor={(n) => {
                if (n.type === 'centralAsset') return '#0284c7';
                if (n.type === 'moduleHub') return '#8b5cf6';
                if (n.data?.type === 'failure') return '#ef4444';
                if (n.data?.type === 'inspection') return '#10b981';
                return '#64748b';
              }}
            />
          </ReactFlow>

          {/* Calm Status Hint */}
          <div className="absolute bottom-3 left-3 z-10 bg-slate-900/90 backdrop-blur-sm border border-slate-800 px-3 py-1.5 rounded-lg flex items-center gap-3 text-[10px] text-slate-400 font-mono">
            <span>By default, modules are kept collapsed to eliminate clutter. Click any module to expand.</span>
          </div>
        </div>

        {/* 3. RIGHT-SIDE INSPECTOR PANEL */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between space-y-4 shadow-xl">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5 text-brand-400" />
                <span>Entity Inspector</span>
              </span>
              {selectedNodeData && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded font-semibold uppercase bg-slate-800 text-brand-400">
                  {selectedNodeData.type || 'Module'}
                </span>
              )}
            </div>

            {selectedNodeData ? (
              <div className="space-y-4 text-xs">
                <div>
                  <h3 className="font-bold text-sm text-white">
                    {selectedNodeData.label}
                  </h3>
                  <p className="text-slate-400 mt-1 text-[11px] leading-relaxed">
                    {selectedNodeData.details}
                  </p>
                </div>

                {/* Verified Attributes */}
                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold block">
                    Verified Attributes
                  </span>
                  <div className="space-y-1 font-mono text-[11px] text-slate-300">
                    {Object.entries(selectedNodeData.metadata || {}).map(([k, v]) => (
                      <div key={k} className="flex items-center justify-between py-0.5 border-b border-slate-900 last:border-0">
                        <span className="text-slate-400 capitalize">{k.replace(/_/g, ' ')}:</span>
                        <span className="text-slate-200 truncate max-w-[130px] font-semibold">{String(v || 'N/A')}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-12 text-center text-slate-400 text-xs">
                Select any module or node to inspect details.
              </div>
            )}
          </div>

          {/* Action Footer */}
          {selectedNodeData && (
            <div className="pt-3 border-t border-slate-800 space-y-2">
              <button
                onClick={() => setEvidenceDrawerOpen(true)}
                className="w-full py-2 rounded-lg bg-brand-500 hover:bg-brand-600 text-white font-semibold text-xs flex items-center justify-center gap-1.5 transition-all shadow-md shadow-brand-500/20"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>View Evidence Chain</span>
              </button>

              {(selectedNodeData.type === 'document' || selectedNodeData.type === 'procedure') && (
                <button
                  onClick={() => onOpenDocViewer && onOpenDocViewer(selectedNodeData.metadata?.document_id || selectedNodeData.id)}
                  className="w-full py-2 rounded-lg bg-slate-800 hover:bg-slate-750 text-slate-200 font-medium text-xs flex items-center justify-center gap-1.5 transition-all border border-slate-700"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>Open Document Chunks</span>
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Evidence Drawer */}
      <EvidenceDrawer
        isOpen={evidenceDrawerOpen}
        onClose={() => setEvidenceDrawerOpen(false)}
        evidenceData={
          selectedNodeData ? [{
            document_name: selectedNodeData.label,
            date: selectedNodeData.metadata?.date || 'Historical Record',
            page: '1',
            status: selectedNodeData.status || 'Verified',
            excerpt: selectedNodeData.details || selectedNodeData.label
          }] : null
        }
        onOpenDocViewer={onOpenDocViewer}
      />
    </div>
  );
}
