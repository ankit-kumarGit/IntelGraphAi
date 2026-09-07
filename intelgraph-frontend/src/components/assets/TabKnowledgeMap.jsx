import React, { useState, useEffect } from 'react';
import { Network } from 'lucide-react';
import { api } from '../../services/api';
import GraphCanvas from '../knowledge/GraphCanvas';

export default function TabKnowledgeMap({ assetTag, onOpenDocViewer }) {
  const [mapData, setMapData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function loadMap() {
      setLoading(true);
      try {
        const data = await api.getKnowledgeMap(assetTag);
        if (isMounted) setMapData(data);
      } catch (err) {
        console.error('Failed to load knowledge map:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadMap();
    return () => { isMounted = false; };
  }, [assetTag]);

  if (loading) {
    return (
      <div className="p-16 text-center text-slate-400">
        <div className="w-8 h-8 border-2 border-brand-400 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
        Constructing interactive Knowledge Brain for {assetTag}...
      </div>
    );
  }

  return (
    <GraphCanvas
      rawNodes={mapData.nodes}
      rawLinks={mapData.links}
      assetTag={assetTag}
      onOpenDocViewer={onOpenDocViewer}
    />
  );
}
