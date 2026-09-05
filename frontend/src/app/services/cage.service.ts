import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import {
  CageDetailModel,
  CageSummary,
  CageMoveRequest,
  RackPositionSummary,
  CageLocationHistory,
  CageResponsibilityRequest,
  ColonyUser,
} from '../models/cage.model';

import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class CageService {
  private readonly apiUrl = `${environment.apiBaseUrl}/api/cages`;

  constructor(private http: HttpClient) { }

  getCages(): Observable<CageSummary[]> {
    return this.http.get<CageSummary[]>(
      `${this.apiUrl}/`
    );
  }

  getCage(id: string): Observable<CageDetailModel> {
    return this.http.get<CageDetailModel>(
      `${this.apiUrl}/${id}/`
    );
  }

  moveCage(
    cageId: string,
    request: CageMoveRequest
  ): Observable<CageDetailModel> {
    return this.http.post<CageDetailModel>(
      `${this.apiUrl}/${cageId}/move/`,
      request
    );
  }

  getRackPositions(): Observable<RackPositionSummary[]> {
    return this.http.get<RackPositionSummary[]>(
      `${environment.apiBaseUrl}/api/rack-positions/`
    );
  }

  getLocationHistory(
    cageId: string
  ): Observable<CageLocationHistory[]> {
    return this.http.get<CageLocationHistory[]>(
      `${this.apiUrl}/${cageId}/location-history/`
    );
  }

  assignResponsibility(
    cageId: string,
    request: CageResponsibilityRequest
  ) {
    return this.http.post(
      `${environment.apiBaseUrl}/api/cages/${cageId}/responsibility/`,
      request,
      {
        withCredentials: true,
      }
    );
  }

  getColonyUsers() {
    return this.http.get<ColonyUser[]>(
      `${environment.apiBaseUrl}/api/users/`,
      {
        withCredentials: true,
      }
    );
  }
}