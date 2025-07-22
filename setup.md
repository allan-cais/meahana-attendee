# API Integration Setup Guide

## Quick Setup

1. **Set Environment Variable**
   ```bash
   # For development (default)
   export REACT_APP_API_URL=http://localhost:8000
   
   # For production
   export REACT_APP_API_URL=https://your-api-domain.com
   ```

2. **Start Your Backend API**
   ```bash
   # Make sure your API is running on the configured URL
   # Default: http://localhost:8000
   ```

3. **Start the React App**
   ```bash
   npm start
   ```

## API Endpoints Used

The frontend integrates with these endpoints from your API documentation:

### ✅ Implemented
- `POST /api/v1/bots/` - Create meeting bot
- `GET /meeting/{id}/report` - Get AI reports
- `GET /meeting/{id}/transcripts` - Get transcripts (ready for future use)

### 🔄 Status Flow
1. **Create Bot** → Returns `pending` status
2. **Poll Status** → Waits for `started` → `completed`
3. **Fetch Report** → Gets AI-generated report with scores

### 📊 Report Display
The app displays:
- **Engagement Score** (0-10 scale)
- **Sentiment Analysis** (positive/negative/neutral)
- **Meeting Summary**
- **Key Points** (bullet list)
- **Action Items** (bullet list)

## Testing the Integration

1. **Create a Bot**
   - Fill in meeting URL (e.g., `https://meet.google.com/abc-def-ghi`)
   - Enter bot name
   - Click "Create Bot"
   - Wait 30-60 seconds for bot creation

2. **Monitor Status**
   - Watch status change from "Creating..." → "In Meeting" → "Completed"
   - App automatically polls for status updates

3. **View Report**
   - Once completed, report appears automatically
   - Shows engagement score, sentiment, summary, key points, and action items

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Ensure your API allows requests from `http://localhost:3000`
   - Add CORS headers to your API responses

2. **API Not Found**
   - Check `REACT_APP_API_URL` environment variable
   - Verify API is running on the correct port

3. **Bot Creation Fails**
   - Check meeting URL format
   - Ensure API is accepting POST requests to `/api/v1/bots/`

### Debug Mode

Enable console logging by checking the browser's developer tools. The app logs:
- Bot creation requests
- API responses
- Status polling updates
- Error messages

## Next Steps

1. **Add Transcript Display**: Implement real-time transcript viewing
2. **Persistent Storage**: Store bot list in localStorage or database
3. **User Authentication**: Add login/logout functionality
4. **Real-time Updates**: Use WebSockets for live status updates 