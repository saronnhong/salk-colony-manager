import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { Observable } from 'rxjs';

import {
  ImportBatchPreview,
  ImportCommitResponse,
} from '../models/import-preview.model';

@Injectable({
  providedIn: 'root',
})
export class ImportService {
  private readonly apiUrl =
    'http://localhost:8000/api/imports/animals';

  constructor(
    private http: HttpClient,
  ) {}

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
}