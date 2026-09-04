import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import {
    AnimalDetailModel,
    AnimalLocationHistory,
    AnimalMoveRequest,
} from '../models/animal.model';

@Injectable({
    providedIn: 'root',
})
export class AnimalService {
    private readonly apiUrl =
        'http://localhost:8000/api/animals';

    constructor(private http: HttpClient) { }

    getAnimal(id: string): Observable<AnimalDetailModel> {
        return this.http.get<AnimalDetailModel>(
            `${this.apiUrl}/${id}/`
        );
    }

    getLocationHistory(
        id: string
    ): Observable<AnimalLocationHistory[]> {
        return this.http.get<AnimalLocationHistory[]>(
            `${this.apiUrl}/${id}/location-history/`
        );
    }

    moveAnimal(
        animalId: string,
        request: AnimalMoveRequest
    ): Observable<AnimalDetailModel> {
        return this.http.post<AnimalDetailModel>(
            `${this.apiUrl}/${animalId}/move/`,
            request
        );
    }
}