export type Product = {
  _id: number;
  title: string;
  category: string;
  source: string;
  metadataCutoffMs: number;
  available: boolean;
};
export type User = {
  id: string;
  name: string;
  email: string;
  personalization: boolean;
  selectedCategories: string[];
  wishlist: number[];
  cart: number[];
};
export type Recommendation = {
  itemid: number;
  reason: string;
  catalogue_description: string | null;
  description_source: string;
  product: Product;
};
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}
export async function api<T>(
  path: string,
  method = "GET",
  body?: unknown,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch("/api" + path, {
    method,
    credentials: "same-origin",
    headers: body === undefined ? {} : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
  });
  if (!response.ok) {
    let message = "Pasal is temporarily unavailable. Please try again.";
    try {
      message = (await response.json()).error || message;
    } catch {}
    throw new ApiError(message, response.status);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
