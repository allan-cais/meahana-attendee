/**
 * API Service for Meeting Bot Dashboard
 * 
 * FIXED: Double /api/ issue
 * The service now automatically detects and prevents duplicate /api/ paths
 * that were causing requests to /api/api/v1/bots/ instead of /api/v1/bots/
 */

import { 
  CreateBotRequest, 
  CreateBotResponse, 
  MeetingBot, 
  TranscriptData, 
  ReportData 
} from '../types';

// Clean the API base URL to remove any trailing slashes
const API_BASE_URL = (process.env.REACT_APP_API_URL || 'https://js-cais-dev-97449-u35829.vm.elestio.app').replace(/\/$/, '');

// Log API configuration for debugging
console.log('API Service initialized with base URL:', API_BASE_URL);

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
    console.log('🔧 FIXED: Removed /api from base URL to prevent duplication');
    console.log(`   Original base: ${cleanBase}`);
    console.log(`   Adjusted base: ${finalBase}`);
  }
  
  // Construct URL
  const url = `${finalBase}${cleanEndpoint}`;
  
  // Remove any double slashes (except for protocol)
  let finalUrl = url.replace(/([^:])\/+/g, '$1/');
  
  // Final safety check: if we still have double /api/, fix it
  if (finalUrl.includes('/api/api/')) {
    console.log('🚨 CRITICAL: Double /api/ still detected after initial fix!');
    console.log(`   URL before final fix: ${finalUrl}`);
    finalUrl = finalUrl.replace('/api/api/', '/api/');
    console.log(`   URL after final fix: ${finalUrl}`);
  }
  
  return finalUrl;
}

class ApiService {
  private async makeRequest<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = constructUrl(API_BASE_URL, endpoint);
    
    // Log API request for debugging (only in development)
    if (process.env.NODE_ENV === 'development') {
      console.log(`🌐 API Request: ${endpoint} → ${url}`);
    }
    
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

      return await response.json();
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      // Re-throw as a standard Error to ensure it's catchable
      throw new Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  // Create a new meeting bot
  async createBot(request: CreateBotRequest): Promise<CreateBotResponse> {
    console.log('Creating bot with request:', request);
    
    const result = await this.makeRequest<CreateBotResponse>('/api/v1/bots/', {
      method: 'POST',
      body: JSON.stringify(request),
    });
    console.log('API call successful:', result);
    return result;
  }

  // Get meeting transcripts
  async getTranscripts(meetingId: number): Promise<TranscriptData> {
    return this.makeRequest<TranscriptData>(`/meeting/${meetingId}/transcripts`);
  }

  // Get meeting report
  async getReport(meetingId: number): Promise<ReportData> {
    console.log('Fetching report for meeting ID:', meetingId);
    
    const result = await this.makeRequest<ReportData>(`/meeting/${meetingId}/report`);
    console.log('Report API call successful:', result);
    return result;
  }

  // Poll for report with exponential backoff
  async pollForReport(meetingId: number, maxAttempts: number = 10): Promise<ReportData> {
    let attempt = 0;
    let delay = 2000; // Start with 2 seconds

    while (attempt < maxAttempts) {
      try {
        const report = await this.getReport(meetingId);
        
        // If report is available, return it
        if (report.reports && report.reports.length > 0) {
          return report;
        }

        // If meeting is still in progress, wait longer
        if (report.status === 'started') {
          await new Promise(resolve => setTimeout(resolve, 10000)); // Wait 10 seconds
        } else {
          // If report is being generated, use exponential backoff
          await new Promise(resolve => setTimeout(resolve, delay));
          delay = Math.min(delay * 1.5, 30000); // Max 30 seconds
        }

        attempt++;
      } catch (error) {
        console.error(`Poll attempt ${attempt + 1} failed:`, error);
        await new Promise(resolve => setTimeout(resolve, delay));
        delay = Math.min(delay * 1.5, 30000);
        attempt++;
      }
    }

    throw new Error('Report polling timed out');
  }

  // Get all bots (this would need to be implemented on the backend)
  async getBots(): Promise<MeetingBot[]> {
    // Note: This endpoint is not in the API docs, so we'll return empty array
    // You may need to implement this on your backend or store bots locally
    return [];
  }
}

// Create singleton instance
const apiService = new ApiService();

export default apiService; 