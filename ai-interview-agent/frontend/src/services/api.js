export class ApiError extends Error {
  constructor(message, status, errorData) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.error = errorData?.error || 'api_error';
    this.data = errorData;
  }
}

export async function postInterviewTurn(payload) {
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
  const response = await fetch(`${baseUrl}/interview`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

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
