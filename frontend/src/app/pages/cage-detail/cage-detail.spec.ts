import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CageDetail } from './cage-detail';

describe('CageDetail', () => {
  let component: CageDetail;
  let fixture: ComponentFixture<CageDetail>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CageDetail]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CageDetail);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
