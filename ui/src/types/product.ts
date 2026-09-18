/** Shape of the public product payload, confirmed against dev 2026-09-16. */
export interface ProductPayload {
  id: string;
  organization_id: string;
  organization_name: string;
  name: string;
  short_description: string | null;
  description: string | null;
  content: unknown;
  slug: string;
  brand: string | null;
  company_logo: string | null;
  /** Drives whether the "Talk to me" entry point renders. */
  has_assistant: boolean;
  assets: unknown[];
}

/** Error body returned for unknown product or organization. */
export interface ApiError {
  message: string | string[];
  error?: string;
  statusCode: number;
}
