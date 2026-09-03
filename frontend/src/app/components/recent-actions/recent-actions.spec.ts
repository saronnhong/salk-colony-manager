import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RecentActions } from './recent-actions';

describe('RecentActions', () => {
  let component: RecentActions;
  let fixture: ComponentFixture<RecentActions>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RecentActions]
    })
    .compileComponents();

    fixture = TestBed.createComponent(RecentActions);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
