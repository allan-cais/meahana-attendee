import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { Bot, RefreshCw } from 'lucide-react';
import { MeetingConfig, MeetingBot, ScorecardResponse } from './types';
import Sidebar from './components/Sidebar';
import ConfigScreen from './components/ConfigScreen';
import ScorecardScreen from './components/ScorecardScreen';
import apiService from './services/api';

const App: React.FC = () => {
  const [bots, setBots] = useState<MeetingBot[]>([]);
  const [selectedBotId, setSelectedBotId] = useState<number | null>(() => {
    const saved = localStorage.getItem('selectedBotId');
    return saved ? parseInt(saved, 10) : null;
  });
  const [isCreatingNewBot, setIsCreatingNewBot] = useState(false);
  const [config, setConfig] = useState<MeetingConfig>({
    meeting_url: '',
    bot_name: '',
    join_at: undefined
  });
  
  // Store scorecard data for ALL meetings to prevent re-fetching
  const [scorecardCache, setScorecardCache] = useState<Map<number, ScorecardResponse>>(new Map());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Use refs to track active polling intervals and prevent memory leaks
  const pollingIntervals = useRef<Map<number, NodeJS.Timeout>>(new Map());
  const isMounted = useRef(true);
  const fetchInProgress = useRef<Set<number>>(new Set());

  // Memoize selected bot to prevent unnecessary re-renders
  const selectedBot = useMemo(() => 
    bots.find(bot => bot.id === selectedBotId), 
    [bots, selectedBotId]
  );

  // Get scorecard data for current meeting from cache
  const currentScorecardData = useMemo(() => 
    selectedBotId ? scorecardCache.get(selectedBotId) : null,
    [selectedBotId, scorecardCache]
  );

  // Cleanup function for polling intervals
  const cleanupPolling = useCallback((botId?: number) => {
    if (botId) {
      const interval = pollingIntervals.current.get(botId);
      if (interval) {
        clearInterval(interval);
        pollingIntervals.current.delete(botId);
      }
    } else {
      // Cleanup all intervals
      pollingIntervals.current.forEach(interval => clearInterval(interval));
      pollingIntervals.current.clear();
    }
  }, []);

  // Enhanced scorecard fetching with caching and meeting-specific data
  const fetchScorecardData = useCallback(async (meetingId?: number) => {
    const targetMeetingId = meetingId || selectedBotId;
    
    if (!targetMeetingId) {
      return; // No meeting ID
    }
    
    if (fetchInProgress.current.has(targetMeetingId)) {
      return; // Already fetching this specific meeting
    }
    
    fetchInProgress.current.add(targetMeetingId);
    
    if (targetMeetingId === selectedBotId) {
      setLoading(true);
      setError(null);
    }

    try {
      const data = await apiService.getMeetingScorecard(targetMeetingId);
      
      // Cache the scorecard data for this meeting
      setScorecardCache(prev => new Map(prev).set(targetMeetingId, data));
      
      // If scorecard is still processing, retry after a delay
      if (data.status === 'processing') {
        setTimeout(() => {
          if (isMounted.current) {
            fetchScorecardData(targetMeetingId);
          }
        }, 5000); // Wait 5 seconds before retry
      }
      
    } catch (err) {
      if (targetMeetingId === selectedBotId) {
        setError(err instanceof Error ? err.message : 'Failed to fetch scorecard data');
      }
    } finally {
      fetchInProgress.current.delete(targetMeetingId);
      if (targetMeetingId === selectedBotId) {
        setLoading(false);
      }
    }
  }, [selectedBotId]);

  // Enhanced status polling with better error handling and real-time updates
  const startStatusPolling = useCallback((botId: number) => {
    // Clear any existing interval for this bot
    cleanupPolling(botId);
    
    const interval = setInterval(async () => {
      if (!isMounted.current) return;
      
      try {
        const statusResult = await apiService.pollBotStatus(botId);
        
        if (statusResult.status_updated) {
          // Update bot status in real-time
          setBots(prev => prev.map(bot => 
            bot.id === botId 
              ? { ...bot, status: statusResult.new_status, updated_at: new Date().toISOString() }
              : bot
          ));
          
          // Handle status-specific actions
          if (statusResult.new_status === 'COMPLETED') {
            cleanupPolling(botId);
            
            // Trigger analysis in background
            setTimeout(async () => {
              try {
                await apiService.triggerAnalysis(botId);
                
                // Wait a bit more then fetch the scorecard
                setTimeout(() => {
                  if (isMounted.current) {
                    fetchScorecardData(botId);
                  }
                }, 3000);
              } catch (error) {
                // Silently handle analysis trigger errors
              }
            }, 2000);
            
          } else if (statusResult.new_status === 'FAILED') {
            cleanupPolling(botId);
          }
        }
        
      } catch (error) {
        // Silently handle polling errors
      }
    }, 5000); // Poll every 5 seconds for more responsive updates
    
    pollingIntervals.current.set(botId, interval);
  }, [cleanupPolling, fetchScorecardData]);

  // Enhanced bot status refresh with real-time updates
  const refreshBotStatus = useCallback(async (botId?: number) => {
    const targetBotId = botId || selectedBotId;
    if (!targetBotId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const statusResult = await apiService.pollBotStatus(targetBotId);
      
      if (statusResult.status_updated) {
        // Update bot in the list
        setBots(prev => prev.map(bot => 
          bot.id === targetBotId 
            ? { ...bot, status: statusResult.new_status, updated_at: new Date().toISOString() }
            : bot
        ));
        
        // Handle status changes
        if (statusResult.new_status === 'PENDING' || statusResult.new_status === 'STARTED') {
          startStatusPolling(targetBotId);
        }
      }
      
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to refresh bot status');
    } finally {
      setLoading(false);
    }
  }, [selectedBotId, startStatusPolling]);

  // Create new bot
  const handleNewBot = () => {
    setSelectedBotId(null);
    setIsCreatingNewBot(true);
    setConfig({ meeting_url: '', bot_name: '', join_at: undefined });
    setError(null);
  };

  // Handle bot creation
  const handleConfigSubmit = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await apiService.createBot(config);
      
      // Add the new bot to the list
      const newBot: MeetingBot = {
        id: result.id,
        meeting_url: result.meeting_url,
        bot_id: result.bot_id,
        status: result.status as MeetingBot['status'],
        meeting_metadata: result.meeting_metadata,
        created_at: result.created_at,
        updated_at: result.updated_at
      };
      
      setBots(prev => [newBot, ...prev]); // Add to beginning for newest first
      setSelectedBotId(result.id);
      localStorage.setItem('selectedBotId', result.id.toString());
      setIsCreatingNewBot(false);
      
      // Start polling for status updates
      if (result.status === 'PENDING' || result.status === 'STARTED') {
        startStatusPolling(result.id);
      } else if (result.status === 'COMPLETED') {
        setTimeout(() => fetchScorecardData(result.id), 1000);
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bot creation failed');
    } finally {
      setLoading(false);
    }
  }, [config, startStatusPolling, fetchScorecardData]);

  // Enhanced bot selection with proper data management
  const handleBotSelect = useCallback((botId: number) => {
    setSelectedBotId(botId);
    localStorage.setItem('selectedBotId', botId.toString());
    setIsCreatingNewBot(false);
    
    const bot = bots.find(b => b.id === botId);
    if (bot) {
      // Set config from bot metadata
      setConfig({
        meeting_url: bot.meeting_url,
        bot_name: bot.meeting_metadata.bot_name,
        join_at: bot.meeting_metadata.join_at
      });
      
      // Check if we already have scorecard data for this meeting
      const existingScorecard = scorecardCache.get(botId);
      
      if (bot.status === 'COMPLETED' && !existingScorecard) {
        fetchScorecardData(botId);
      } else if (bot.status === 'PENDING' || bot.status === 'STARTED') {
        startStatusPolling(botId);
      }
    }
  }, [bots, scorecardCache, fetchScorecardData, startStatusPolling]);

  // Handle bot deletion
  const handleDeleteBot = useCallback(async (botId: number) => {
    try {
      await apiService.deleteBot(botId);
      
      // Cleanup polling for this bot
      cleanupPolling(botId);
      
      // Remove scorecard from cache
      setScorecardCache(prev => {
        const newCache = new Map(prev);
        newCache.delete(botId);
        return newCache;
      });
      
      // Remove bot from local state
      setBots(prev => prev.filter(bot => bot.id !== botId));
      
      // If the deleted bot was selected, clear selection
      if (selectedBotId === botId) {
        setSelectedBotId(null);
        localStorage.removeItem('selectedBotId');
        setConfig({ meeting_url: '', bot_name: '', join_at: undefined });
      }
      
    } catch (error) {
      alert(`Failed to delete bot: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }, [selectedBotId, cleanupPolling]);

  // Check if a bot has been stuck in the same status for too long
  const isBotStuck = useCallback((bot: MeetingBot) => {
    const now = new Date();
    const updatedAt = new Date(bot.updated_at);
    const timeDiff = now.getTime() - updatedAt.getTime();
    const minutesDiff = timeDiff / (1000 * 60);
    
    // Consider a bot stuck if it's been in pending/started status for more than 30 minutes
    return (bot.status === 'PENDING' || bot.status === 'STARTED') && minutesDiff > 30;
  }, []);

  // Load bots from API on component mount
  useEffect(() => {
    const loadBots = async () => {
      try {
        const botsData = await apiService.getBots();
        setBots(botsData);
        
        // Auto-select most recent bot if none selected
        if (botsData.length > 0 && !selectedBotId) {
          const mostRecentBot = botsData[0];
          setSelectedBotId(mostRecentBot.id);
          localStorage.setItem('selectedBotId', mostRecentBot.id.toString());
          setConfig({
            meeting_url: mostRecentBot.meeting_url,
            bot_name: mostRecentBot.meeting_metadata.bot_name,
            join_at: mostRecentBot.meeting_metadata.join_at
          });
          
          // If bot is completed, fetch scorecard
          if (mostRecentBot.status === 'COMPLETED') {
            setTimeout(() => fetchScorecardData(mostRecentBot.id), 100);
          }
        }
        
        // Fetch scorecard data for all completed bots
        botsData.forEach((bot, index) => {
          if (bot.status === 'COMPLETED') {
            setTimeout(() => {
              fetchScorecardData(bot.id);
            }, 100 * (index + 1)); // Stagger requests with shorter delays
          }
        });
        
        // Start polling for active bots
        botsData.forEach(bot => {
          if (bot.status === 'PENDING' || bot.status === 'STARTED') {
            startStatusPolling(bot.id);
          }
        });
        
      } catch (error) {
        // Silently handle bot loading errors
      }
    };
    
    loadBots();
  }, [selectedBotId, fetchScorecardData, startStatusPolling]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMounted.current = false;
      cleanupPolling();
    };
  }, [cleanupPolling]);

  // Determine which screen to show
  const shouldShowReport = selectedBot && selectedBot.status === 'COMPLETED' && currentScorecardData && currentScorecardData.scorecard;
  const shouldShowConfig = selectedBot && selectedBot.status !== 'COMPLETED';

  return (
    <div className="min-h-screen bg-gray-50 text-black">
      <div className="flex h-screen">
        {/* Sidebar */}
        <Sidebar
          bots={bots}
          selectedBotId={selectedBotId}
          onBotSelect={handleBotSelect}
          onNewBot={handleNewBot}
          onDeleteBot={handleDeleteBot}
          reportData={currentScorecardData}
          scorecardCache={scorecardCache}
          isBotStuck={isBotStuck}
        />

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <header className="bg-white border-b border-gray-200 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Bot className="w-6 h-6 text-primary-600" />
                <h1 className="text-xl font-bold text-black">Meeting Bot Dashboard</h1>
                {selectedBot && (
                  <div className="flex items-center gap-2">
                    <span className="text-gray-600">• {selectedBot.meeting_metadata.bot_name}</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      selectedBot.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                      selectedBot.status === 'STARTED' ? 'bg-blue-100 text-blue-800' :
                      selectedBot.status === 'PENDING' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {selectedBot.status === 'COMPLETED' ? 'Completed' :
                       selectedBot.status === 'STARTED' ? 'In Meeting' :
                       selectedBot.status === 'PENDING' ? 'Creating...' :
                       'Failed'}
                    </span>
                  </div>
                )}
              </div>
              
              {/* Action Buttons */}
              {selectedBotId && selectedBot && selectedBot.status === 'COMPLETED' && 
               (!currentScorecardData || !currentScorecardData.scorecard) && (
                <div className="flex gap-2">
                  <button
                    onClick={() => fetchScorecardData()}
                    disabled={loading}
                    className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-4 py-2 rounded-lg transition-colors duration-200 flex items-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    {loading ? 'Fetching...' : 'Fetch Scorecard'}
                  </button>
                </div>
              )}
            </div>
          </header>

          {/* Content Area */}
          <main className="flex-1 p-6 overflow-y-auto">
            {isCreatingNewBot ? (
              <ConfigScreen
                config={config}
                setConfig={setConfig}
                onSubmit={handleConfigSubmit}
                loading={loading}
                error={error}
              />
            ) : !selectedBotId ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Bot className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h2 className="text-xl font-semibold text-gray-600 mb-2">No Bot Selected</h2>
                  <p className="text-gray-500">Select a bot from the sidebar or create a new one</p>
                </div>
              </div>
            ) : shouldShowReport ? (
              <ScorecardScreen
                scorecardData={currentScorecardData}
                config={config}
                onRefresh={() => fetchScorecardData()}
                onTriggerAnalysis={async () => {
                  if (selectedBotId) {
                    try {
                      setLoading(true);
                      await apiService.triggerAnalysis(selectedBotId);
                      // Wait a bit then fetch the updated scorecard
                      setTimeout(() => {
                        if (isMounted.current) {
                          fetchScorecardData(selectedBotId);
                        }
                      }, 3000);
                    } catch (error) {
                      setError(error instanceof Error ? error.message : 'Failed to trigger analysis');
                    } finally {
                      setLoading(false);
                    }
                  }
                }}
                loading={loading}
                error={error}
              />
            ) : shouldShowConfig ? (
              <ConfigScreen
                config={config}
                setConfig={setConfig}
                onSubmit={handleConfigSubmit}
                loading={loading}
                error={error}
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Bot className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h2 className="text-xl font-semibold text-gray-600 mb-2">Bot Ready</h2>
                  <p className="text-gray-500">Configure your bot to get started</p>
                </div>
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
};

export default App; 