import { Component, OnInit, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { CageDetailModel } from '../../models/cage.model';
import { CageService } from '../../services/cage.service';

@Component({
  selector: 'app-cage-detail',
  imports: [RouterLink],
  templateUrl: './cage-detail.html',
  styleUrl: './cage-detail.scss',
})
export class CageDetail implements OnInit {
    cage = signal<CageDetailModel | null>(null);

  loading = signal(true);
  error = signal('');

  constructor(
    private route: ActivatedRoute,
    private cageService: CageService
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');

    if (!id) {
      this.error.set('Cage ID is missing.');
      this.loading.set(false);
      return;
    }

    this.loadCage(id);
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
}
