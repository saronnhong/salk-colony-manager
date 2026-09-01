import { TestBed } from '@angular/core/testing';

import { Cage } from './cage';

describe('Cage', () => {
  let service: Cage;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Cage);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
