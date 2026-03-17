import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_BASE_URL } from './api-base';
import { AuthLoginRequest, AuthRegisterRequest, AuthSessionResponse } from '../models/auth.models';

@Injectable({
  providedIn: 'root'
})
export class AuthApiService {
  private readonly http = inject(HttpClient);

  login(payload: AuthLoginRequest): Observable<AuthSessionResponse> {
    return this.http.post<AuthSessionResponse>(`${API_BASE_URL}/api/auth/login`, payload);
  }

  register(payload: AuthRegisterRequest): Observable<AuthSessionResponse> {
    return this.http.post<AuthSessionResponse>(`${API_BASE_URL}/api/auth/register`, payload);
  }
}
