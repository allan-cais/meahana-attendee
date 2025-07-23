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
      // Re-throw as a standard Error to ensure it's catchable
      throw new Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  // Create a new meeting bot
  async createBot(request: CreateBotRequest): Promise<CreateBotResponse> {
    console.log('Creating bot with request:', request);
    
    // Try to make the API call
    try {
      const result = await this.makeRequest<CreateBotResponse>('/api/v1/bots/', {
        method: 'POST',
        body: JSON.stringify(request),
      });
      console.log('API call successful:', result);
      return result;
    } catch (error) {
      // Return mock data if API is not available
      console.log('API not available, returning mock bot creation response');
      console.log('Error details:', error);
      const mockResponse = this.getMockBotCreationResponse(request);
      console.log('Mock response:', mockResponse);
      return mockResponse;
    }
  }

  // Get meeting transcripts
  async getTranscripts(meetingId: number): Promise<TranscriptData> {
    return this.makeRequest<TranscriptData>(`/meeting/${meetingId}/transcripts`);
  }

  // Get meeting report
  async getReport(meetingId: number): Promise<ReportData> {
    console.log('Fetching report for meeting ID:', meetingId);
    
    try {
      const result = await this.makeRequest<ReportData>(`/meeting/${meetingId}/report`);
      console.log('Report API call successful:', result);
      return result;
    } catch (error) {
      // Return mock data if API is not available
      console.log('API not available, returning mock data');
      console.log('Report fetch error details:', error);
      const mockData = this.getMockReportData(meetingId);
      console.log('Mock report data:', mockData);
      return mockData;
    }
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

  // Mock report data for development
  private getMockReportData(meetingId: number): ReportData {
    return {
      meeting_id: meetingId,
      status: 'completed',
      reports: [
        {
          id: 1,
          score: {
            overall_score: 0.7,
            sentiment: "neutral",
            key_topics: ["MCP server build", "AI integration", "Third party APIs", "Clock backend", "Symptom Server", "System architecture diagram"],
            action_items: ["Focus on log for MCP server", "Authenticate user", "Request chat sending to external API", "Interact clock backend with third party APIs", "Build Symptom Server", "Review system architecture diagram"],
            participants: ["Awais Anwaar", "Arjun"],
            engagement_score: 0.9,
            meeting_effectiveness: 0.6,
            summary: "Awais Anwaar discussed the current progress on various aspects of the project, including the MCP server, AI integration, and third-party APIs. He also mentioned the need to focus on the clock backend and the creation of a Symptom Server. A new system architecture diagram was created and sent for review.",
            insights: ["The project is in progress and expected to cover all aspects in the next three to four days", "There is a need to focus on multiple aspects of the project, particularly the clock backend", "A new system architecture diagram has been created and sent for review"],
            recommendations: ["Increase focus on the clock backend and Symptom Server", "Ensure timely review of the new system architecture diagram", "Maintain progress pace to cover all aspects in the stated timeline"]
          },
          created_at: new Date().toISOString()
        }
      ],
      message: null
    };
  }

  // Mock bot creation response for development
  private getMockBotCreationResponse(request: CreateBotRequest): CreateBotResponse {
    const botId = Math.floor(Math.random() * 10000);
    return {
      id: botId,
      meeting_url: request.meeting_url,
      bot_id: `bot_${botId}`,
      status: 'completed', // Changed from 'pending' to 'completed' for immediate mock data
      meeting_metadata: {
        bot_name: request.bot_name,
        join_at: request.join_at
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
  }
}

// Create singleton instance
const apiService = new ApiService();

export default apiService; 