import React, { useState, useEffect } from 'react';
import { Bot } from 'lucide-react';
import { MeetingConfig, MeetingBot, ReportData } from './types';
import Sidebar from './components/Sidebar';
import ConfigScreen from './components/ConfigScreen';
import ScorecardScreen from './components/ScorecardScreen';
import apiService from './services/api';

const App: React.FC = () => {
  const [bots, setBots] = useState<MeetingBot[]>([]);
  const [selectedBotId, setSelectedBotId] = useState<number | null>(() => {
    // Try to restore selected bot ID from localStorage
    const saved = localStorage.getItem('selectedBotId');
    return saved ? parseInt(saved, 10) : null;
  });
  const [isCreatingNewBot, setIsCreatingNewBot] = useState(false);
  const [config, setConfig] = useState<MeetingConfig>({
    meeting_url: '',
    bot_name: '',
    join_at: undefined
  });
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

  const selectedBot = bots.find(bot => bot.id === selectedBotId);

  // Create new bot
  const handleNewBot = () => {
    setSelectedBotId(null);
    setIsCreatingNewBot(true);
    setConfig({ meeting_url: '', bot_name: '', join_at: undefined });
    setReportData(null);
    setError(null);
  };

  // Handle bot creation
  const handleConfigSubmit = async () => {
    setLoading(true);
    setError(null);

    try {
      console.log('Creating bot with config:', config);
      const result = await apiService.createBot(config);
      console.log('Bot created successfully:', result);
      
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
      
      setBots(prev => [...prev, newBot]);
      setSelectedBotId(result.id);
      localStorage.setItem('selectedBotId', result.id.toString()); // Save to localStorage
      setIsCreatingNewBot(false);
      
      // If bot is completed, fetch report data immediately
      if (result.status === 'completed') {
        console.log('Bot is completed, fetching report data...');
        fetchReportData();
      }
      // Start polling for status updates if bot is pending
      else if (result.status === 'pending') {
        startStatusPolling(result.id);
      }
      
    } catch (err) {
      console.log('Error in handleConfigSubmit:', err);
      setError(err instanceof Error ? err.message : 'Bot creation failed');
    } finally {
      setLoading(false);
    }
  };

  // Poll for bot status updates
  const startStatusPolling = (botId: number) => {
    console.log(`Starting status polling for bot ${botId}`);
    
    const interval = setInterval(async () => {
      try {
        console.log(`Polling status for bot ${botId}...`);
        
        // Check if bot status has changed
        const report = await apiService.getReport(botId);
        console.log(`Bot ${botId} status: ${report.status}, reports:`, report.reports);
        
        if (report.status === 'completed') {
          console.log(`Bot ${botId} completed, stopping polling`);
          clearInterval(interval);
          setPollingInterval(null);
          
          // Update bot status
          setBots(prev => prev.map(bot => 
            bot.id === botId 
              ? { ...bot, status: 'completed', updated_at: new Date().toISOString() }
              : bot
          ));
          
          // If report is available, set it
          if (report.reports && report.reports.length > 0) {
            console.log(`Setting report data for completed bot ${botId}:`, report);
            setReportData(report);
          } else {
            console.log(`Bot ${botId} completed but no reports yet, starting report polling...`);
            // Start polling for the actual report
            try {
              const polledData = await apiService.pollForReport(botId);
              console.log(`Report polling successful for bot ${botId}:`, polledData);
              setReportData(polledData);
            } catch (pollError) {
              console.error(`Report polling failed for bot ${botId}:`, pollError);
            }
          }
        } else if (report.status === 'failed') {
          console.log(`Bot ${botId} failed, stopping polling`);
          clearInterval(interval);
          setPollingInterval(null);
          
          // Update bot status
          setBots(prev => prev.map(bot => 
            bot.id === botId 
              ? { ...bot, status: 'failed', updated_at: new Date().toISOString() }
              : bot
          ));
        }
        // Continue polling for other statuses (pending, started)
        
      } catch (error) {
        console.error(`Status polling error for bot ${botId}:`, error);
        // Don't stop polling on error, just log it
      }
    }, 5000); // Poll every 5 seconds

    setPollingInterval(interval);
  };

  // Fetch report data
  const fetchReportData = async () => {
    if (!selectedBotId) return;
    
    setLoading(true);
    setError(null);

    try {
      const data = await apiService.getReport(selectedBotId);
      setReportData(data);
      
      // If bot is completed but we don't have reports yet, start polling
      if (data.status === 'completed' && (!data.reports || data.reports.length === 0)) {
        const polledData = await apiService.pollForReport(selectedBotId);
        setReportData(polledData);
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch report data');
    } finally {
      setLoading(false);
    }
  };

  // Refresh current bot status and restart polling if needed
  const refreshBotStatus = async () => {
    if (!selectedBotId) return;
    
    try {
      const bot = await apiService.getBot(selectedBotId);
      
      // Update bot in the list
      setBots(prev => prev.map(b => b.id === selectedBotId ? bot : b));
      
      // If bot is still pending/started, restart polling
      if (bot.status === 'pending' || bot.status === 'started') {
        console.log(`Bot ${selectedBotId} is still ${bot.status}, restarting polling...`);
        if (pollingInterval) {
          clearInterval(pollingInterval);
          setPollingInterval(null);
        }
        startStatusPolling(selectedBotId);
      }
      
      // If bot is completed, fetch report
      if (bot.status === 'completed') {
        fetchReportData();
      }
      
    } catch (error) {
      console.error('Failed to refresh bot status:', error);
    }
  };

  // Manually trigger analysis for a meeting
  const triggerAnalysis = async () => {
    if (!selectedBotId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      console.log(`Manually triggering analysis for meeting ${selectedBotId}`);
      await apiService.triggerAnalysis(selectedBotId);
      
      // Wait a moment then fetch the report
      setTimeout(() => {
        fetchReportData();
      }, 2000);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to trigger analysis');
    } finally {
      setLoading(false);
    }
  };

  // Get webhook debug information
  const checkWebhookStatus = async () => {
    try {
      console.log('Checking webhook status...');
      const debugInfo = await apiService.getWebhookDebugInfo();
      console.log('Webhook debug info:', debugInfo);
      
      // Show debug info in an alert for now (you could make this a modal)
      alert(`Webhook Debug Info:\n\nMeetings: ${JSON.stringify(debugInfo.meetings, null, 2)}\n\nWebhook Events: ${JSON.stringify(debugInfo.webhook_events, null, 2)}`);
      
    } catch (error) {
      console.error('Failed to check webhook status:', error);
      alert('Failed to check webhook status. See console for details.');
    }
  };

  // Handle bot selection
  const handleBotSelect = (botId: number) => {
    setSelectedBotId(botId);
    localStorage.setItem('selectedBotId', botId.toString()); // Save to localStorage
    setIsCreatingNewBot(false);
    const bot = bots.find(b => b.id === botId);
    if (bot) {
      // Set config from bot metadata
      setConfig({
        meeting_url: bot.meeting_url,
        bot_name: bot.meeting_metadata.bot_name,
        join_at: bot.meeting_metadata.join_at
      });
      
      // Clear any existing report data
      setReportData(null);
    }
  };

  // Auto-fetch report data when bot is completed
  useEffect(() => {
    if (selectedBot && selectedBot.status === 'completed') {
      fetchReportData();
    }
  }, [selectedBotId]);

  // Load bots from API on component mount
  useEffect(() => {
    const loadBots = async () => {
      try {
        const botsData = await apiService.getBots();
        setBots(botsData);
        
        // If we have bots and none is selected, select the most recent one
        if (botsData.length > 0 && !selectedBotId) {
          const mostRecentBot = botsData[0]; // Already sorted by created_at desc
          setSelectedBotId(mostRecentBot.id);
          localStorage.setItem('selectedBotId', mostRecentBot.id.toString());
          setConfig({
            meeting_url: mostRecentBot.meeting_url,
            bot_name: mostRecentBot.meeting_metadata.bot_name,
            join_at: mostRecentBot.meeting_metadata.join_at
          });
          
          // If the bot is completed, fetch its report
          if (mostRecentBot.status === 'completed') {
            setReportData(null); // Clear any existing data
            setTimeout(() => fetchReportData(), 100); // Small delay to ensure state is set
          }
        }
        
        // If we have a saved selectedBotId, verify it still exists and restore state
        if (selectedBotId && botsData.length > 0) {
          const savedBot = botsData.find(bot => bot.id === selectedBotId);
          if (savedBot) {
            console.log(`Restoring saved bot ${selectedBotId}:`, savedBot);
            setConfig({
              meeting_url: savedBot.meeting_url,
              bot_name: savedBot.meeting_metadata.bot_name,
              join_at: savedBot.meeting_metadata.join_at
            });
            
            // If the bot is completed, fetch its report
            if (savedBot.status === 'completed') {
              setReportData(null); // Clear any existing data
              setTimeout(() => fetchReportData(), 100); // Small delay to ensure state is set
            } else if (savedBot.status === 'pending' || savedBot.status === 'started') {
              // Restart polling for this bot
              console.log(`Restarting polling for restored bot ${selectedBotId}`);
              startStatusPolling(selectedBotId);
            }
          } else {
            console.log(`Saved bot ${selectedBotId} not found, clearing selection`);
            setSelectedBotId(null);
            localStorage.removeItem('selectedBotId');
          }
        }
      } catch (error) {
        console.error('Failed to load bots:', error);
      }
    };
    
    loadBots();
  }, []); // Empty dependency array - only run on mount

  // Cleanup polling interval on unmount
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  // Determine which screen to show
  const shouldShowReport = selectedBot && selectedBot.status === 'completed';
  const shouldShowConfig = selectedBot && selectedBot.status !== 'completed';

  return (
    <div className="min-h-screen bg-gray-50 text-black">
      <div className="flex h-screen">
        {/* Sidebar */}
        <Sidebar
          bots={bots}
          selectedBotId={selectedBotId}
          onBotSelect={handleBotSelect}
          onNewBot={handleNewBot}
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
                  <span className="text-gray-600">• {selectedBot.meeting_metadata.bot_name}</span>
                )}
              </div>
              
              {/* Refresh Button */}
              {selectedBotId && (
                <div className="flex gap-2">
                  <button
                    onClick={refreshBotStatus}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors duration-200 flex items-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Refresh Status
                  </button>
                  
                  {/* Show trigger analysis button if bot is completed but no reports */}
                  {selectedBot && selectedBot.status === 'completed' && 
                   (!reportData || !reportData.reports || reportData.reports.length === 0) && (
                    <button
                      onClick={triggerAnalysis}
                      disabled={loading}
                      className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-4 py-2 rounded-lg transition-colors duration-200 flex items-center gap-2"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      {loading ? 'Triggering...' : 'Trigger Analysis'}
                    </button>
                  )}
                  
                  {/* Debug button */}
                  <button
                    onClick={checkWebhookStatus}
                    className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors duration-200 flex items-center gap-2"
                    title="Check webhook status and debug info"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Debug
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
                reportData={reportData}
                config={config}
                onRefresh={fetchReportData}
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