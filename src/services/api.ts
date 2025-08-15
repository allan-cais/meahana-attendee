/**
 * API Service for Meeting Bot Dashboard
 * 
 * Handles all API communication with the backend service
 */

import { 
  CreateBotRequest, 
  CreateBotResponse, 
  MeetingBot, 
  TranscriptData, 
  ReportData,
  ScorecardResponse
} from '../types';

// Clean the API base URL to remove any trailing slashes
const API_BASE_URL = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace(/\/$/, '');

// Utility function to properly construct URLs
function constructUrl(baseUrl: string, endpoint: string): string {
  // Remove trailing slash from base URL
  const cleanBase = baseUrl.replace(/\/$/, '');
  
  // Ensure endpoint starts with /
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  
  // Check if base URL already contains /api and endpoint also starts with /api
  // If so, remove the /api from the base URL to avoid duplication
  let finalBase = cleanBase;
  if (cleanBase.endsWith('/api') && cleanEndpoint.startsWith('/api/')) {
    finalBase = cleanBase.slice(0, -4); // Remove '/api' from the end
  }
  
  // Construct URL
  const url = `${finalBase}${cleanEndpoint}`;
  
  // Remove any double slashes (except for protocol)
  let finalUrl = url.replace(/([^:])\/+/g, '$1/');
  
  // Final safety check: if we still have double /api/, fix it
  if (finalUrl.includes('/api/api/')) {
    finalUrl = finalUrl.replace('/api/api/', '/api/');
  }
  
  return finalUrl;
}

class ApiService {
  private async makeRequest<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = constructUrl(API_BASE_URL, endpoint);
    
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, defaultOptions);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      // Re-throw as a standard Error to ensure it's catchable
      throw new Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  // Create a new meeting bot
  async createBot(request: CreateBotRequest): Promise<CreateBotResponse> {
    const result = await this.makeRequest<CreateBotResponse>('/api/v1/bots/', {
      method: 'POST',
      body: JSON.stringify(request),
    });
    return result;
  }

  // Get meeting transcripts
  async getTranscripts(meetingId: number): Promise<TranscriptData> {
    return this.makeRequest<TranscriptData>(`/meeting/${meetingId}/transcripts`);
  }

  // Get meeting report
  async getReport(meetingId: number): Promise<ReportData> {
    const result = await this.makeRequest<ReportData>(`/meeting/${meetingId}/report`);
    return result;
  }

  // Poll for report with exponential backoff
  async pollForReport(meetingId: number, maxAttempts: number = 10): Promise<ReportData> {
    let attempt = 0;
    let delay = 2000; // Start with 2 seconds

    const wait = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

    while (attempt < maxAttempts) {
      try {
        const report = await this.getReport(meetingId);
        
        // If report is available, return it
        if (report.reports && report.reports.length > 0) {
          return report;
        }

        // If meeting is still in progress, wait longer
        if (report.status === 'STARTED') {
          await wait(10000); // Wait 10 seconds
        } else {
          // If report is being generated, use exponential backoff
          await wait(delay);
          delay = Math.min(delay * 1.5, 30000); // Max 30 seconds
        }

        attempt++;
      } catch (error) {
        await wait(delay);
        delay = Math.min(delay * 1.5, 30000);
        attempt++;
      }
    }

    throw new Error('Report polling timed out');
  }

  // Get all bots
  async getBots(): Promise<MeetingBot[]> {
    try {
      const result = await this.makeRequest<MeetingBot[]>('/api/v1/bots/');
      return result;
    } catch (error) {
      return [];
    }
  }

  // Get a specific bot by ID
  async getBot(botId: number): Promise<MeetingBot> {
    const result = await this.makeRequest<MeetingBot>(`/api/v1/bots/${botId}`);
    return result;
  }

  // Delete a bot
  async deleteBot(botId: number): Promise<{message: string}> {
    const result = await this.makeRequest<{message: string}>(`/api/v1/bots/${botId}`, {
      method: 'DELETE',
    });
    return result;
  }

  // Poll for bot status updates
  async pollBotStatus(botId: number): Promise<any> {
    const result = await this.makeRequest<any>(`/api/v1/bots/${botId}/poll-status`, {
      method: 'POST',
    });
    return result;
  }

  // Add webhook to existing bot
  async addWebhookToBot(botId: number): Promise<any> {
    const result = await this.makeRequest<any>(`/api/v1/bots/${botId}/add-webhook`, {
      method: 'POST',
    });
    return result;
  }

  // Manually trigger analysis for a meeting
  async triggerAnalysis(meetingId: number): Promise<{message: string}> {
    const result = await this.makeRequest<{message: string}>(`/meeting/${meetingId}/trigger-analysis`, {
      method: 'POST',
    });
    return result;
  }

  // Get webhook information
  async getWebhookInfo(): Promise<any> {
    const result = await this.makeRequest<any>('/webhook/debug');
    return result;
  }

  // Get current webhook URL
  async getWebhookUrl(): Promise<any> {
    const result = await this.makeRequest<any>('/webhook/url');
    return result;
  }

  // Get meeting scorecard
  async getMeetingScorecard(meetingId: number): Promise<ScorecardResponse> {
    const result = await this.makeRequest<ScorecardResponse>(`/meeting/${meetingId}/scorecard`);
    return result;
  }
}

// Create singleton instance
const apiService = new ApiService();

export default apiService; 