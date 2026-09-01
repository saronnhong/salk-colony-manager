import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CageList } from './cage-list';

describe('CageList', () => {
  let component: CageList;
  let fixture: ComponentFixture<CageList>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CageList]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CageList);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
