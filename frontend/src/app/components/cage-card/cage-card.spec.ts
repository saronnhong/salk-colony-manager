import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CageCard } from './cage-card';

describe('CageCard', () => {
  let component: CageCard;
  let fixture: ComponentFixture<CageCard>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CageCard]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CageCard);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
