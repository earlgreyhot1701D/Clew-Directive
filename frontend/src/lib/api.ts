/**
 * API Client for Clew Directive Backend
 * 
 * Handles all communication with the FastAPI backend.
 * Includes error handling, retry logic, and type safety.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// API Response Types
export interface ApiError {
  error: string;
  retry_allowed: boolean;
}

export interface VibeCheckResponse {
  profile: string;
}

export interface RefineProfileResponse {
  profile: string;
}

export interface LearningResource {
  resource_id: string;
  resource_name: string;
  resource_url: string;
  provider: string;
  provider_url: string;
  why_for_you: string;
  difficulty: string;
  estimated_hours: number;
  format: string;
  free_model: string;
  sequence_note: string;
  sequence_order: number;
}

export interface BriefingResponse {
  profile_summary: string;
  recommended_resources: LearningResource[];
  approach_guidance: string;
  total_estimated_hours: number;
  pdf_url?: string | null;
  pdf_warning?: string;
}

// Custom error class
export class ClewApiError extends Error {
  constructor(
    message: string,
    public retryAllowed: boolean = true,
    public statusCode?: number
  ) {
    super(message);
    this.name = 'ClewApiError';
  }
}

/**
 * Make API request with error handling
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      // Backend returned an error
      const errorData = data as ApiError;
      throw new ClewApiError(
        errorData.error || 'An unexpected error occurred',
        errorData.retry_allowed ?? true,
        response.status
      );
    }

    return data as T;
  } catch (error) {
    // Network error or JSON parse error
    if (error instanceof ClewApiError) {
      throw error;
    }
    
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new ClewApiError(
        'Connection error. Please check your internet and try again.',
        true
      );
    }

    throw new ClewApiError(
      'An unexpected error occurred. Please try again.',
      true
    );
  }
}

/**
 * Submit Vibe Check responses and get profile
 */
export async function submitVibeCheck(
  responses: Record<string, string>
): Promise<VibeCheckResponse> {
  return apiRequest<VibeCheckResponse>('/vibe-check', {
    method: 'POST',
    body: JSON.stringify({
      vibe_check_responses: responses,
    }),
  });
}

/**
 * Refine profile based on user feedback
 */
export async function refineProfile(
  originalProfile: string,
  userCorrection: string,
  refinementCount: number = 0
): Promise<RefineProfileResponse> {
  return apiRequest<RefineProfileResponse>('/refine-profile', {
    method: 'POST',
    body: JSON.stringify({
      original_profile: originalProfile,
      user_correction: userCorrection,
      refinement_count: refinementCount,
    }),
  });
}

/**
 * Generate learning path briefing
 */
export async function generateBriefing(
  approvedProfile: string
): Promise<BriefingResponse> {
  return apiRequest<BriefingResponse>('/generate-briefing', {
    method: 'POST',
    body: JSON.stringify({
      approved_profile: approvedProfile,
    }),
  });
}
