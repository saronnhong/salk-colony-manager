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

  pageSize = 10;
  currentPage: number = 0;

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

  get paginatedCages() {
    const start =
      this.currentPage * this.pageSize;

    const end =
      start + this.pageSize;

    return this.cages().slice(start, end);
  }

  get totalPages(): number {
    return Math.ceil(
      this.cages().length / this.pageSize,
    );
  }

  nextPage(): void {
    if (this.currentPage < this.totalPages - 1) {
      this.currentPage++;
      this.scrollToCageList();
    }
  }

  previousPage(): void {
    if (this.currentPage > 0) {
      this.currentPage--;
      this.scrollToCageList();
    }
  }

  private scrollToCageList(): void {
    document
      .getElementById('cage-list')
      ?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
  }
}
