import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import {
  HusbandryEvent,
  HusbandryEventCreateRequest,
  HusbandryEventCorrectionRequest
} from '../models/husbandry-event.model';

@Injectable({
  providedIn: 'root',
})
export class HusbandryEventService {
  private readonly apiUrl =
    'http://127.0.0.1:8000/api/husbandry-events';

  constructor(private http: HttpClient) {}

  createEvent(
    request: HusbandryEventCreateRequest
  ): Observable<HusbandryEvent> {
    return this.http.post<HusbandryEvent>(
      `${this.apiUrl}/`,
      request
    );
  }

  getEventsForAnimal(
    animalId: string
  ): Observable<HusbandryEvent[]> {
    return this.http.get<HusbandryEvent[]>(
      `${this.apiUrl}/?animal=${animalId}`
    );
  }

  correctEvent(
  eventId: number,
  payload: HusbandryEventCorrectionRequest
) {
  return this.http.post<HusbandryEvent>(
    `${this.apiUrl}/${eventId}/correct/`,
    payload
  );
}
}