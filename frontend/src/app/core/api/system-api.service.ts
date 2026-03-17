import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_BASE_URL } from './api-base';
import { ApiHealthResponse } from '../models/system.models';

@Injectable({
  providedIn: 'root'
})
export class SystemApiService {
  private readonly http = inject(HttpClient);

  getHealth(): Observable<ApiHealthResponse> {
    return this.http.get<ApiHealthResponse>(`${API_BASE_URL}/api/health`);
  }
}
