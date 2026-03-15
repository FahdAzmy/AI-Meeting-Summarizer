# Quickstart: Frontend Dashboard

This guide provides instructions to boot up the Frontend Dashboard application locally.

## Prerequisites

- Node.js `v18.x` or higher
- `npm` or `yarn` installed
- The Python Backend API service running simultaneously on `http://localhost:8000`

## Initial Setup

1. **Navigate to the frontend directory**
   ```bash
   cd frontend
   ```

2. **Install Javascript dependencies**
   ```bash
   npm install
   ```

3. **Configure Environment Variables**
   Create a `.env.local` file inside the `/frontend` directory:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

## Running the Application

1. **Start the development server**
   ```bash
   npm run dev
   ```
2. The UI will be available in your browser at: `http://localhost:3000`. 
   
   If `NEXT_PUBLIC_API_URL` is configured correctly, visiting the root page will render the Dashboard and connecting routes like network calls should proxy over to the running backend.

## Running Tests (TDD)

Per the project constitution, code must be tested first:

- To run core logic unit tests and component rendering tests:
  ```bash
  npm run test
  ```
- To run E2E flows (Playwright):
  ```bash
  npx playwright test
  ```
