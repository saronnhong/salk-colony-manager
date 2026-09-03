import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { AuditOperation } from '../models/audit-operation.model';

@Injectable({
  providedIn: 'root',
})
export class AuditOperationService {
  private readonly apiUrl =
    'http://127.0.0.1:8000/api/audit-operations';

  constructor(private http: HttpClient) {}

  getOperations(): Observable<AuditOperation[]> {
    return this.http.get<AuditOperation[]>(
      `${this.apiUrl}/`
    );
  }

  undoOperation(
    operationId: number,
    reason = 'Undo from Recent Actions',
  ): Observable<AuditOperation> {
    return this.http.post<AuditOperation>(
      `${this.apiUrl}/${operationId}/undo/`,
      { reason },
    );
  }
}