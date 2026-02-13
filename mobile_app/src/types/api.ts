export type User = {
  id: number;
  email: string;
  phone_number: string | null;
  email_verified_at: string | null;
  phone_verified_at: string | null;
  two_factor_enabled: boolean;
  created_at: string;
};

export type WatchlistItem = {
  id: number;
  user_id: number;
  product_url: string;
  threshold: number;
  is_active: boolean;
  last_price: number | null;
  last_currency: string | null;
  last_checked_at: string | null;
  created_at: string;
  updated_at: string;
};

export type PriceCheckRun = {
  id: number;
  watchlist_item_id: number;
  status: string;
  message: string;
  price_amount: number | null;
  price_currency: string | null;
  alert_sent: boolean;
  created_at: string;
};

export type AuthFlowResponse = {
  message: string;
  dev_code?: string | null;
};

export type AuthTokenResponse = {
  access_token: string;
  token_type: "bearer";
  user: User;
};
