import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { Observable } from 'rxjs';

import {
  ImportBatchPreview,
  ImportCommitResponse,
  ImportUndoResponse,
} from '../models/import-preview.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class ImportService {
  private readonly apiUrl = `${environment.apiBaseUrl}/api/imports/animals`;

  constructor(
    private http: HttpClient,
  ) { }

  previewAnimalImport(
    file: File,
  ): Observable<ImportBatchPreview> {
    const formData = new FormData();

    formData.append(
      'file',
      file,
    );

    return this.http.post<ImportBatchPreview>(
      `${this.apiUrl}/preview/`,
      formData,
    );
  }

  commitAnimalImport(
    batchId: number,
  ): Observable<ImportCommitResponse> {
    return this.http.post<ImportCommitResponse>(
      `${this.apiUrl}/${batchId}/commit/`,
      {},
    );
  }

  undoAnimalImport(
    batchId: number,
  ): Observable<ImportUndoResponse> {
    return this.http.post<ImportUndoResponse>(
      `${this.apiUrl}/${batchId}/undo/`,
      {},
    );
  }
}