/**
 * API Service for Meeting Bot Dashboard
 * 
 * Handles all API communication with the backend service
 */

import { 
  CreateBotRequest, 
  CreateBotResponse, 
  MeetingBot, 
  ScorecardResponse
} from '../types';
import authService from './auth';

const API_BASE_URL = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace(/\/$/, '');

class ApiService {
  private async makeRequest<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    // Add authentication token if available
    const token = authService.getToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    // Add any custom headers from options
    if (options.headers) {
      Object.entries(options.headers).forEach(([key, value]) => {
        if (typeof value === 'string') {
          headers[key] = value;
        }
      });
    }
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    const defaultOptions: RequestInit = {
      headers,
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
      throw new Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

      // Create a new meeting bot
  async createBot(request: CreateBotRequest): Promise<CreateBotResponse> {
    // webhook_base_url is required by the type, so webhooks are always created
    const webhookUrl = `${request.webhook_base_url.replace(/\/$/, '')}/webhook/`;
    const requestBody = {
      ...request,
      webhooks: [
        {
          url: webhookUrl,
          triggers: [
            'bot.state_change',
            'transcript.update', 
            'chat_messages.update',
            'participant_events.join_leave'
          ]
        }
      ]
    };

    return this.makeRequest<CreateBotResponse>('/api/v1/bots/', {
      method: 'POST',
      body: JSON.stringify(requestBody),
    });
  }

  // Get all bots
  async getBots(): Promise<{ items: MeetingBot[]; total: number }> {
    return this.makeRequest<{ items: MeetingBot[]; total: number }>('/api/v1/bots/');
  }

  // Get a specific bot by ID
  async getBot(botId: number): Promise<MeetingBot> {
    return this.makeRequest<MeetingBot>(`/api/v1/bots/${botId}`);
  }

  // Delete a bot
  async deleteBot(botId: number): Promise<{message: string}> {
    return this.makeRequest<{message: string}>(`/api/v1/bots/${botId}`, {
      method: 'DELETE',
    });
  }

  // Poll for bot status updates
  async pollBotStatus(botId: number): Promise<any> {
    return this.makeRequest<any>(`/api/v1/bots/${botId}/poll-status`, {
      method: 'POST',
    });
  }

  // Manually trigger analysis for a meeting
  async triggerAnalysis(meetingId: number): Promise<{message: string}> {
    return this.makeRequest<{message: string}>(`/meeting/${meetingId}/trigger-analysis`, {
      method: 'POST',
    });
  }

  // Get meeting scorecard
  async getMeetingScorecard(meetingId: number): Promise<ScorecardResponse> {
    return this.makeRequest<ScorecardResponse>(`/meeting/${meetingId}/scorecard`);
  }
}

// Create singleton instance
const apiService = new ApiService();

export default apiService; 