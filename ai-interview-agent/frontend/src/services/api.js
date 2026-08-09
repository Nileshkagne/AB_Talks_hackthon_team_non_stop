export class ApiError extends Error {
  constructor(message, status, errorData) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.error = errorData?.error || 'api_error';
    this.data = errorData;
  }
}

/**
 * Post an interview turn (start or continue).
 * Uses standard fetch without premature timeouts so Render free-tier
 * cold starts (30-50s wake-up delay) resolve gracefully.
 */
export async function postInterviewTurn(payload) {
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

  let response;
  try {
    response = await fetch(`${baseUrl}/interview`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
  } catch (netErr) {
    throw new ApiError(
      'Unable to connect to backend server. If restarting from idle, please wait a moment for the server to wake up and try again.',
      0,
      { error: 'network_error' }
    );
  }

  let data;
  try {
    data = await response.json();
  } catch (err) {
    data = null;
  }

  if (!response.ok) {
    const errorMsg = data?.message || data?.error || `Request failed with status ${response.status}`;
    throw new ApiError(errorMsg, response.status, data);
  }

  return data;
}

/**
 * Fetch detailed evaluation report for a completed session.
 */
export async function fetchInterviewReport(sessionId) {
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

  let response;
  try {
    response = await fetch(`${baseUrl}/interview/${sessionId}/report`);
  } catch (netErr) {
    throw new ApiError(
      'Unable to fetch report from backend server. Please check your network connection.',
      0,
      { error: 'network_error' }
    );
  }

  let data;
  try {
    data = await response.json();
  } catch (err) {
    data = null;
  }

  if (!response.ok) {
    const errorMsg = data?.message || data?.error || `Report fetch failed with status ${response.status}`;
    throw new ApiError(errorMsg, response.status, data);
  }

  return data;
}
