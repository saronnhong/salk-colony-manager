import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import {
  CageDetailModel,
  CageSummary,
  CageMoveRequest,
  RackPositionSummary,
  CageLocationHistory,
} from '../models/cage.model';

@Injectable({
  providedIn: 'root'
})
export class CageService {
  private readonly apiUrl = 'http://localhost:8000/api/cages';

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
      'http://localhost:8000/api/rack-positions/'
    );
  }

  getLocationHistory(
    cageId: string
  ): Observable<CageLocationHistory[]> {
    return this.http.get<CageLocationHistory[]>(
      `${this.apiUrl}/${cageId}/location-history/`
    );
  }
}