# Quickstart: Zoom Meeting SDK Integration

To test the Zoom Meeting SDK integration locally, you need to set up a Zoom Developer App.

## 1. Create a Zoom App

1. Go to the [Zoom App Marketplace](https://marketplace.zoom.us/).
2. Sign in and click **Develop** > **Build App**.
3. Choose **General App**.
4. In the app configuration, make sure to enable the **Meeting SDK** feature.
5. In the **App Credentials** tab, copy the **Client ID** and **Client Secret**.

## 2. Configure Environment

Add the credentials to your backend `.env` file:

```env
ZOOM_SDK_CLIENT_ID=your_client_id_here
ZOOM_SDK_CLIENT_SECRET=your_client_secret_here
```

## 3. Install Dependencies

**Backend:**
```bash
cd backend
pip install pyjwt>=2.8.0
```

**Frontend:**
```bash
cd frontend
npm install @zoom/meetingsdk
```

## 4. Testing

To verify it works, you can test the backend token generation directly:

```bash
curl -X POST http://localhost:8000/api/zoom/signature \
  -H "Content-Type: application/json" \
  -d '{"meeting_number": "1234567890", "role": 0}'
```

You should receive a JSON response with `signature` and `sdk_key`. If you get an error or empty response, check that your `.env` variables are correctly loaded.
