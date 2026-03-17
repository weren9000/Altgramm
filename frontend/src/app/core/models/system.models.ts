export interface ApiHealthResponse {
  service: string;
  status: 'ok' | 'degraded';
  environment: string;
  database: 'online' | 'offline';
}
