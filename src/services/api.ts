import { 
  CreateBotRequest, 
  CreateBotResponse, 
  MeetingBot, 
  TranscriptData, 
  ReportData 
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  private async makeRequest<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
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
      throw error;
    }
  }

  // Create a new meeting bot
  async createBot(request: CreateBotRequest): Promise<CreateBotResponse> {
    console.log('Creating bot with request:', request);
    return this.makeRequest<CreateBotResponse>('/api/v1/bots/', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Get meeting transcripts
  async getTranscripts(meetingId: number): Promise<TranscriptData> {
    return this.makeRequest<TranscriptData>(`/meeting/${meetingId}/transcripts`);
  }

  // Get meeting report
  async getReport(meetingId: number): Promise<ReportData> {
    return this.makeRequest<ReportData>(`/meeting/${meetingId}/report`);
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