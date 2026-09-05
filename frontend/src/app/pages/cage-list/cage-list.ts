import { Component, OnInit, signal } from '@angular/core';

import { CageCard } from '../../components/cage-card/cage-card';
import { CageSummary } from '../../models/cage.model';
import { CageService } from '../../services/cage.service';
import { RecentActions } from '../../components/recent-actions/recent-actions';
import {
  ExportService,
} from '../../services/export.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-cage-list',
  imports: [CageCard, RecentActions],
  templateUrl: './cage-list.html',
  styleUrl: './cage-list.scss',
})
export class CageList implements OnInit {
  cages = signal<CageSummary[]>([]);
  loading = signal(true);
  error = signal('');

  constructor(
    private cageService: CageService,
    private exportService: ExportService,
    private router: Router,
  ) { }

  ngOnInit(): void {
    this.loadCages();
  }

  private loadCages(): void {
    this.loading.set(true);
    this.error.set('');

    this.cageService.getCages().subscribe({
      next: cages => {
        console.log('Cages received:', cages);

        this.cages.set(cages);
        this.loading.set(false);
      },

      error: error => {
        console.error(error);

        this.error.set('Unable to load cages.');
        this.loading.set(false);
      }
    });
  }

  downloadCensus(): void {
    this.exportService.downloadAnimalCensus();
  }

  goToAnimalImport(): void {
  this.router.navigate([
    '/imports/animals',
  ]);
}
}
