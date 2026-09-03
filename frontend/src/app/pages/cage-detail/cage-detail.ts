import { Component, OnInit, signal, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import {
  FormBuilder,
  ReactiveFormsModule,
  Validators,
  FormsModule,
} from '@angular/forms';

import { CageDetailModel, RackPositionSummary, CageLocationHistory } from '../../models/cage.model';
import { CageService } from '../../services/cage.service';
import { DatePipe } from '@angular/common';
// import { RecentActions } from '../../components/recent-actions/recent-actions';


@Component({
  selector: 'app-cage-detail',
  imports: [RouterLink, DatePipe, ReactiveFormsModule, FormsModule],
  templateUrl: './cage-detail.html',
  styleUrl: './cage-detail.scss',
})
export class CageDetail implements OnInit {
  private readonly fb = inject(FormBuilder);
  cage = signal<CageDetailModel | null>(null);
  locationHistory = signal<CageLocationHistory[]>([]);

  loading = signal(true);
  error = signal('');

  rackPositions = signal<RackPositionSummary[]>([]);

  moveFormVisible = signal(false);
  moving = signal(false);
  moveError = signal<string | null>(null);
  moveSuccess = signal<string | null>(null);

  moveForm = this.fb.group({
    destination_rack_position_id: [
      null as number | null,
      Validators.required,
    ],
    reason: [''],
  });

  constructor(
    private route: ActivatedRoute,
    private cageService: CageService,
  ) { }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');

    if (!id) {
      this.error.set('Cage ID is missing.');
      this.loading.set(false);
      return;
    }

    this.loadCage(id);
    this.loadRackPositions();
    this.loadLocationHistory(id);
  }

  private loadCage(id: string): void {
    this.loading.set(true);
    this.error.set('');

    this.cageService.getCage(id).subscribe({
      next: cage => {
        this.cage.set(cage);
        this.loading.set(false);
      },

      error: error => {
        console.error(error);

        this.error.set('Unable to load cage.');
        this.loading.set(false);
      }
    });
  }

  private loadRackPositions(): void {
    this.cageService.getRackPositions().subscribe({
      next: positions => {
        this.rackPositions.set(positions);
        console.log('rack positions', positions);
      },
      error: () => {
        this.rackPositions.set([]);
      },
    });
  }

  showMoveForm(): void {
    this.moveError.set(null);
    this.moveSuccess.set(null);
    this.moveFormVisible.set(true);
  }

  cancelMove(): void {
    this.moveFormVisible.set(false);
    this.moveError.set(null);

    this.moveForm.reset({
      destination_rack_position_id: null,
      reason: '',
    });
  }

  submitMove(): void {
    if (this.moveForm.invalid) {
      this.moveForm.markAllAsTouched();
      return;
    }

    const cage = this.cage();

    if (!cage) {
      return;
    }

    const destinationPositionId =
      this.moveForm.controls
        .destination_rack_position_id.value;

    if (destinationPositionId === null) {
      return;
    }

    this.moving.set(true);
    this.moveError.set(null);
    this.moveSuccess.set(null);

    this.cageService.moveCage(
      cage.id,
      {
        destination_rack_position_id:
          destinationPositionId,
        reason:
          this.moveForm.controls.reason.value || '',
      }
    ).subscribe({
      next: updatedCage => {
        this.cage.set(updatedCage);

        this.moveSuccess.set(
          'Cage moved successfully.'
        );

        this.moveFormVisible.set(false);
        this.moving.set(false);

        this.moveForm.reset({
          destination_rack_position_id: null,
          reason: '',
        });

        this.loadRackPositions();
        this.loadLocationHistory(updatedCage.id);
      },

      error: error => {
        console.error('Move cage error:', error);

        const detail = error?.error?.detail;

        this.moveError.set(
          Array.isArray(detail)
            ? detail.join(' ')
            : detail ||
            `Unable to move cage. Server returned ${error.status}.`
        );

        this.moving.set(false);
      },
    });
  }

  private loadLocationHistory(id: string): void {
    this.cageService.getLocationHistory(id).subscribe({
      next: history => {
        this.locationHistory.set(history);
      },
      error: () => {
        this.locationHistory.set([]);
      },
    });
  }
}
