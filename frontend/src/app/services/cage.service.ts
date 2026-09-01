import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import {
  CageDetailModel,
  CageSummary
} from '../models/cage.model';

@Injectable({
  providedIn: 'root'
})
export class CageService {
  private readonly apiUrl = 'http://127.0.0.1:8000/api/cages';

  constructor(private http: HttpClient) {}

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
}