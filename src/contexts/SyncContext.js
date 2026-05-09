import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';

const SyncContext = createContext();
const API = '/api';

export const SyncProvider = ({ children }) => {
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState(null);
  const [syncStats, setSyncStats] = useState({ imported: 0, updated: 0, processed: 0, currentBatch: 0, totalBatches: 0 });
  const [syncProgress, setSyncProgress] = useState(0);
  const [lastSyncResult, setLastSyncResult] = useState(null);
  
  const pollTimer = useRef(null);

  const fetchSyncStatus = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/scraper/sync/status`, { withCredentials: true });
      
      if (data.status === 'running') {
        setIsSyncing(true);
        setSyncProgress(Math.round((data.current_page / (data.total_pages || 1)) * 100));
        setSyncStats({
          imported: data.imported,
          updated: data.updated,
          processed: data.processed,
          currentBatch: data.current_page,
          totalBatches: data.total_pages
        });
      } else if (data.status === 'completed') {
        if (isSyncing) {
          setLastSyncResult({ added: data.imported, updated: data.updated });
        }
        setIsSyncing(false);
        setSyncProgress(100);
      } else {
        setIsSyncing(false);
      }
    } catch (err) {
      console.error("Sync status fetch failed:", err);
    }
  }, [isSyncing]);

  const startSync = async () => {
    setIsSyncing(true);
    setSyncProgress(0);
    setLastSyncResult(null);
    try {
      await axios.post(`${API}/scraper/sync/start`, {}, { withCredentials: true });
    } catch (err) {
      setIsSyncing(false);
      throw err;
    }
  };

  useEffect(() => {
    if (isSyncing) {
      pollTimer.current = setInterval(fetchSyncStatus, 3000);
    } else {
      clearInterval(pollTimer.current);
      // Final check on mount if sync was already running
      fetchSyncStatus();
    }
    return () => clearInterval(pollTimer.current);
  }, [isSyncing, fetchSyncStatus]);

  return (
    <SyncContext.Provider value={{
      isSyncing,
      syncStatus,
      syncStats,
      syncProgress,
      lastSyncResult,
      startSync,
      refreshStatus: fetchSyncStatus
    }}>
      {children}
    </SyncContext.Provider>
  );
};

export const useSync = () => {
  const context = useContext(SyncContext);
  if (!context) throw new Error('useSync must be used within a SyncProvider');
  return context;
};
